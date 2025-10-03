"""アプリケーション設定"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # FastAPI設定
    app_name: str = Field(default="inheritance-calculator-backend", description="アプリケーション名")
    app_version: str = Field(default="0.1.0", description="バージョン")
    app_env: str = Field(default="development", description="環境")
    debug: bool = Field(default=False, description="デバッグモード")

    # サーバー設定
    host: str = Field(default="0.0.0.0", description="ホスト")
    port: int = Field(default=8000, description="ポート")

    # CORS設定
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="許可するオリジン",
    )

    # Neo4j設定
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4jユーザー名")
    neo4j_password: str = Field(default="", description="Neo4jパスワード")
    neo4j_database: str = Field(default="neo4j", description="Neo4jデータベース名")

    # Ollama設定
    ollama_host: str = Field(default="http://localhost:11434", description="Ollamaホスト")
    ollama_model: str = Field(default="gpt-oss:20b", description="Ollamaモデル")
    ollama_timeout: int = Field(default=120, description="Ollamaタイムアウト(秒)")
    ollama_temperature: float = Field(default=0.7, description="Ollama温度パラメータ")

    # JWT設定
    secret_key: str = Field(default="your-secret-key", description="秘密鍵")
    algorithm: str = Field(default="HS256", description="アルゴリズム")
    access_token_expire_minutes: int = Field(default=30, description="アクセストークン有効期限(分)")

    # ログ設定
    log_level: str = Field(default="INFO", description="ログレベル")
    log_file: str = Field(default="logs/backend.log", description="ログファイル")


settings = Settings()
