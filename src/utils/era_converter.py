"""日本の元号と西暦の変換ユーティリティ

このモジュールは日本の元号（明治、大正、昭和、平成、令和）と
西暦の相互変換機能を提供します。
"""

from datetime import date
from typing import Dict, Optional, Tuple
import re


# 元号マッピングデータ
# Format: 元号名 -> (略称, 開始年, 開始月, 開始日, 終了年, 終了月, 終了日)
ERA_MAP: Dict[str, Tuple[str, int, int, int, Optional[int], Optional[int], Optional[int]]] = {
    "明治": ("M", 1868, 1, 25, 1912, 7, 30),
    "大正": ("T", 1912, 7, 30, 1926, 12, 25),
    "昭和": ("S", 1926, 12, 25, 1989, 1, 7),
    "平成": ("H", 1989, 1, 8, 2019, 4, 30),
    "令和": ("R", 2019, 5, 1, None, None, None),
}

# 略称から元号名へのマッピング
ABBREV_TO_ERA: Dict[str, str] = {
    "M": "明治",
    "T": "大正",
    "S": "昭和",
    "H": "平成",
    "R": "令和",
}


class EraConversionError(ValueError):
    """元号変換エラー"""
    pass


def parse_japanese_date(input_str: str) -> date:
    """元号形式の日付を西暦dateオブジェクトに変換

    Args:
        input_str: 元号形式の日付文字列
                  例: "令和5年10月3日", "R5.10.3", "R5/10/3"

    Returns:
        date: 西暦のdateオブジェクト

    Raises:
        EraConversionError: 変換できない形式の場合

    Examples:
        >>> parse_japanese_date("令和5年10月3日")
        datetime.date(2023, 10, 3)
        >>> parse_japanese_date("R5.10.3")
        datetime.date(2023, 10, 3)
        >>> parse_japanese_date("H31/4/30")
        datetime.date(2019, 4, 30)
    """
    # 全角数字を半角に変換
    input_str = _normalize_numbers(input_str)

    # パターン1: 令和5年10月3日
    pattern1 = r"^([明大昭平令][治正和成和])(\d{1,2})年(\d{1,2})月(\d{1,2})日$"
    match = re.match(pattern1, input_str)
    if match:
        era_name = match.group(1)
        era_year = int(match.group(2))
        month = int(match.group(3))
        day = int(match.group(4))
        return _convert_era_to_date(era_name, era_year, month, day)

    # パターン2: R5.10.3 または R5/10/3
    pattern2 = r"^([MTSHR])(\d{1,2})[./](\d{1,2})[./](\d{1,2})$"
    match = re.match(pattern2, input_str)
    if match:
        abbrev = match.group(1)
        era_year = int(match.group(2))
        month = int(match.group(3))
        day = int(match.group(4))

        if abbrev not in ABBREV_TO_ERA:
            raise EraConversionError(f"不明な元号略称: {abbrev}")

        era_name = ABBREV_TO_ERA[abbrev]
        return _convert_era_to_date(era_name, era_year, month, day)

    # パターン3: 西暦形式（YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD）
    pattern3 = r"^(\d{4})[\-/.](\d{1,2})[\-/.](\d{1,2})$"
    match = re.match(pattern3, input_str)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        try:
            return date(year, month, day)
        except ValueError as e:
            raise EraConversionError(f"無効な日付: {input_str}") from e

    raise EraConversionError(
        f"サポートされていない日付形式: {input_str}\n"
        f"サポート形式: 令和5年10月3日, R5.10.3, R5/10/3, 2023-10-03"
    )


def _normalize_numbers(text: str) -> str:
    """全角数字を半角数字に変換"""
    zen_to_han = str.maketrans("０１２３４５６７８９", "0123456789")
    return text.translate(zen_to_han)


