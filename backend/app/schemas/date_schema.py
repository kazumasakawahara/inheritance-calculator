"""日付変換用Pydanticスキーマ"""

from pydantic import BaseModel, Field


class DateConversionRequest(BaseModel):
    """日付変換リクエスト"""

    date_str: str = Field(..., description="変換元の日付文字列")
    format_type: str = Field(default="long", description="変換先のフォーマット (long, short, slash)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"date_str": "令和5年10月3日", "format_type": "long"},
                {"date_str": "2023-10-03", "format_type": "short"},
            ]
        }
    }


class DateConversionResponse(BaseModel):
    """日付変換レスポンス"""

    original: str = Field(..., description="変換元の日付文字列")
    converted: str = Field(..., description="変換後の日付文字列")
    era_name: str | None = Field(default=None, description="元号名")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"original": "令和5年10月3日", "converted": "2023-10-03", "era_name": "令和"},
                {"original": "2023-10-03", "converted": "令和5年10月3日", "era_name": "令和"},
            ]
        }
    }


class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    detail: str = Field(..., description="エラー詳細")

    model_config = {"json_schema_extra": {"examples": [{"detail": "サポートされていない日付形式です"}]}}
