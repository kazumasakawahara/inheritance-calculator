"""相続計算API"""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import CalculationRequest, CalculationResult, ErrorResponse
from app.services.neo4j_service import Neo4jService, get_neo4j_service
from app.services.calculation_service import CalculationService

router = APIRouter(prefix="/calculation", tags=["calculation"])


@router.post(
    "/calculate",
    response_model=CalculationResult,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="相続計算実行",
    description="指定された案件の相続人と相続割合を計算します。",
)
async def calculate_inheritance(
    request: CalculationRequest, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> CalculationResult:
    """相続計算実行

    Args:
        request: 計算リクエスト
        neo4j: Neo4jサービス（DI）

    Returns:
        CalculationResult: 計算結果

    Raises:
        HTTPException: 計算エラー時
    """
    try:
        # 計算サービス初期化
        calc_service = CalculationService(neo4j)

        # 相続計算実行
        result = calc_service.calculate_inheritance(request.case_id)

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"相続計算エラー: {str(e)}"
        ) from e


@router.get(
    "/cases/{case_id}/calculate",
    response_model=CalculationResult,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="相続計算実行（GETメソッド）",
    description="指定された案件IDの相続人と相続割合を計算します。",
)
async def calculate_inheritance_by_case_id(
    case_id: str, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> CalculationResult:
    """相続計算実行（GETメソッド）

    Args:
        case_id: 案件ID
        neo4j: Neo4jサービス（DI）

    Returns:
        CalculationResult: 計算結果

    Raises:
        HTTPException: 計算エラー時
    """
    try:
        # 計算サービス初期化
        calc_service = CalculationService(neo4j)

        # 相続計算実行
        result = calc_service.calculate_inheritance(case_id)

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"相続計算エラー: {str(e)}"
        ) from e
