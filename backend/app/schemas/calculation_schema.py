"""相続計算結果のPydanticスキーマ"""

from typing import Optional
from pydantic import BaseModel, Field


class HeirInfo(BaseModel):
    """相続人情報"""

    person_id: str = Field(..., description="人物ID")
    name: str = Field(..., description="氏名")
    relationship: str = Field(..., description="続柄")
    rank: int = Field(..., description="相続順位（0=配偶者, 1-3=第1-3順位）")
    share_numerator: int = Field(..., description="相続割合の分子")
    share_denominator: int = Field(..., description="相続割合の分母")
    share_percentage: float = Field(..., description="相続割合（パーセント）")
    is_substitute: bool = Field(default=False, description="代襲相続フラグ")
    substitute_for: Optional[str] = Field(default=None, description="代襲される人物ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "person_id": "person-123",
                    "name": "山田花子",
                    "relationship": "配偶者",
                    "rank": 0,
                    "share_numerator": 1,
                    "share_denominator": 2,
                    "share_percentage": 50.0,
                    "is_substitute": False,
                    "substitute_for": None,
                }
            ]
        }
    }


class CalculationResult(BaseModel):
    """相続計算結果"""

    case_id: str = Field(..., description="案件ID")
    decedent_name: str = Field(..., description="被相続人氏名")
    heirs: list[HeirInfo] = Field(..., description="相続人リスト")
    total_heirs: int = Field(..., description="相続人総数")
    calculation_basis: str = Field(..., description="計算根拠（民法条文など）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "case_id": "case-123",
                    "decedent_name": "山田太郎",
                    "heirs": [],
                    "total_heirs": 0,
                    "calculation_basis": "民法890条（配偶者の相続権）、民法900条（法定相続分）",
                }
            ]
        }
    }


class CalculationRequest(BaseModel):
    """相続計算リクエスト"""

    case_id: str = Field(..., description="計算対象の案件ID")

    model_config = {"json_schema_extra": {"examples": [{"case_id": "case-123"}]}}
