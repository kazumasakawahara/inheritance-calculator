"""関係性モデル"""
from datetime import date
from typing import Optional, Any
from enum import Enum
from uuid import UUID

from pydantic import Field, field_validator

from .base import Neo4jRelationship


class BloodType(str, Enum):
    """血縁タイプ"""
    FULL = "full"  # 全血（父母が同じ）
    HALF = "half"  # 半血（父または母が同じ）


class SharedParent(str, Enum):
    """共通の親"""
    BOTH = "both"  # 両親とも同じ
    MOTHER = "mother"  # 母のみ同じ
    FATHER = "father"  # 父のみ同じ


class ChildOf(Neo4jRelationship):
    """
    子関係（CHILD_OF）

    子から親への関係を表現。
    """

    parent_id: UUID = Field(..., description="親のID")
    child_id: UUID = Field(..., description="子のID")
    is_adoption: bool = Field(default=False, description="養子縁組であるか")
    is_biological: bool = Field(default=True, description="実子であるか")
    adoption_date: Optional[date] = Field(default=None, description="養子縁組日")

    @field_validator('is_biological')
    @classmethod
    def validate_biological(cls, v: bool, info: Any) -> bool:
        """実子フラグの検証"""
        # 養子の場合、実子ではない
        values = info.data
        if values.get('is_adoption', False) and v:
            raise ValueError("Adopted child cannot be biological")
        return v


class SpouseOf(Neo4jRelationship):
    """
    配偶者関係（SPOUSE_OF）

    配偶者間の関係を表現。
    """

    person1_id: UUID = Field(..., description="配偶者1のID")
    person2_id: UUID = Field(..., description="配偶者2のID")
    marriage_date: Optional[date] = Field(default=None, description="婚姻日")
    divorce_date: Optional[date] = Field(default=None, description="離婚日")
    is_current: bool = Field(default=True, description="現在の配偶者か")

    @field_validator('is_current')
    @classmethod
    def validate_current(cls, v: bool, info: Any) -> bool:
        """現在の配偶者フラグの検証"""
        values = info.data
        # 離婚日がある場合、is_currentはFalseであるべき
        if values.get('divorce_date') is not None and v:
            raise ValueError("Divorced spouse cannot be current")
        return v

    @field_validator('divorce_date')
    @classmethod
    def validate_divorce_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        """離婚日の検証"""
        if v is not None:
            values = info.data
            marriage_date = values.get('marriage_date')
            if marriage_date is not None and v < marriage_date:
                raise ValueError("Divorce date cannot be before marriage date")
        return v


class SiblingOf(Neo4jRelationship):
    """
    兄弟姉妹関係（SIBLING_OF）

    兄弟姉妹間の関係を表現。
    """

    person1_id: UUID = Field(..., description="人物1のID")
    person2_id: UUID = Field(..., description="人物2のID")
    blood_type: BloodType = Field(..., description="血縁タイプ")
    shared_parent: SharedParent = Field(..., description="共通の親")

    @field_validator('shared_parent')
    @classmethod
    def validate_shared_parent(cls, v: SharedParent, info: Any) -> SharedParent:
        """共通の親の検証"""
        values = info.data
        blood_type = values.get('blood_type')

        # 全血の場合、両親とも同じでなければならない
        if blood_type == BloodType.FULL and v != SharedParent.BOTH:
            raise ValueError("Full blood siblings must share both parents")

        # 半血の場合、片親のみ同じでなければならない
        if blood_type == BloodType.HALF and v == SharedParent.BOTH:
            raise ValueError("Half blood siblings cannot share both parents")

        return v


class Renounced(Neo4jRelationship):
    """
    相続放棄（RENOUNCED）

    相続放棄の関係を表現。
    """

    heir_id: UUID = Field(..., description="相続人のID")
    decedent_id: UUID = Field(..., description="被相続人のID")
    renounce_date: date = Field(..., description="放棄日")
    reason: Optional[str] = Field(default=None, description="放棄理由")

    @field_validator('renounce_date')
    @classmethod
    def validate_renounce_date(cls, v: date) -> date:
        """放棄日の検証"""
        from datetime import date as date_class
        # 未来の日付は不可
        if v > date_class.today():
            raise ValueError("Renounce date cannot be in the future")
        return v


class Disqualified(Neo4jRelationship):
    """
    相続欠格（DISQUALIFIED）

    相続欠格の関係を表現。
    """

    heir_id: UUID = Field(..., description="相続人のID")
    decedent_id: UUID = Field(..., description="被相続人のID")
    reason: str = Field(..., description="欠格事由", min_length=1)
    determination_date: date = Field(..., description="確定日")

    @field_validator('determination_date')
    @classmethod
    def validate_determination_date(cls, v: date) -> date:
        """確定日の検証"""
        from datetime import date as date_class
        if v > date_class.today():
            raise ValueError("Determination date cannot be in the future")
        return v


class Disinherited(Neo4jRelationship):
    """
    相続廃除（DISINHERITED）

    相続廃除の関係を表現。
    """

    heir_id: UUID = Field(..., description="相続人のID")
    decedent_id: UUID = Field(..., description="被相続人のID")
    reason: str = Field(..., description="廃除事由", min_length=1)
    court_decision_date: date = Field(..., description="審判確定日")

    @field_validator('court_decision_date')
    @classmethod
    def validate_court_decision_date(cls, v: date) -> date:
        """審判確定日の検証"""
        from datetime import date as date_class
        if v > date_class.today():
            raise ValueError("Court decision date cannot be in the future")
        return v
