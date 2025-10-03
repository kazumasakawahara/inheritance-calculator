"""pytestの共通設定とフィクスチャ"""
import pytest
from pathlib import Path
import tempfile
import os

# テスト実行前に必須の環境変数を設定
os.environ.setdefault("NEO4J_PASSWORD", "test_password_123")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")


@pytest.fixture
def temp_env_file():
    """一時的な.envファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("NEO4J_URI=bolt://localhost:7687\n")
        f.write("NEO4J_USER=neo4j\n")
        f.write("NEO4J_PASSWORD=test_password_123\n")
        f.write("OLLAMA_HOST=http://localhost:11434\n")
        temp_path = f.name

    yield temp_path

    os.unlink(temp_path)


@pytest.fixture
def mock_settings(monkeypatch):
    """モック設定を提供"""
    monkeypatch.setenv("NEO4J_PASSWORD", "test_password_123")
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")

    # 設定モジュールを再インポートして環境変数を反映
    import importlib
    from src.utils import config
    importlib.reload(config)

    return config.Settings()
