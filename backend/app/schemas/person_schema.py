"""人物（Person）のPydanticスキーマ"""

from typing import Optional
from pydantic import BaseModel, Field


class PersonBase(BaseModel):
    """人物の基本情報"""

    name: str = Field(..., description="氏名", min_length=1, max_length=100)
    is_alive: bool = Field(default=True, description="生存状態")
    death_date: Optional[str] = Field(default=None, description="死亡日（元号または西暦）")
    birth_date: Optional[str] = Field(default=None, description="生年月日（元号または西暦）")
    gender: Optional[str] = Field(default=None, description="性別")


class PersonCreate(PersonBase):
    """人物作成リクエスト"""

    case_id: str = Field(..., description="所属する案件ID")
    is_decedent: bool = Field(default=False, description="被相続人フラグ")


class PersonUpdate(BaseModel):
    """人物更新リクエスト"""

    name: Optional[str] = Field(default=None, description="氏名", min_length=1, max_length=100)
    is_alive: Optional[bool] = Field(default=None, description="生存状態")
    death_date: Optional[str] = Field(default=None, description="死亡日")
    birth_date: Optional[str] = Field(default=None, description="生年月日")
    gender: Optional[str] = Field(default=None, description="性別")


class PersonResponse(PersonBase):
    """人物レスポンス"""

    id: str = Field(..., description="人物ID")
    is_decedent: bool = Field(..., description="被相続人フラグ")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "person-123",
                    "name": "山田太郎",
                    "is_alive": False,
                    "death_date": "令和5年6月15日",
                    "birth_date": "昭和30年3月10日",
                    "gender": "男性",
                    "is_decedent": True,
                }
            ]
        }
    }


class RelationshipCreate(BaseModel):
    """関係性作成リクエスト"""

    case_id: str = Field(..., description="所属する案件ID")
    from_person_id: str = Field(..., description="関係の起点となる人物ID")
    to_person_id: str = Field(..., description="関係の終点となる人物ID")
    relationship_type: str = Field(
        ...,
        description="関係性タイプ (CHILD_OF, SPOUSE_OF, SIBLING_OF, RENOUNCED, DISQUALIFIED, DISINHERITED)",
    )
    properties: Optional[dict[str, str | bool | int]] = Field(default=None, description="関係性の追加属性")


class RelationshipResponse(BaseModel):
    """関係性レスポンス"""

    from_person_id: str = Field(..., description="起点人物ID")
    to_person_id: str = Field(..., description="終点人物ID")
    relationship_type: str = Field(..., description="関係性タイプ")
    properties: dict[str, str | bool | int] = Field(default_factory=dict, description="関係性の追加属性")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "from_person_id": "person-123",
                    "to_person_id": "person-456",
                    "relationship_type": "CHILD_OF",
                    "properties": {"is_biological": True, "adoption": False},
                }
            ]
        }
    }


class FamilyTreeResponse(BaseModel):
    """家系図レスポンス"""

    persons: list[PersonResponse] = Field(..., description="人物リスト")
    relationships: list[RelationshipResponse] = Field(..., description="関係性リスト")

    model_config = {"json_schema_extra": {"examples": [{"persons": [], "relationships": []}]}}
