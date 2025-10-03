"""相続案件（Case）のPydanticスキーマ"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    """相続案件の基本情報"""

    title: str = Field(..., description="案件名", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="案件の説明")
    decedent_name: str = Field(..., description="被相続人の氏名", min_length=1)
    death_date: str = Field(..., description="死亡日（元号または西暦）")


class CaseCreate(CaseBase):
    """相続案件作成リクエスト"""

    pass


class CaseUpdate(BaseModel):
    """相続案件更新リクエスト"""

    title: Optional[str] = Field(default=None, description="案件名", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="案件の説明")
    status: Optional[str] = Field(default=None, description="ステータス")


class CaseResponse(CaseBase):
    """相続案件レスポンス"""

    id: str = Field(..., description="案件ID")
    status: str = Field(default="draft", description="ステータス (draft, in_progress, completed)")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "case-123",
                    "title": "山田太郎の相続案件",
                    "description": "配偶者と子2名のケース",
                    "decedent_name": "山田太郎",
                    "death_date": "令和5年6月15日",
                    "status": "draft",
                    "created_at": "2023-10-03T10:00:00",
                    "updated_at": "2023-10-03T10:00:00",
                }
            ]
        }
    }


class CaseListResponse(BaseModel):
    """相続案件一覧レスポンス"""

    cases: list[CaseResponse] = Field(..., description="案件リスト")
    total: int = Field(..., description="総件数")

    model_config = {"json_schema_extra": {"examples": [{"cases": [], "total": 0}]}}
