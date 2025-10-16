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
from ..utils.exceptions import RenunciationConflictError
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
        retransfer_relationships: Optional[Dict[str, Dict[str, str]]] = None,
        second_inheritance_renounced: Optional[Dict[str, List[Person]]] = None,
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
            retransfer_relationships: 再転相続先の関係情報（相続人ID: {人物ID: 関係タイプ}）
                例: {"deceased_heir_id": {"person1_id": "spouse", "person2_id": "child"}}
            second_inheritance_renounced: 第2次相続の放棄者情報（死亡相続人ID: 放棄者リスト）
                例: {"deceased_heir_id": [person1, person2]}
                判例により、第2次相続を放棄した者は第1次相続のみを承認できない

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
        if retransfer_relationships is None:
            retransfer_relationships = {}
        if second_inheritance_renounced is None:
            second_inheritance_renounced = {}

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
                result, retransfer_heirs_info, retransfer_relationships, second_inheritance_renounced
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
        retransfer_info: Dict[str, List[Person]],
        retransfer_relationships: Dict[str, Dict[str, str]],
        second_inheritance_renounced: Dict[str, List[Person]]
    ) -> InheritanceResult:
        """
        再転相続の処理（情報付き版）

        Args:
            result: 現在の相続計算結果
            retransfer_info: 再転相続先の情報（相続人ID: 再転相続先リスト）
            retransfer_relationships: 再転相続先の関係情報（相続人ID: {人物ID: 関係タイプ}）
            second_inheritance_renounced: 第2次相続の放棄者情報（死亡相続人ID: 放棄者リスト）

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

            # 判例制約の検証: 第2次相続を放棄した者が第1次相続の再転相続先に含まれていないか
            self._validate_retransfer_renunciation(
                result.decedent,
                original_heir.person,
                retransfer_targets,
                second_inheritance_renounced.get(heir_id, [])
            )

            # 再転相続先を相続順位別に分類
            # retransfer_relationships から該当する相続人の関係情報を取得
            relationship_hints = retransfer_relationships.get(heir_id, None)

            classified_heirs = self._classify_retransfer_heirs(
                retransfer_targets,
                original_heir.person,
                relationship_hints
            )

            # 再転相続分を計算（法定相続分に基づく）
            retransfer_shares = self._calculate_retransfer_shares_classified(
                original_heir.share,
                classified_heirs
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

    def _validate_retransfer_renunciation(
        self,
        decedent: Person,
        deceased_heir: Person,
        retransfer_targets: List[Person],
        second_inheritance_renounced: List[Person]
    ) -> None:
        """
        再転相続における相続放棄の制約を検証

        判例（最高裁昭和63年6月21日判決）により、再転相続において
        第2次相続（相続人の相続）を放棄した者は、第1次相続（被相続人の相続）
        のみを承認することはできない。

        Args:
            decedent: 被相続人（第1次相続の被相続人）
            deceased_heir: 遺産分割前に死亡した相続人（第2次相続の被相続人）
            retransfer_targets: 再転相続先（第1次相続を承認しようとしている者）
            second_inheritance_renounced: 第2次相続の放棄者リスト

        Raises:
            RenunciationConflictError: 第2次相続を放棄した者が第1次相続を承認しようとしている場合
        """
        for renounced_person in second_inheritance_renounced:
            if renounced_person in retransfer_targets:
                raise RenunciationConflictError(
                    f"{renounced_person.name}は{deceased_heir.name}の相続を放棄しているため、"
                    f"{decedent.name}の相続のみを承認することはできません "
                    f"（最高裁昭和63年6月21日判決）。\n"
                    f"再転相続においては、第2次相続を放棄した者は第1次相続のみを単独で承認できません。"
                )

    def _classify_retransfer_heirs(
        self,
        retransfer_targets: List[Person],
        deceased_heir: Person,
        relationship_hints: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Person]]:
        """
        再転相続先を相続順位別に分類

        relationship_hintsが提供されている場合は、それを使用して分類する。
        提供されていない場合は、暫定的に全員を子として扱う（後方互換性）。

        Args:
            retransfer_targets: 再転相続先のリスト
            deceased_heir: 遺産分割前に死亡した相続人
            relationship_hints: 人物IDから関係タイプへのマッピング
                キー: 人物ID（str(person.id)）
                値: 'spouse' | 'child' | 'parent' | 'sibling'

        Returns:
            相続順位別の分類 {'spouses': [...], 'children': [...], ...}
        """
        classified: Dict[str, List[Person]] = {
            'spouses': [],
            'children': [],
            'parents': [],
            'siblings': []
        }

        # relationship_hintsが提供されていない場合は全員を子として扱う（後方互換性）
        if relationship_hints is None:
            classified['children'] = retransfer_targets
            return classified

        # relationship_hintsを使って分類
        for person in retransfer_targets:
            person_id = str(person.id)
            relationship = relationship_hints.get(person_id, 'child')  # デフォルトは子

            if relationship == 'spouse':
                classified['spouses'].append(person)
            elif relationship == 'child':
                classified['children'].append(person)
            elif relationship == 'parent':
                classified['parents'].append(person)
            elif relationship == 'sibling':
                classified['siblings'].append(person)
            else:
                # 不明な関係タイプの場合は子として扱う
                classified['children'].append(person)

        return classified

    def _calculate_retransfer_shares_classified(
        self,
        original_share: Fraction,
        classified_heirs: Dict[str, List[Person]]
    ) -> List[tuple[Person, Fraction]]:
        """
        分類済み再転相続先の相続分を計算（民法第896条に基づく）

        遺産分割前に死亡した相続人の相続分を、その相続人の法定相続人に
        法定相続分に従って分配する。

        計算フロー:
        1. 分類済みの相続人リストを使用
        2. ShareCalculatorで法定相続分を計算
        3. 元の相続分に法定相続分を乗じて最終的な相続分を算出

        Args:
            original_share: 元の相続分（遺産分割前に死亡した相続人の相続分）
            classified_heirs: 相続順位別に分類された再転相続先

        Returns:
            各再転相続人と相続分のタプルのリスト

        Example:
            元の相続分が1/1で、配偶者1人・子2人の場合:
            - 配偶者: 1/1 × 1/2 = 1/2（民法900条1号）
            - 子1: 1/1 × 1/4 = 1/4（民法900条1号）
            - 子2: 1/1 × 1/4 = 1/4（民法900条1号）
        """
        spouses = classified_heirs.get('spouses', [])
        children = classified_heirs.get('children', [])
        parents = classified_heirs.get('parents', [])
        siblings = classified_heirs.get('siblings', [])

        # 再転相続先がいない場合
        if not (spouses or children or parents or siblings):
            return []

        # ShareCalculatorを使って法定相続分を計算
        statutory_shares = self.calculator.calculate_shares(
            spouses=spouses,
            first_rank=children,
            second_rank=parents,
            third_rank=siblings,
            third_rank_blood_types={}  # TODO: 必要に応じて血縁タイプ情報を渡す
        )

        # 元の相続分を法定相続分で按分
        result = []
        all_heirs = spouses + children + parents + siblings
        for person in all_heirs:
            person_id = str(person.id)
            if person_id in statutory_shares:
                # 元の相続分 × 再転相続先の法定相続分
                final_share = original_share * statutory_shares[person_id]
                result.append((person, final_share))

        return result

    def _calculate_retransfer_shares(
        self,
        original_share: Fraction,
        retransfer_targets: List[Person]
    ) -> List[tuple[Person, Fraction]]:
        """
        再転相続分を計算（後方互換性のためのラッパー）

        Args:
            original_share: 元の相続分
            retransfer_targets: 再転相続先のリスト

        Returns:
            各再転相続人と相続分のタプルのリスト
        """
        # 暫定的な分類（全員を子として扱う）
        classified: Dict[str, List[Person]] = {
            'spouses': [],
            'children': retransfer_targets,
            'parents': [],
            'siblings': []
        }
        return self._calculate_retransfer_shares_classified(original_share, classified)
