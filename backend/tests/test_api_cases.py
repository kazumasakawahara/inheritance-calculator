"""Case管理APIのテスト"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Note: これらのテストは実際のNeo4jデータベースに接続することを想定しています
# Neo4jが起動していない場合はスキップされます

pytestmark = pytest.mark.skipif(
    True,  # CI環境などでNeo4jがない場合はスキップ
    reason="Neo4j integration tests require running Neo4j instance",
)


class TestCaseAPI:
    """Case管理APIのテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> None:
        """テスト前後のセットアップとクリーンアップ"""
        # テスト前: 既存のテストデータをクリーンアップ
        # （本来はここでテスト用データベースのクリーンアップを行う）
        yield
        # テスト後: クリーンアップ
        pass

    def test_create_case(self) -> None:
        """Case作成のテスト"""
        response = client.post(
            "/api/v1/cases/",
            json={
                "title": "テスト案件",
                "description": "テスト用の案件です",
                "decedent_name": "山田太郎",
                "death_date": "令和5年6月15日",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "テスト案件"
        assert data["decedent_name"] == "山田太郎"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    def test_create_case_invalid_death_date(self) -> None:
        """不正な死亡日でCase作成エラー"""
        response = client.post(
            "/api/v1/cases/",
            json={
                "title": "テスト案件",
                "description": "テスト用の案件です",
                "decedent_name": "山田太郎",
                "death_date": "invalid-date",
            },
        )
        assert response.status_code == 400
        assert "死亡日の形式が不正" in response.json()["detail"]

    def test_list_cases(self) -> None:
        """Case一覧取得のテスト"""
        response = client.get("/api/v1/cases/")
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "total" in data
        assert isinstance(data["cases"], list)

    def test_get_case(self) -> None:
        """Case詳細取得のテスト"""
        # まずCase作成
        create_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "詳細取得テスト",
                "description": "詳細取得用",
                "decedent_name": "田中花子",
                "death_date": "2023-10-03",
            },
        )
        assert create_response.status_code == 201
        case_id = create_response.json()["id"]

        # Case詳細取得
        response = client.get(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_id
        assert data["title"] == "詳細取得テスト"

    def test_get_case_not_found(self) -> None:
        """存在しないCase取得でエラー"""
        response = client.get("/api/v1/cases/nonexistent-id")
        assert response.status_code == 404
        assert "案件が見つかりません" in response.json()["detail"]

    def test_update_case(self) -> None:
        """Case更新のテスト"""
        # まずCase作成
        create_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "更新テスト",
                "description": "更新前",
                "decedent_name": "佐藤一郎",
                "death_date": "H31.4.30",
            },
        )
        assert create_response.status_code == 201
        case_id = create_response.json()["id"]

        # Case更新
        response = client.patch(
            f"/api/v1/cases/{case_id}",
            json={
                "title": "更新後のタイトル",
                "description": "更新後の説明",
                "status": "in_progress",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新後のタイトル"
        assert data["description"] == "更新後の説明"
        assert data["status"] == "in_progress"

    def test_delete_case(self) -> None:
        """Case削除のテスト"""
        # まずCase作成
        create_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "削除テスト",
                "description": "削除用",
                "decedent_name": "鈴木二郎",
                "death_date": "S64.1.7",
            },
        )
        assert create_response.status_code == 201
        case_id = create_response.json()["id"]

        # Case削除
        response = client.delete(f"/api/v1/cases/{case_id}")
        assert response.status_code == 204

        # 削除確認
        get_response = client.get(f"/api/v1/cases/{case_id}")
        assert get_response.status_code == 404

    def test_create_person(self) -> None:
        """Person追加のテスト"""
        # まずCase作成
        create_case_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "Person追加テスト",
                "description": "Person追加用",
                "decedent_name": "高橋三郎",
                "death_date": "R5.10.3",
            },
        )
        assert create_case_response.status_code == 201
        case_id = create_case_response.json()["id"]

        # Person追加
        response = client.post(
            f"/api/v1/cases/{case_id}/persons",
            json={
                "case_id": case_id,
                "name": "高橋花子",
                "is_alive": True,
                "is_decedent": False,
                "gender": "女性",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "高橋花子"
        assert data["is_alive"] is True
        assert data["is_decedent"] is False
        assert "id" in data

    def test_list_persons(self) -> None:
        """Person一覧取得のテスト"""
        # まずCase作成
        create_case_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "Person一覧テスト",
                "description": "Person一覧用",
                "decedent_name": "渡辺五郎",
                "death_date": "2023-01-01",
            },
        )
        assert create_case_response.status_code == 201
        case_id = create_case_response.json()["id"]

        # Person一覧取得
        response = client.get(f"/api/v1/cases/{case_id}/persons")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 被相続人が自動作成されているはず
        assert len(data) >= 1
        # 被相続人を確認
        decedent = next((p for p in data if p["is_decedent"]), None)
        assert decedent is not None
        assert decedent["name"] == "渡辺五郎"

    def test_create_relationship(self) -> None:
        """Relationship追加のテスト"""
        # まずCase作成
        create_case_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "Relationship追加テスト",
                "description": "Relationship追加用",
                "decedent_name": "伊藤六郎",
                "death_date": "R5.5.1",
            },
        )
        assert create_case_response.status_code == 201
        case_id = create_case_response.json()["id"]

        # Person追加
        person1_response = client.post(
            f"/api/v1/cases/{case_id}/persons",
            json={
                "case_id": case_id,
                "name": "伊藤七子",
                "is_alive": True,
                "is_decedent": False,
            },
        )
        person1_id = person1_response.json()["id"]

        # 被相続人のIDを取得
        persons_response = client.get(f"/api/v1/cases/{case_id}/persons")
        decedent = next((p for p in persons_response.json() if p["is_decedent"]), None)
        assert decedent is not None
        decedent_id = decedent["id"]

        # Relationship追加（子の関係）
        response = client.post(
            f"/api/v1/cases/{case_id}/relationships",
            json={
                "case_id": case_id,
                "from_person_id": person1_id,
                "to_person_id": decedent_id,
                "relationship_type": "CHILD_OF",
                "properties": {"is_biological": True},
            },
        )
        assert response.status_code == 201
        assert "message" in response.json()
