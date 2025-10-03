"""相続計算結果モデル"""
from typing import List, Optional, Any
from fractions import Fraction
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .person import Person


class HeritageRank(str, Enum):
    """相続順位"""
    SPOUSE = "spouse"  # 配偶者（常に相続人）
    FIRST = "first"  # 第1順位（子・直系卑属）
    SECOND = "second"  # 第2順位（直系尊属）
    THIRD = "third"  # 第3順位（兄弟姉妹）


class SubstitutionType(str, Enum):
    """代襲相続タイプ"""
    NONE = "none"  # 代襲なし
    CHILD = "child"  # 子の代襲（孫、曾孫...）
    SIBLING = "sibling"  # 兄弟姉妹の代襲（甥・姪のみ）


class Heir(BaseModel):
    """
    相続人

    相続人の資格と相続割合を表現。
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    person: Person = Field(..., description="相続人")
    rank: HeritageRank = Field(..., description="相続順位")
    share: Fraction = Field(..., description="相続割合（法定相続分）")
    share_percentage: float = Field(..., description="相続割合（百分率）")
    is_substitution: bool = Field(default=False, description="代襲相続人か")
    substitution_type: SubstitutionType = Field(
        default=SubstitutionType.NONE, description="代襲相続タイプ"
    )
    substituted_person: Optional[Person] = Field(
        default=None, description="被代襲者（代襲相続の場合）"
    )
    generation: int = Field(default=1, description="代襲世代数（1=直接相続人）")
    is_retransfer: bool = Field(default=False, description="再転相続人か")
    retransfer_from: Optional[Person] = Field(
        default=None, description="再転相続元の相続人（遺産分割前に死亡した相続人）"
    )
    original_share: Optional[Fraction] = Field(
        default=None, description="再転相続前の元の相続分"
    )

    @field_validator('share_percentage', mode='before')
    @classmethod
    def calculate_percentage(cls, v: Any, info: Any) -> float:
        """相続割合の百分率を計算"""
        # shareから計算（vが0.0の場合も含む）
        values = info.data
        share = values.get('share')
        if share is not None:
            return float(share) * 100

        # すでに計算されている場合はそのまま返す
        if isinstance(v, float):
            return v

        return 0.0

    @field_validator('substitution_type')
    @classmethod
    def validate_substitution_type(cls, v: SubstitutionType, info: Any) -> SubstitutionType:
        """代襲相続タイプの検証"""
        values = info.data
        is_substitution = values.get('is_substitution', False)

        # 代襲相続でない場合、タイプはNONEでなければならない
        if not is_substitution and v != SubstitutionType.NONE:
            raise ValueError("Non-substitution heir must have NONE type")

        # 代襲相続の場合、タイプはNONE以外でなければならない
        if is_substitution and v == SubstitutionType.NONE:
            raise ValueError("Substitution heir must have valid substitution type")

        return v

    def __str__(self) -> str:
        """文字列表現"""
        substitution_mark = ""
        if self.is_substitution:
            substitution_mark = f"（代襲: {self.substituted_person.name if self.substituted_person else '不明'}）"

        share_str = f"{self.share} ({self.share_percentage:.2f}%)"
        return f"{self.person.name} - {self.rank.value} - {share_str}{substitution_mark}"


class InheritanceResult(BaseModel):
    """
    相続計算結果

    相続人の確定と相続割合の計算結果を表現。
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    decedent: Person = Field(..., description="被相続人")
    heirs: List[Heir] = Field(default_factory=list, description="相続人リスト")
    has_spouse: bool = Field(default=False, description="配偶者がいるか")
    has_children: bool = Field(default=False, description="子がいるか")
    has_parents: bool = Field(default=False, description="直系尊属がいるか")
    has_siblings: bool = Field(default=False, description="兄弟姉妹がいるか")
    calculation_basis: List[str] = Field(
        default_factory=list, description="計算根拠（適用した民法条文等）"
    )

    @field_validator('heirs')
    @classmethod
    def validate_total_share(cls, v: List[Heir]) -> List[Heir]:
        """相続割合の合計が1（100%）であることを検証"""
        if not v:
            return v

        total = sum(heir.share for heir in v)
        if total != Fraction(1, 1):
            raise ValueError(
                f"Total share must be 1 (100%), but got {total} ({float(total) * 100}%)"
            )

        return v

    def add_heir(
        self,
        person: Person,
        rank: HeritageRank,
        share: Fraction,
        is_substitution: bool = False,
        substitution_type: SubstitutionType = SubstitutionType.NONE,
        substituted_person: Optional[Person] = None,
        generation: int = 1
    ) -> None:
        """
        相続人を追加

        Args:
            person: 相続人
            rank: 相続順位
            share: 相続割合
            is_substitution: 代襲相続人か
            substitution_type: 代襲相続タイプ
            substituted_person: 被代襲者
            generation: 代襲世代数
        """
        heir = Heir(
            person=person,
            rank=rank,
            share=share,
            share_percentage=float(share) * 100,
            is_substitution=is_substitution,
            substitution_type=substitution_type,
            substituted_person=substituted_person,
            generation=generation
        )
        self.heirs.append(heir)

    def add_calculation_basis(self, basis: str) -> None:
        """
        計算根拠を追加

        Args:
            basis: 計算根拠（民法条文等）
        """
        self.calculation_basis.append(basis)

    def get_heirs_by_rank(self, rank: HeritageRank) -> List[Heir]:
        """
        指定された順位の相続人を取得

        Args:
            rank: 相続順位

        Returns:
            相続人のリスト
        """
        return [heir for heir in self.heirs if heir.rank == rank]

    def get_substitution_heirs(self) -> List[Heir]:
        """
        代襲相続人のリストを取得

        Returns:
            代襲相続人のリスト
        """
        return [heir for heir in self.heirs if heir.is_substitution]

    @property
    def total_heirs(self) -> int:
        """相続人の総数"""
        return len(self.heirs)

    def __str__(self) -> str:
        """文字列表現"""
        result = [f"被相続人: {self.decedent.name}"]
        result.append(f"相続人総数: {self.total_heirs}名")
        result.append("---")

        for heir in self.heirs:
            result.append(str(heir))

        if self.calculation_basis:
            result.append("---")
            result.append("計算根拠:")
            for basis in self.calculation_basis:
                result.append(f"  - {basis}")

        return "\n".join(result)
