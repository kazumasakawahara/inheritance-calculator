"""元号変換サービス

既存のera_converterモジュールをバックエンドAPIから利用可能にするラッパー
"""

import sys
from pathlib import Path
from datetime import date

# 親プロジェクトのsrcディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from utils.era_converter import (  # type: ignore[import-not-found]
    parse_japanese_date,
    format_japanese_date,
    get_era_name,
    EraConversionError,
)

__all__ = [
    "parse_japanese_date",
    "format_japanese_date",
    "get_era_name",
    "EraConversionError",
]


def convert_era_to_western(era_str: str) -> str:
    """元号形式の日付文字列を西暦形式(YYYY-MM-DD)に変換

    Args:
        era_str: 元号形式の日付文字列（例: "令和5年10月3日", "R5.10.3"）

    Returns:
        str: 西暦形式の日付文字列（例: "2023-10-03"）

    Raises:
        EraConversionError: 変換できない形式の場合
    """
    parsed_date: date = parse_japanese_date(era_str)
    result: str = parsed_date.isoformat()
    return result


def convert_western_to_era(western_str: str, format_type: str = "long") -> str:
    """西暦形式の日付文字列を元号形式に変換

    Args:
        western_str: 西暦形式の日付文字列（例: "2023-10-03"）
        format_type: 出力形式 ("long", "short", "slash")

    Returns:
        str: 元号形式の日付文字列

    Raises:
        EraConversionError: 変換できない形式の場合
    """
    parsed_date = date.fromisoformat(western_str)
    result: str = format_japanese_date(parsed_date, format_type)
    return result
