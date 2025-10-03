"""相続案件（Case）管理API"""

import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseListResponse,
    ErrorResponse,
    PersonCreate,
    PersonResponse,
    RelationshipCreate,
    FamilyTreeResponse,
)
from app.services.neo4j_service import Neo4jService, get_neo4j_service
from app.services.era_converter import parse_japanese_date, EraConversionError

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "/",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    summary="相続案件を作成",
    description="新しい相続案件を作成します。",
)
async def create_case(
    case_data: CaseCreate, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> CaseResponse:
    """相続案件作成

    Args:
        case_data: 案件作成データ
        neo4j: Neo4jサービス（DI）

    Returns:
        CaseResponse: 作成された案件

    Raises:
        HTTPException: 作成エラー時
    """
    try:
        # 死亡日の妥当性検証
        try:
            parse_japanese_date(case_data.death_date)
        except EraConversionError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"死亡日の形式が不正: {str(e)}") from e

        # 案件ID生成
        case_id = f"case-{uuid.uuid4().hex[:12]}"

        # Neo4jにCase節点作成
        case_node = neo4j.create_case_node(case_id=case_id, title=case_data.title, description=case_data.description)

        # 被相続人のPerson節点も作成
        decedent_id = f"person-{uuid.uuid4().hex[:12]}"
        neo4j.create_person_node(
            person_id=decedent_id,
            case_id=case_id,
            name=case_data.decedent_name,
            is_alive=False,
            is_decedent=True,
            death_date=case_data.death_date,
        )

        return CaseResponse(
            id=case_node["id"],
            title=case_node["title"],
            description=case_node.get("description"),
            decedent_name=case_data.decedent_name,
            death_date=case_data.death_date,
            status=case_node["status"],
            created_at=case_node["created_at"],
            updated_at=case_node["updated_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get(
    "/",
    response_model=CaseListResponse,
    summary="相続案件一覧取得",
    description="全ての相続案件を取得します。",
)
async def list_cases(neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]) -> CaseListResponse:
    """相続案件一覧取得

    Args:
        neo4j: Neo4jサービス（DI）

    Returns:
        CaseListResponse: 案件一覧
    """
    try:
        case_nodes = neo4j.get_all_cases()

        cases = []
        for case_node in case_nodes:
            # 被相続人情報を取得
            persons = neo4j.get_persons_by_case(case_node["id"])
            decedent = next((p for p in persons if p.get("is_decedent")), None)

            cases.append(
                CaseResponse(
                    id=case_node["id"],
                    title=case_node["title"],
                    description=case_node.get("description"),
                    decedent_name=decedent["name"] if decedent else "",
                    death_date=decedent.get("death_date", "") if decedent else "",
                    status=case_node["status"],
                    created_at=case_node["created_at"],
                    updated_at=case_node["updated_at"],
                )
            )

        return CaseListResponse(cases=cases, total=len(cases))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    responses={404: {"model": ErrorResponse}},
    summary="相続案件詳細取得",
    description="指定されたIDの相続案件を取得します。",
)
async def get_case(case_id: str, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]) -> CaseResponse:
    """相続案件詳細取得

    Args:
        case_id: 案件ID
        neo4j: Neo4jサービス（DI）

    Returns:
        CaseResponse: 案件詳細

    Raises:
        HTTPException: 案件が見つからない場合
    """
    try:
        case_node = neo4j.get_case_by_id(case_id)
        if not case_node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 被相続人情報を取得
        persons = neo4j.get_persons_by_case(case_id)
        decedent = next((p for p in persons if p.get("is_decedent")), None)

        return CaseResponse(
            id=case_node["id"],
            title=case_node["title"],
            description=case_node.get("description"),
            decedent_name=decedent["name"] if decedent else "",
            death_date=decedent.get("death_date", "") if decedent else "",
            status=case_node["status"],
            created_at=case_node["created_at"],
            updated_at=case_node["updated_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    responses={404: {"model": ErrorResponse}},
    summary="相続案件更新",
    description="指定されたIDの相続案件を更新します。",
)
async def update_case(
    case_id: str, case_data: CaseUpdate, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> CaseResponse:
    """相続案件更新

    Args:
        case_id: 案件ID
        case_data: 更新データ
        neo4j: Neo4jサービス（DI）

    Returns:
        CaseResponse: 更新後の案件

    Raises:
        HTTPException: 案件が見つからない場合
    """
    try:
        # 存在確認
        existing_case = neo4j.get_case_by_id(case_id)
        if not existing_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 更新データ準備（Noneでない項目のみ）
        updates = {k: v for k, v in case_data.model_dump().items() if v is not None}

        if not updates:
            # 更新項目がない場合は既存データを返す
            persons = neo4j.get_persons_by_case(case_id)
            decedent = next((p for p in persons if p.get("is_decedent")), None)
            return CaseResponse(
                id=existing_case["id"],
                title=existing_case["title"],
                description=existing_case.get("description"),
                decedent_name=decedent["name"] if decedent else "",
                death_date=decedent.get("death_date", "") if decedent else "",
                status=existing_case["status"],
                created_at=existing_case["created_at"],
                updated_at=existing_case["updated_at"],
            )

        # 更新実行
        updated_case = neo4j.update_case(case_id, updates)
        if not updated_case:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新に失敗しました")

        # 被相続人情報を取得
        persons = neo4j.get_persons_by_case(case_id)
        decedent = next((p for p in persons if p.get("is_decedent")), None)

        return CaseResponse(
            id=updated_case["id"],
            title=updated_case["title"],
            description=updated_case.get("description"),
            decedent_name=decedent["name"] if decedent else "",
            death_date=decedent.get("death_date", "") if decedent else "",
            status=updated_case["status"],
            created_at=updated_case["created_at"],
            updated_at=updated_case["updated_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="相続案件削除",
    description="指定されたIDの相続案件を削除します。関連する人物や関係性も全て削除されます。",
)
async def delete_case(case_id: str, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]) -> None:
    """相続案件削除

    Args:
        case_id: 案件ID
        neo4j: Neo4jサービス（DI）

    Raises:
        HTTPException: 案件が見つからない場合
    """
    try:
        # 存在確認
        existing_case = neo4j.get_case_by_id(case_id)
        if not existing_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 削除実行
        neo4j.delete_case(case_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


# Person管理エンドポイント
@router.post(
    "/{case_id}/persons",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
    summary="人物追加",
    description="指定された案件に人物を追加します。",
)
async def create_person(
    case_id: str, person_data: PersonCreate, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> PersonResponse:
    """人物追加

    Args:
        case_id: 案件ID
        person_data: 人物データ
        neo4j: Neo4jサービス（DI）

    Returns:
        PersonResponse: 作成された人物

    Raises:
        HTTPException: エラー時
    """
    try:
        # 案件存在確認
        case_node = neo4j.get_case_by_id(case_id)
        if not case_node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 人物ID生成
        person_id = f"person-{uuid.uuid4().hex[:12]}"

        # 追加属性準備
        kwargs = {}
        if person_data.death_date:
            kwargs["death_date"] = person_data.death_date
        if person_data.birth_date:
            kwargs["birth_date"] = person_data.birth_date
        if person_data.gender:
            kwargs["gender"] = person_data.gender

        # Person節点作成
        person_node = neo4j.create_person_node(
            person_id=person_id,
            case_id=case_id,
            name=person_data.name,
            is_alive=person_data.is_alive,
            is_decedent=person_data.is_decedent,
            **kwargs,
        )

        return PersonResponse(
            id=person_node["id"],
            name=person_node["name"],
            is_alive=person_node["is_alive"],
            death_date=person_node.get("death_date"),
            birth_date=person_node.get("birth_date"),
            gender=person_node.get("gender"),
            is_decedent=person_node["is_decedent"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get(
    "/{case_id}/persons",
    response_model=list[PersonResponse],
    responses={404: {"model": ErrorResponse}},
    summary="人物一覧取得",
    description="指定された案件の全ての人物を取得します。",
)
async def list_persons(case_id: str, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]) -> list[PersonResponse]:
    """人物一覧取得

    Args:
        case_id: 案件ID
        neo4j: Neo4jサービス（DI）

    Returns:
        list[PersonResponse]: 人物一覧

    Raises:
        HTTPException: 案件が見つからない場合
    """
    try:
        # 案件存在確認
        case_node = neo4j.get_case_by_id(case_id)
        if not case_node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 人物一覧取得
        person_nodes = neo4j.get_persons_by_case(case_id)

        return [
            PersonResponse(
                id=p["id"],
                name=p["name"],
                is_alive=p["is_alive"],
                death_date=p.get("death_date"),
                birth_date=p.get("birth_date"),
                gender=p.get("gender"),
                is_decedent=p["is_decedent"],
            )
            for p in person_nodes
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


# Relationship管理エンドポイント
@router.post(
    "/{case_id}/relationships",
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
    summary="関係性追加",
    description="人物間の関係性を追加します。",
)
async def create_relationship(
    case_id: str, rel_data: RelationshipCreate, neo4j: Annotated[Neo4jService, Depends(get_neo4j_service)]
) -> dict[str, str]:
    """関係性追加

    Args:
        case_id: 案件ID
        rel_data: 関係性データ
        neo4j: Neo4jサービス（DI）

    Returns:
        dict[str, str]: 成功メッセージ

    Raises:
        HTTPException: エラー時
    """
    try:
        # 案件存在確認
        case_node = neo4j.get_case_by_id(case_id)
        if not case_node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"案件が見つかりません: {case_id}")

        # 関係性作成
        success = neo4j.create_relationship(
            from_person_id=rel_data.from_person_id,
            to_person_id=rel_data.to_person_id,
            rel_type=rel_data.relationship_type,
            properties=rel_data.properties,
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="関係性の作成に失敗しました")

        return {"message": "関係性を作成しました"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
