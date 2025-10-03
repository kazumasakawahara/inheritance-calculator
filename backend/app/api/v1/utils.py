"""ユーティリティAPI - 元号変換エンドポイント"""

from fastapi import APIRouter, HTTPException, status
from app.schemas import DateConversionRequest, DateConversionResponse, ErrorResponse
from app.services.era_converter import (
    parse_japanese_date,
    format_japanese_date,
    get_era_name,
    EraConversionError,
)
from datetime import date

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/convert-era-to-western",
    response_model=DateConversionResponse,
    responses={400: {"model": ErrorResponse}},
    summary="元号を西暦に変換",
    description="元号形式の日付（令和5年10月3日、R5.10.3など）を西暦形式(YYYY-MM-DD)に変換します。",
)
async def convert_era_to_western(request: DateConversionRequest) -> DateConversionResponse:
    """元号形式の日付を西暦に変換

    Args:
        request: 変換リクエスト

    Returns:
        DateConversionResponse: 変換結果

    Raises:
        HTTPException: 変換エラー時
    """
    try:
        parsed_date = parse_japanese_date(request.date_str)
        western_str = parsed_date.isoformat()
        era_name = get_era_name(parsed_date)

        return DateConversionResponse(
            original=request.date_str,
            converted=western_str,
            era_name=era_name,
        )
    except EraConversionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/convert-western-to-era",
    response_model=DateConversionResponse,
    responses={400: {"model": ErrorResponse}},
    summary="西暦を元号に変換",
    description="西暦形式の日付(YYYY-MM-DD)を元号形式に変換します。format_typeで出力形式を指定できます。",
)
async def convert_western_to_era(request: DateConversionRequest) -> DateConversionResponse:
    """西暦形式の日付を元号に変換

    Args:
        request: 変換リクエスト (format_type: "long", "short", "slash")

    Returns:
        DateConversionResponse: 変換結果

    Raises:
        HTTPException: 変換エラー時
    """
    try:
        # 西暦文字列をdateオブジェクトに変換
        parsed_date = date.fromisoformat(request.date_str)

        # 元号形式に変換
        era_str = format_japanese_date(parsed_date, request.format_type)
        era_name = get_era_name(parsed_date)

        return DateConversionResponse(
            original=request.date_str,
            converted=era_str,
            era_name=era_name,
        )
    except (ValueError, EraConversionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/detect-and-convert",
    response_model=DateConversionResponse,
    responses={400: {"model": ErrorResponse}},
    summary="自動判定して変換",
    description="入力された日付形式を自動判定し、元号⇔西暦の適切な変換を行います。",
)
async def detect_and_convert(request: DateConversionRequest) -> DateConversionResponse:
    """日付形式を自動判定して変換

    元号形式なら西暦に、西暦形式なら元号に変換します。

    Args:
        request: 変換リクエスト

    Returns:
        DateConversionResponse: 変換結果

    Raises:
        HTTPException: 変換エラー時
    """
    import re

    try:
        # 西暦形式かチェック（YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD）
        western_pattern = r"^(\d{4})[\-/.](\d{1,2})[\-/.](\d{1,2})$"
        if re.match(western_pattern, request.date_str):
            # 西暦形式 → 元号に変換
            parsed_date = date.fromisoformat(request.date_str.replace("/", "-").replace(".", "-"))
            era_str = format_japanese_date(parsed_date, request.format_type)
            era_name = get_era_name(parsed_date)
            return DateConversionResponse(
                original=request.date_str,
                converted=era_str,
                era_name=era_name,
            )
        else:
            # 元号形式 → 西暦に変換
            parsed_date = parse_japanese_date(request.date_str)
            western_str = parsed_date.isoformat()
            era_name = get_era_name(parsed_date)
            return DateConversionResponse(
                original=request.date_str,
                converted=western_str,
                era_name=era_name,
            )
    except (ValueError, EraConversionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日付変換エラー: {str(e)}",
        ) from e
