"""相続計算サービス

相続人の確定と相続割合の計算を統合して実行するサービス。
"""
from typing import List, Dict, Optional
from fractions import Fraction

from ..models.person import Person
from ..models.relationship import BloodType
from ..models.inheritance import (
    InheritanceResult,
    HeritageRank,
    SubstitutionType,
    Heir,
)
from .heir_validator import HeirValidator
from .share_calculator import ShareCalculator
from .base import BaseService


class InheritanceCalculator(BaseService[InheritanceResult]):
    """
    相続計算サービス

    相続人の資格確定、相続割合の計算、結果の生成を統合的に実行する。
    """

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.validator = HeirValidator()
        self.calculator = ShareCalculator()

    def calculate(
        self,
        decedent: Person,
        spouses: List[Person],
        children: List[Person],
        parents: List[Person],
        siblings: List[Person],
        renounced: Optional[List[Person]] = None,
        disqualified: Optional[List[Person]] = None,
        disinherited: Optional[List[Person]] = None,
        sibling_blood_types: Optional[Dict[str, BloodType]] = None,
        retransfer_heirs_info: Optional[Dict[str, List[Person]]] = None,
    ) -> InheritanceResult:
        """
        相続計算を実行

        Args:
            decedent: 被相続人
            spouses: 配偶者候補
            children: 子候補
            parents: 直系尊属候補
            siblings: 兄弟姉妹候補
            renounced: 相続放棄者
            disqualified: 相続欠格者
            disinherited: 相続廃除者
            sibling_blood_types: 兄弟姉妹の血縁タイプ
            retransfer_heirs_info: 再転相続先の情報（相続人ID: 再転相続先リスト）

        Returns:
            相続計算結果
        """
        # デフォルト値の設定
        if renounced is None:
            renounced = []
        if disqualified is None:
            disqualified = []
        if disinherited is None:
            disinherited = []
        if sibling_blood_types is None:
            sibling_blood_types = {}
        if retransfer_heirs_info is None:
            retransfer_heirs_info = {}

        # バリデータの初期化
        self.validator.set_decedent(decedent)
        self.validator.renounced_persons = renounced
        self.validator.disqualified_persons = disqualified
        self.validator.disinherited_persons = disinherited

        # 結果オブジェクトの作成
        result = InheritanceResult(decedent=decedent)

        # 各順位の相続人を確定
        valid_spouses = self._validate_spouses(spouses, result)
        valid_children = self._validate_children(children, result)
        valid_parents = self._validate_parents(parents, result, bool(valid_children))
        valid_siblings = self._validate_siblings(
            siblings, result, bool(valid_children), bool(valid_parents)
        )

        # 相続割合を計算
        shares = self.calculator.calculate_shares(
            valid_spouses,
            valid_children,
            valid_parents,
            valid_siblings,
            sibling_blood_types
        )

        # 相続人を結果に追加
        self._add_heirs_to_result(
            result,
            valid_spouses,
            valid_children,
            valid_parents,
            valid_siblings,
            shares
        )

        # フラグを設定
        result.has_spouse = len(valid_spouses) > 0
        result.has_children = len(valid_children) > 0
        result.has_parents = len(valid_parents) > 0
        result.has_siblings = len(valid_siblings) > 0

        # 再転相続の処理
        if retransfer_heirs_info:
            all_persons = spouses + children + parents + siblings
            result = self._process_retransfer_inheritance_with_info(
                result, retransfer_heirs_info
            )

        self.log_operation(
            "Inheritance calculation completed",
            total_heirs=result.total_heirs
        )

        return result

    def _validate_spouses(
        self, spouses: List[Person], result: InheritanceResult
    ) -> List[Person]:
        """配偶者の資格検証"""
        valid_spouses = []
        for spouse in spouses:
            if self.validator.validate_spouse(spouse):
                valid_spouses.append(spouse)
                result.add_calculation_basis("民法890条（配偶者の相続権）")

        return valid_spouses

    def _validate_children(
        self, children: List[Person], result: InheritanceResult
    ) -> List[Person]:
        """子の資格検証"""
        valid_children = []
        for child in children:
            if self.validator.validate_child(child):
                valid_children.append(child)

        if valid_children:
            result.add_calculation_basis("民法887条1項（子の相続権）")

        return valid_children

    def _validate_parents(
        self,
        parents: List[Person],
        result: InheritanceResult,
        has_first_rank: bool
    ) -> List[Person]:
        """直系尊属の資格検証"""
        valid_parents = []
        for parent in parents:
            if self.validator.validate_parent(parent, has_first_rank):
                valid_parents.append(parent)

        if valid_parents:
            result.add_calculation_basis("民法889条1項1号（直系尊属の相続権）")

        return valid_parents

    def _validate_siblings(
        self,
        siblings: List[Person],
        result: InheritanceResult,
        has_first_rank: bool,
        has_second_rank: bool
    ) -> List[Person]:
        """兄弟姉妹の資格検証"""
        valid_siblings = []
        for sibling in siblings:
            if self.validator.validate_sibling(
                sibling, has_first_rank, has_second_rank
            ):
                valid_siblings.append(sibling)

        if valid_siblings:
            result.add_calculation_basis("民法889条1項2号（兄弟姉妹の相続権）")

        return valid_siblings

    def _add_heirs_to_result(
        self,
        result: InheritanceResult,
        spouses: List[Person],
        children: List[Person],
        parents: List[Person],
        siblings: List[Person],
        shares: Dict[str, Fraction]
    ) -> None:
        """相続人を結果に追加"""
        # 配偶者
        for spouse in spouses:
            share = shares.get(str(spouse.id), Fraction(0, 1))
            result.add_heir(spouse, HeritageRank.SPOUSE, share)

        # 子
        for child in children:
            share = shares.get(str(child.id), Fraction(0, 1))
            result.add_heir(child, HeritageRank.FIRST, share)

        # 直系尊属
        for parent in parents:
            share = shares.get(str(parent.id), Fraction(0, 1))
            result.add_heir(parent, HeritageRank.SECOND, share)

        # 兄弟姉妹
        for sibling in siblings:
            share = shares.get(str(sibling.id), Fraction(0, 1))
            result.add_heir(sibling, HeritageRank.THIRD, share)

        # 相続分の計算根拠を追加
        if spouses and children:
            result.add_calculation_basis("民法900条1号（配偶者1/2、子1/2）")
        elif spouses and parents:
            result.add_calculation_basis("民法900条2号（配偶者2/3、直系尊属1/3）")
        elif spouses and siblings:
            result.add_calculation_basis("民法900条3号（配偶者3/4、兄弟姉妹1/4）")

    def _process_retransfer_inheritance_with_info(
        self,
        result: InheritanceResult,
        retransfer_info: Dict[str, List[Person]]
    ) -> InheritanceResult:
        """
        再転相続の処理（情報付き版）

        Args:
            result: 現在の相続計算結果
            retransfer_info: 再転相続先の情報（相続人ID: 再転相続先リスト）

        Returns:
            再転相続処理後の相続計算結果
        """
        # 遺産分割前に死亡した相続人を特定
        retransfer_heirs = [
            heir for heir in result.heirs
            if heir.person.died_before_division and not heir.person.is_alive
        ]

        if not retransfer_heirs:
            return result

        # 再転相続が発生した旨を記録
        result.add_calculation_basis("民法第896条（相続人の相続、再転相続）")

        new_heirs = []

        # 再転相続が発生しない相続人をそのまま追加
        for heir in result.heirs:
            if not heir.person.died_before_division:
                new_heirs.append(heir)

        # 再転相続の処理
        for original_heir in retransfer_heirs:
            heir_id = str(original_heir.person.id)
            retransfer_targets = retransfer_info.get(heir_id, [])

            if not retransfer_targets:
                # 再転相続先がいない場合は元の相続人をそのまま
                new_heirs.append(original_heir)
                continue

            # 再転相続分を計算
            retransfer_shares = self._calculate_retransfer_shares(
                original_heir.share,
                retransfer_targets
            )

            # 再転相続人を追加
            for target, share in retransfer_shares:
                new_heir = Heir(
                    person=target,
                    rank=original_heir.rank,
                    share=share,
                    share_percentage=float(share) * 100,
                    is_retransfer=True,
                    retransfer_from=original_heir.person,
                    original_share=original_heir.share
                )
                new_heirs.append(new_heir)

        # 相続人リストを更新
        result.heirs = new_heirs

        return result

    def _process_retransfer_inheritance(
        self,
        result: InheritanceResult,
        all_persons: List[Person]
    ) -> InheritanceResult:
        """
        再転相続の処理

        遺産分割前に死亡した相続人がいる場合、
        その相続分をその相続人の相続人に再転相続させる。

        Args:
            result: 現在の相続計算結果
            all_persons: 再転相続先の候補となる全人物リスト

        Returns:
            再転相続処理後の相続計算結果
        """
        # 遺産分割前に死亡した相続人を特定
        retransfer_heirs = [
            heir for heir in result.heirs
            if heir.person.died_before_division and not heir.person.is_alive
        ]

        if not retransfer_heirs:
            return result

        # 再転相続が発生した旨を記録
        result.add_calculation_basis("民法第896条（相続人の相続、再転相続）")

        new_heirs = []

        # 再転相続が発生しない相続人をそのまま追加
        for heir in result.heirs:
            if not heir.person.died_before_division:
                new_heirs.append(heir)

        # 再転相続の処理
        for original_heir in retransfer_heirs:
            # この相続人の相続人を探す
            retransfer_targets = self._find_retransfer_heirs(
                original_heir.person,
                all_persons
            )

            if not retransfer_targets:
                # 再転相続先がいない場合は元の相続人をそのまま
                new_heirs.append(original_heir)
                continue

            # 再転相続分を計算
            retransfer_shares = self._calculate_retransfer_shares(
                original_heir.share,
                retransfer_targets
            )

            # 再転相続人を追加
            for target, share in retransfer_shares:
                new_heir = Heir(
                    person=target,
                    rank=original_heir.rank,
                    share=share,
                    share_percentage=float(share) * 100,
                    is_retransfer=True,
                    retransfer_from=original_heir.person,
                    original_share=original_heir.share
                )
                new_heirs.append(new_heir)

        # 相続人リストを更新
        result.heirs = new_heirs

        return result

    def _find_retransfer_heirs(
        self,
        deceased_heir: Person,
        all_persons: List[Person]
    ) -> List[Person]:
        """
        再転相続先の相続人を探す

        Args:
            deceased_heir: 遺産分割前に死亡した相続人
            all_persons: 全人物リスト

        Returns:
            再転相続先の相続人リスト
        """
        # 簡易実装: 配偶者と子を再転相続先とする
        # 実際にはHeirValidatorを使って正確に判定すべき
        retransfer_heirs = []

        for person in all_persons:
            if person.is_alive and person.id != deceased_heir.id:
                # この実装では、配偶者・子・親などの関係を
                # 外部から渡される必要がある
                # 簡易実装として、すべての生存者を候補とする
                retransfer_heirs.append(person)

        return retransfer_heirs

    def _calculate_retransfer_shares(
        self,
        original_share: Fraction,
        retransfer_targets: List[Person]
    ) -> List[tuple[Person, Fraction]]:
        """
        再転相続分を計算

        Args:
            original_share: 元の相続分
            retransfer_targets: 再転相続先のリスト

        Returns:
            各再転相続人と相続分のタプルのリスト
        """
        if not retransfer_targets:
            return []

        # 簡易実装: 均等に分割
        # 実際には再転相続先の法定相続分に応じて按分すべき
        per_person_share = original_share / len(retransfer_targets)

        return [
            (person, per_person_share)
            for person in retransfer_targets
        ]
