"""Phase 6 統合テスト"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPhase6Integration:
    """Phase 6の統合テスト"""

    def test_api_root(self) -> None:
        """APIルートエンドポイントのテスト"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_check(self) -> None:
        """ヘルスチェックのテスト"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_era_conversion_endpoints(self) -> None:
        """元号変換エンドポイントのテスト"""
        # 元号→西暦
        response = client.post(
            "/api/v1/utils/convert-era-to-western", json={"date_str": "令和5年10月3日", "format_type": "long"}
        )
        assert response.status_code == 200
        assert response.json()["converted"] == "2023-10-03"

        # 西暦→元号
        response = client.post(
            "/api/v1/utils/convert-western-to-era", json={"date_str": "2023-10-03", "format_type": "long"}
        )
        assert response.status_code == 200
        assert response.json()["converted"] == "令和5年10月3日"

    def test_swagger_docs(self) -> None:
        """Swagger UIドキュメントのテスト"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self) -> None:
        """OpenAPI JSONスキーマのテスト"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # エンドポイントの存在確認
        paths = data["paths"]
        assert "/api/v1/cases/" in paths
        assert "/api/v1/utils/convert-era-to-western" in paths
        assert "/api/v1/calculation/calculate" in paths
        # WebSocketはOpenAPIスキーマに含まれないため、HTTPエンドポイントで確認
        assert "/api/v1/chat/test" in paths

    def test_chat_test_endpoint(self) -> None:
        """Chat APIテストエンドポイントのテスト"""
        response = client.get("/api/v1/chat/test")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Chat API is working" in data["message"]


@pytest.mark.skipif(
    True, reason="Neo4j integration tests require running Neo4j instance. Skip for now."  # CI環境用
)
class TestPhase6WithNeo4j:
    """Neo4jを使用するPhase 6の統合テスト"""

    def test_full_workflow(self) -> None:
        """完全なワークフローのテスト（Case作成→Person追加→計算）"""
        # 1. Case作成
        create_case_response = client.post(
            "/api/v1/cases/",
            json={
                "title": "統合テスト案件",
                "description": "ワークフロー検証用",
                "decedent_name": "統合テスト太郎",
                "death_date": "令和5年10月3日",
            },
        )
        assert create_case_response.status_code == 201
        case_id = create_case_response.json()["id"]

        # 2. 配偶者追加
        spouse_response = client.post(
            f"/api/v1/cases/{case_id}/persons",
            json={
                "case_id": case_id,
                "name": "統合テスト花子",
                "is_alive": True,
                "is_decedent": False,
                "gender": "女性",
            },
        )
        assert spouse_response.status_code == 201

        # 3. 子追加
        child_response = client.post(
            f"/api/v1/cases/{case_id}/persons",
            json={
                "case_id": case_id,
                "name": "統合テスト一郎",
                "is_alive": True,
                "is_decedent": False,
                "gender": "男性",
            },
        )
        assert child_response.status_code == 201

        # 4. Person一覧取得
        persons_response = client.get(f"/api/v1/cases/{case_id}/persons")
        assert persons_response.status_code == 200
        persons = persons_response.json()
        assert len(persons) == 3  # 被相続人 + 配偶者 + 子

        # 5. 相続計算実行
        calc_response = client.get(f"/api/v1/calculation/cases/{case_id}/calculate")
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        assert "heirs" in calc_data
        assert "total_heirs" in calc_data
        assert "calculation_basis" in calc_data

        # 6. Case削除
        delete_response = client.delete(f"/api/v1/cases/{case_id}")
        assert delete_response.status_code == 204


class TestPhase6Documentation:
    """Phase 6のドキュメント検証テスト"""

    def test_all_endpoints_have_tags(self) -> None:
        """全エンドポイントがタグを持つことを確認"""
        response = client.get("/openapi.json")
        data = response.json()

        for path, methods in data["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "patch", "delete", "put"]:
                    assert "tags" in details, f"{method.upper()} {path} にタグがありません"
                    assert len(details["tags"]) > 0, f"{method.upper()} {path} のタグが空です"

    def test_all_endpoints_have_summary(self) -> None:
        """全エンドポイントがsummaryを持つことを確認"""
        response = client.get("/openapi.json")
        data = response.json()

        for path, methods in data["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "patch", "delete", "put"]:
                    assert "summary" in details, f"{method.upper()} {path} にsummaryがありません"

    def test_error_responses_defined(self) -> None:
        """エラーレスポンスが定義されていることを確認"""
        response = client.get("/openapi.json")
        data = response.json()

        endpoints_requiring_error_responses = [
            "/api/v1/cases/{case_id}",
            "/api/v1/cases/{case_id}/persons",
            "/api/v1/calculation/calculate",
        ]

        for path in endpoints_requiring_error_responses:
            if path in data["paths"]:
                for method, details in data["paths"][path].items():
                    if method in ["get", "post", "patch", "delete"]:
                        assert "responses" in details, f"{method.upper()} {path} にresponsesがありません"
                        # 400または404エラーレスポンスが定義されているか
                        responses = details["responses"]
                        has_error_response = any(code in ["400", "404", "500"] for code in responses.keys())
                        assert has_error_response, f"{method.upper()} {path} にエラーレスポンスがありません"
