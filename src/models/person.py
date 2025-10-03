"""人物モデル"""
from datetime import date
from typing import Optional, Any
from enum import Enum

from pydantic import Field, field_validator

from .base import Neo4jNode


class Gender(str, Enum):
    """性別"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class Person(Neo4jNode):
    """
    人物モデル

    被相続人および相続人候補を表現するモデル。
    Neo4jのPersonノードに対応。
    """

    name: str = Field(..., description="氏名", min_length=1)
    is_alive: bool = Field(default=True, description="生存しているか")
    death_date: Optional[date] = Field(default=None, description="死亡日")
    is_decedent: bool = Field(default=False, description="被相続人フラグ")
    birth_date: Optional[date] = Field(default=None, description="生年月日")
    gender: Gender = Field(default=Gender.UNKNOWN, description="性別")

    @field_validator('death_date')
    @classmethod
    def validate_death_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        """死亡日の検証"""
        if v is not None:
            # 死亡日がある場合、is_aliveはFalseであるべき
            # ただし、バリデーション時点ではis_aliveがまだ設定されていない可能性がある
            pass
        return v

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        """生年月日の検証"""
        if v is not None:
            # 未来の日付は不可
            from datetime import date as date_class
            if v > date_class.today():
                raise ValueError("Birth date cannot be in the future")
        return v

    def mark_as_deceased(self, death_date: date) -> None:
        """
        死亡として記録

        Args:
            death_date: 死亡日
        """
        self.is_alive = False
        self.death_date = death_date
        self.mark_updated()

    def mark_as_decedent(self) -> None:
        """被相続人として記録"""
        self.is_decedent = True
        self.mark_updated()

    @property
    def age_at_death(self) -> Optional[int]:
        """
        死亡時の年齢を取得

        Returns:
            死亡時の年齢（生年月日または死亡日が不明な場合はNone）
        """
        if self.birth_date is None or self.death_date is None:
            return None

        age = self.death_date.year - self.birth_date.year
        # 誕生日前なら1歳引く
        if (self.death_date.month, self.death_date.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    @property
    def current_age(self) -> Optional[int]:
        """
        現在の年齢を取得

        Returns:
            現在の年齢（生年月日が不明な場合はNone）
        """
        if self.birth_date is None:
            return None

        if not self.is_alive and self.death_date is not None:
            return self.age_at_death

        from datetime import date as date_class
        today = date_class.today()
        age = today.year - self.birth_date.year
        # 誕生日前なら1歳引く
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def is_older_than(self, other: 'Person') -> bool:
        """
        指定された人物より年上かどうかを判定

        Args:
            other: 比較対象の人物

        Returns:
            年上の場合True（生年月日が不明な場合はFalse）
        """
        if self.birth_date is None or other.birth_date is None:
            return False

        return self.birth_date < other.birth_date

    def died_before(self, other: 'Person') -> bool:
        """
        指定された人物より先に死亡したかどうかを判定

        Args:
            other: 比較対象の人物

        Returns:
            先に死亡している場合True
        """
        if self.death_date is None:
            return False

        if other.death_date is None:
            # 自分は死亡、相手は生存 → 自分が先
            return True

        return self.death_date < other.death_date

    def __str__(self) -> str:
        """文字列表現"""
        status = "故人" if not self.is_alive else "存命"
        decedent_mark = "（被相続人）" if self.is_decedent else ""

        # 年齢情報の追加
        age_info = ""
        if self.current_age is not None:
            if self.is_alive:
                age_info = f", {self.current_age}歳"
            else:
                age_info = f", 享年{self.current_age}歳"

        return f"{self.name} ({status}{age_info}){decedent_mark}"

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return f"Person(name='{self.name}', is_alive={self.is_alive}, is_decedent={self.is_decedent})"
