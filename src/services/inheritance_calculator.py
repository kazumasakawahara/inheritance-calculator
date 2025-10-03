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
