"""ベースモデルクラス"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class BaseEntity(BaseModel):
    """全エンティティの基底クラス"""

    model_config = ConfigDict(
        # JSON互換性
        json_encoders={datetime: lambda v: v.isoformat()},
        # バリデーション設定
        validate_assignment=True,
        # 追加フィールドを許可しない
        extra='forbid',
    )

    id: UUID = Field(default_factory=uuid4, description="エンティティID")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: Optional[datetime] = Field(default=None, description="更新日時")

    def mark_updated(self) -> None:
        """更新日時を記録"""
        self.updated_at = datetime.now()


class Neo4jNode(BaseEntity):
    """Neo4jノードの基底クラス"""

    @property
    def neo4j_labels(self) -> list[str]:
        """Neo4jラベルのリスト"""
        return [self.__class__.__name__]

    @property
    def neo4j_properties(self) -> dict:
        """Neo4jプロパティの辞書"""
        return self.model_dump(exclude={'id'})


class Neo4jRelationship(BaseModel):
    """Neo4jリレーションシップの基底クラス"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    @property
    def neo4j_type(self) -> str:
        """Neo4jリレーションシップタイプ"""
        return self.__class__.__name__.upper()

    @property
    def neo4j_properties(self) -> dict:
        """Neo4jプロパティの辞書"""
        return self.model_dump()