def _convert_era_to_date(era_name: str, era_year: int, month: int, day: int) -> date:
    """元号と年月日を西暦dateに変換

    Args:
        era_name: 元号名（例: "令和"）
        era_year: 元号の年（例: 5）
        month: 月
        day: 日

    Returns:
        date: 西暦のdateオブジェクト

    Raises:
        EraConversionError: 無効な元号や日付の場合
    """
    if era_name not in ERA_MAP:
        raise EraConversionError(f"不明な元号: {era_name}")

    abbrev, start_year, start_month, start_day, end_year, end_month, end_day = ERA_MAP[era_name]

    # 元号元年は1年として扱う
    if era_year < 1:
        raise EraConversionError(f"{era_name}の年は1以上である必要があります: {era_year}")

    # 西暦年を計算
    western_year = start_year + era_year - 1

    # 日付を作成
    try:
        result_date = date(western_year, month, day)
    except ValueError as e:
        raise EraConversionError(f"無効な日付: {era_name}{era_year}年{month}月{day}日") from e

    # 元号の開始日より前でないかチェック
    era_start = date(start_year, start_month, start_day)
    if result_date < era_start:
        raise EraConversionError(
            f"{era_name}{era_year}年{month}月{day}日は{era_name}の開始日（{era_start}）より前です"
        )

    # 元号の終了日より後でないかチェック（令和は終了日なし）
    if end_year is not None and end_month is not None and end_day is not None:
        era_end = date(end_year, end_month, end_day)
        if result_date > era_end:
            raise EraConversionError(
                f"{era_name}{era_year}年{month}月{day}日は{era_name}の終了日（{era_end}）より後です"
            )

    return result_date


def format_japanese_date(target_date: date, format_type: str = "long") -> str:
    """西暦dateを元号形式の文字列に変換

    Args:
        target_date: 西暦のdateオブジェクト
        format_type: 出力形式
                    - "long": 令和5年10月3日
                    - "short": R5.10.3
                    - "slash": R5/10/3

    Returns:
        str: 元号形式の日付文字列

    Raises:
        EraConversionError: 明治以前の日付の場合

    Examples:
        >>> format_japanese_date(date(2023, 10, 3), "long")
        '令和5年10月3日'
        >>> format_japanese_date(date(2023, 10, 3), "short")
        'R5.10.3'
    """
    # 該当する元号を検索
    for era_name, (abbrev, start_year, start_month, start_day, end_year, end_month, end_day) in ERA_MAP.items():
        era_start = date(start_year, start_month, start_day)

        # 終了日の判定
        if end_year is not None and end_month is not None and end_day is not None:
            era_end = date(end_year, end_month, end_day)
            if era_start <= target_date <= era_end:
                era_year = target_date.year - start_year + 1
                return _format_era_string(era_name, abbrev, era_year, target_date.month, target_date.day, format_type)
        else:
            # 令和（終了日なし）
            if target_date >= era_start:
                era_year = target_date.year - start_year + 1
                return _format_era_string(era_name, abbrev, era_year, target_date.month, target_date.day, format_type)

    raise EraConversionError(f"明治以前の日付は変換できません: {target_date}")


def _format_era_string(era_name: str, abbrev: str, era_year: int, month: int, day: int, format_type: str) -> str:
    """元号文字列をフォーマット"""
    if format_type == "long":
        return f"{era_name}{era_year}年{month}月{day}日"
    elif format_type == "short":
        return f"{abbrev}{era_year}.{month}.{day}"
    elif format_type == "slash":
        return f"{abbrev}{era_year}/{month}/{day}"
    else:
        raise ValueError(f"不明なフォーマット: {format_type}")


def get_era_name(target_date: date) -> str:
    """指定された日付の元号名を取得

    Args:
        target_date: 西暦のdateオブジェクト

    Returns:
        str: 元号名（例: "令和"）

    Raises:
        EraConversionError: 明治以前の日付の場合
    """
    for era_name, (abbrev, start_year, start_month, start_day, end_year, end_month, end_day) in ERA_MAP.items():
        era_start = date(start_year, start_month, start_day)

        if end_year is not None and end_month is not None and end_day is not None:
            era_end = date(end_year, end_month, end_day)
            if era_start <= target_date <= era_end:
                return era_name
        else:
            if target_date >= era_start:
                return era_name

    raise EraConversionError(f"明治以前の日付は対応していません: {target_date}")
