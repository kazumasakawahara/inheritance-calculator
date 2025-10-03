"""相続割合計算サービス

日本の民法に基づいて相続割合（法定相続分）を計算するサービス。
"""
from typing import List, Dict, Optional
from fractions import Fraction

from ..models.person import Person
from ..models.relationship import BloodType
from ..models.inheritance import HeritageRank
from .base import BaseService


class ShareCalculator(BaseService[Person]):
    """
    相続割合計算サービス

    法定相続分を計算する。
    """

    def calculate_shares(
        self,
        spouses: List[Person],
        first_rank: List[Person],
        second_rank: List[Person],
        third_rank: List[Person],
        third_rank_blood_types: Optional[Dict[str, BloodType]] = None
    ) -> Dict[str, Fraction]:
        """
        相続割合を計算

        Args:
            spouses: 配偶者のリスト
            first_rank: 第1順位の相続人（子）
            second_rank: 第2順位の相続人（直系尊属）
            third_rank: 第3順位の相続人（兄弟姉妹）
            third_rank_blood_types: 第3順位の血縁タイプ（人物ID → BloodType）

        Returns:
            人物ID → 相続割合の辞書
        """
        if third_rank_blood_types is None:
            third_rank_blood_types = {}

        shares: Dict[str, Fraction] = {}

        # 配偶者のみの場合
        if spouses and not first_rank and not second_rank and not third_rank:
            shares.update(self._calculate_spouse_only(spouses))
            self.log_operation(
                "Calculated shares: spouse only",
                basis="配偶者のみ（全部相続）"
            )
            return shares

        # 配偶者と子
        if spouses and first_rank:
            shares.update(self._calculate_spouse_and_children(spouses, first_rank))
            self.log_operation(
                "Calculated shares: spouse and children",
                basis="民法900条1号"
            )
            return shares

        # 子のみ
        if first_rank and not spouses:
            shares.update(self._calculate_children_only(first_rank))
            self.log_operation(
                "Calculated shares: children only",
                basis="子のみ（均等分割）"
            )
            return shares

        # 配偶者と直系尊属
        if spouses and second_rank:
            shares.update(self._calculate_spouse_and_parents(spouses, second_rank))
            self.log_operation(
                "Calculated shares: spouse and parents",
                basis="民法900条2号"
            )
            return shares

        # 直系尊属のみ
        if second_rank and not spouses:
            shares.update(self._calculate_parents_only(second_rank))
            self.log_operation(
                "Calculated shares: parents only",
                basis="直系尊属のみ（均等分割）"
            )
            return shares

        # 配偶者と兄弟姉妹
        if spouses and third_rank:
            shares.update(
                self._calculate_spouse_and_siblings(
                    spouses, third_rank, third_rank_blood_types
                )
            )
            self.log_operation(
                "Calculated shares: spouse and siblings",
                basis="民法900条3号・4号"
            )
            return shares

        # 兄弟姉妹のみ
        if third_rank and not spouses:
            shares.update(
                self._calculate_siblings_only(third_rank, third_rank_blood_types)
            )
            self.log_operation(
                "Calculated shares: siblings only",
                basis="兄弟姉妹のみ（民法900条4号）"
            )
            return shares

        # 相続人がいない場合
        self.log_warning("No heirs found")
        return shares

    def _calculate_spouse_only(self, spouses: List[Person]) -> Dict[str, Fraction]:
        """配偶者のみの場合（全部相続）"""
        shares = {}
        share_per_spouse = Fraction(1, len(spouses))
        for spouse in spouses:
            shares[str(spouse.id)] = share_per_spouse
        return shares

    def _calculate_spouse_and_children(
        self, spouses: List[Person], children: List[Person]
    ) -> Dict[str, Fraction]:
        """
        配偶者と子の場合

        民法900条1号：
        - 配偶者: 1/2
        - 子: 1/2を均等に分割
        """
        shares = {}

        # 配偶者: 1/2
        spouse_total = Fraction(1, 2)
        share_per_spouse = spouse_total / len(spouses)
        for spouse in spouses:
            shares[str(spouse.id)] = share_per_spouse

        # 子: 1/2を均等に分割
        children_total = Fraction(1, 2)
        share_per_child = children_total / len(children)
        for child in children:
            shares[str(child.id)] = share_per_child

        return shares

    def _calculate_children_only(self, children: List[Person]) -> Dict[str, Fraction]:
        """子のみの場合（均等分割）"""
        shares = {}
        share_per_child = Fraction(1, len(children))
        for child in children:
            shares[str(child.id)] = share_per_child
        return shares

    def _calculate_spouse_and_parents(
        self, spouses: List[Person], parents: List[Person]
    ) -> Dict[str, Fraction]:
        """
        配偶者と直系尊属の場合

        民法900条2号：
        - 配偶者: 2/3
        - 直系尊属: 1/3を均等に分割
        """
        shares = {}

        # 配偶者: 2/3
        spouse_total = Fraction(2, 3)
        share_per_spouse = spouse_total / len(spouses)
        for spouse in spouses:
            shares[str(spouse.id)] = share_per_spouse

        # 直系尊属: 1/3を均等に分割
        parents_total = Fraction(1, 3)
        share_per_parent = parents_total / len(parents)
        for parent in parents:
            shares[str(parent.id)] = share_per_parent

        return shares

    def _calculate_parents_only(self, parents: List[Person]) -> Dict[str, Fraction]:
        """直系尊属のみの場合（均等分割）"""
        shares = {}
        share_per_parent = Fraction(1, len(parents))
        for parent in parents:
            shares[str(parent.id)] = share_per_parent
        return shares

    def _calculate_spouse_and_siblings(
        self,
        spouses: List[Person],
        siblings: List[Person],
        blood_types: Dict[str, BloodType]
    ) -> Dict[str, Fraction]:
        """
        配偶者と兄弟姉妹の場合

        民法900条3号：
        - 配偶者: 3/4
        - 兄弟姉妹: 1/4を分割

        民法900条4号：
        - 半血兄弟姉妹の相続分は全血兄弟姉妹の1/2
        """
        shares = {}

        # 配偶者: 3/4
        spouse_total = Fraction(3, 4)
        share_per_spouse = spouse_total / len(spouses)
        for spouse in spouses:
            shares[str(spouse.id)] = share_per_spouse

        # 兄弟姉妹: 1/4を血縁タイプに応じて分割
        siblings_total = Fraction(1, 4)
        shares.update(
            self._calculate_sibling_shares(siblings, siblings_total, blood_types)
        )

        return shares

    def _calculate_siblings_only(
        self,
        siblings: List[Person],
        blood_types: Dict[str, BloodType]
    ) -> Dict[str, Fraction]:
        """
        兄弟姉妹のみの場合

        民法900条4号：
        - 半血兄弟姉妹の相続分は全血兄弟姉妹の1/2
        """
        shares = {}
        total = Fraction(1, 1)
        shares.update(self._calculate_sibling_shares(siblings, total, blood_types))
        return shares

    def _calculate_sibling_shares(
        self,
        siblings: List[Person],
        total: Fraction,
        blood_types: Dict[str, BloodType]
    ) -> Dict[str, Fraction]:
        """
        兄弟姉妹の相続分を計算

        民法900条4号：半血兄弟姉妹の相続分は全血兄弟姉妹の1/2

        Args:
            siblings: 兄弟姉妹のリスト
            total: 兄弟姉妹全体の相続分
            blood_types: 血縁タイプ（人物ID → BloodType）

        Returns:
            人物ID → 相続割合の辞書
        """
        shares = {}

        # 全血・半血の人数をカウント
        full_blood_count = sum(
            1 for s in siblings
            if blood_types.get(str(s.id), BloodType.FULL) == BloodType.FULL
        )
        half_blood_count = len(siblings) - full_blood_count

        # 全血を1、半血を0.5として重み付けした総数を計算
        # 全血1人 = 重み1.0、半血1人 = 重み0.5
        total_weight = full_blood_count + (half_blood_count * Fraction(1, 2))

        # 各兄弟姉妹の相続分を計算
        for sibling in siblings:
            blood_type = blood_types.get(str(sibling.id), BloodType.FULL)

            if blood_type == BloodType.FULL:
                # 全血: total / total_weight
                shares[str(sibling.id)] = total / total_weight
            else:
                # 半血: (total / total_weight) * 1/2
                shares[str(sibling.id)] = (total / total_weight) * Fraction(1, 2)

        return shares
