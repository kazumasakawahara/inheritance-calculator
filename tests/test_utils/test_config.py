"""設定管理のテスト"""
import pytest
from pydantic import ValidationError
from inheritance_calculator_core.utils.config import Neo4jSettings, OllamaSettings, LogSettings, Settings
from inheritance_calculator_core.utils.exceptions import ConfigurationError


class TestNeo4jSettings:
    """Neo4j設定のテスト"""

    def test_valid_uri(self):
        """正しいURIの検証"""
        valid_uris = [
            "bolt://localhost:7687",
            "neo4j://localhost:7687",
            "neo4j+s://localhost:7687",
            "neo4j+ssc://localhost:7687",
        ]
        for uri in valid_uris:
            settings = Neo4jSettings(uri=uri, password="test_pass_123")
            assert settings.uri == uri

    def test_invalid_uri(self):
        """不正なURIの検証"""
        with pytest.raises(ValidationError) as exc_info:
            Neo4jSettings(uri="http://localhost:7687", password="test_pass_123")
        assert "Invalid Neo4j URI scheme" in str(exc_info.value)

    def test_password_required(self, monkeypatch):
        """パスワード必須の検証"""
        # 環境変数のパスワードを削除
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        with pytest.raises(ValidationError):
            Neo4jSettings(uri="bolt://localhost:7687")

    def test_password_minimum_length(self):
        """パスワード最小長の検証"""
        with pytest.raises(ValidationError) as exc_info:
            Neo4jSettings(uri="bolt://localhost:7687", password="short")
        assert "at least 8 characters" in str(exc_info.value)

    def test_valid_password(self):
        """正しいパスワードの検証"""
        settings = Neo4jSettings(uri="bolt://localhost:7687", password="password123")
        assert settings.password == "password123"


class TestOllamaSettings:
    """Ollama設定のテスト"""

    def test_valid_host(self):
        """正しいホストURLの検証"""
        settings = OllamaSettings(host="http://localhost:11434")
        assert settings.host == "http://localhost:11434"

    def test_https_host(self):
        """HTTPSホストURLの検証"""
        settings = OllamaSettings(host="https://api.ollama.com")
        assert settings.host == "https://api.ollama.com"

    def test_invalid_host(self):
        """不正なホストURLの検証"""
        with pytest.raises(ValidationError) as exc_info:
            OllamaSettings(host="localhost:11434")
        assert "Invalid Ollama host URL" in str(exc_info.value)

    def test_timeout_validation_too_low(self):
        """タイムアウト値が低すぎる場合の検証"""
        with pytest.raises(ValidationError) as exc_info:
            OllamaSettings(timeout=5)
        assert "between 10 and 600" in str(exc_info.value)

    def test_timeout_validation_too_high(self):
        """タイムアウト値が高すぎる場合の検証"""
        with pytest.raises(ValidationError) as exc_info:
            OllamaSettings(timeout=700)
        assert "between 10 and 600" in str(exc_info.value)

    def test_valid_timeout(self):
        """正しいタイムアウト値の検証"""
        settings = OllamaSettings(timeout=120)
        assert settings.timeout == 120


class TestLogSettings:
    """ログ設定のテスト"""

    def test_valid_log_levels(self):
        """正しいログレベルの検証"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = LogSettings(level=level)
            assert settings.level == level

    def test_case_insensitive_log_level(self):
        """大文字小文字を問わないログレベル"""
        settings = LogSettings(level="info")
        assert settings.level == "INFO"

        settings = LogSettings(level="Debug")
        assert settings.level == "DEBUG"

    def test_invalid_log_level(self):
        """不正なログレベルの検証"""
        with pytest.raises(ValidationError) as exc_info:
            LogSettings(level="INVALID")
        assert "Invalid log level" in str(exc_info.value)


class TestSettings:
    """統合設定のテスト"""

    def test_settings_creation(self, mock_settings):
        """設定オブジェクトの作成"""
        assert mock_settings.neo4j.uri == "bolt://localhost:7687"
        assert mock_settings.neo4j.password == "test_password_123"

    def test_logs_dir_creation(self, mock_settings):
        """ログディレクトリの作成"""
        logs_dir = mock_settings.logs_dir

        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_output_dir_creation(self, mock_settings):
        """出力ディレクトリの作成"""
        output_dir = mock_settings.output_dir

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_project_root(self, mock_settings):
        """プロジェクトルートの取得"""
        root = mock_settings.project_root
        assert root.exists()
        assert root.is_dir()
