"""API utilsエンドポイントのテスト"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestEraConversionAPI:
    """元号変換APIのテスト"""

    def test_root_endpoint(self) -> None:
        """ルートエンドポイントのテスト"""
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

    def test_convert_era_to_western_reiwa(self) -> None:
        """令和を西暦に変換"""
        response = client.post(
            "/api/v1/utils/convert-era-to-western",
            json={"date_str": "令和5年10月3日", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "令和5年10月3日"
        assert data["converted"] == "2023-10-03"
        assert data["era_name"] == "令和"

    def test_convert_era_to_western_short_format(self) -> None:
        """R5.10.3形式を西暦に変換"""
        response = client.post(
            "/api/v1/utils/convert-era-to-western",
            json={"date_str": "R5.10.3", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "R5.10.3"
        assert data["converted"] == "2023-10-03"
        assert data["era_name"] == "令和"

    def test_convert_western_to_era_long(self) -> None:
        """西暦を元号(long)に変換"""
        response = client.post(
            "/api/v1/utils/convert-western-to-era",
            json={"date_str": "2023-10-03", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "2023-10-03"
        assert data["converted"] == "令和5年10月3日"
        assert data["era_name"] == "令和"

    def test_convert_western_to_era_short(self) -> None:
        """西暦を元号(short)に変換"""
        response = client.post(
            "/api/v1/utils/convert-western-to-era",
            json={"date_str": "2023-10-03", "format_type": "short"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "2023-10-03"
        assert data["converted"] == "R5.10.3"
        assert data["era_name"] == "令和"

    def test_convert_western_to_era_slash(self) -> None:
        """西暦を元号(slash)に変換"""
        response = client.post(
            "/api/v1/utils/convert-western-to-era",
            json={"date_str": "2023-10-03", "format_type": "slash"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "2023-10-03"
        assert data["converted"] == "R5/10/3"
        assert data["era_name"] == "令和"

    def test_detect_and_convert_era_input(self) -> None:
        """自動判定: 元号入力 → 西暦出力"""
        response = client.post(
            "/api/v1/utils/detect-and-convert",
            json={"date_str": "令和5年10月3日", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["converted"] == "2023-10-03"

    def test_detect_and_convert_western_input(self) -> None:
        """自動判定: 西暦入力 → 元号出力"""
        response = client.post(
            "/api/v1/utils/detect-and-convert",
            json={"date_str": "2023-10-03", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["converted"] == "令和5年10月3日"

    def test_invalid_date_format(self) -> None:
        """無効な日付形式でエラー"""
        response = client.post(
            "/api/v1/utils/convert-era-to-western",
            json={"date_str": "invalid-date", "format_type": "long"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_heisei_conversion(self) -> None:
        """平成の変換テスト"""
        response = client.post(
            "/api/v1/utils/convert-era-to-western",
            json={"date_str": "平成31年4月30日", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["converted"] == "2019-04-30"
        assert data["era_name"] == "平成"

    def test_showa_conversion(self) -> None:
        """昭和の変換テスト"""
        response = client.post(
            "/api/v1/utils/convert-era-to-western",
            json={"date_str": "昭和64年1月7日", "format_type": "long"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["converted"] == "1989-01-07"
        assert data["era_name"] == "昭和"
