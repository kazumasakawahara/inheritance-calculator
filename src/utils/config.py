"""
アプリケーション設定管理モジュール

環境変数から設定を読み込み、アプリケーション全体で使用する設定を提供します。
"""

import os
import warnings
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import Any

from .exceptions import ConfigurationError

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent

# .envファイルを読み込み
try:
    load_dotenv(PROJECT_ROOT / ".env")
except Exception as e:
    # .envファイルが無くても動作するが警告を出す
    warnings.warn(
        f".env file could not be loaded: {e}. "
        "Using environment variables or defaults.",
        UserWarning
    )


class Neo4jSettings(BaseSettings):
    """Neo4jデータベース接続設定"""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j接続URI")
    user: str = Field(default="neo4j", description="Neo4jユーザー名")
    password: str = Field(..., description="Neo4jパスワード（必須）")
    database: str = Field(default="neo4j", description="Neo4jデータベース名")
    auto_create_constraints: bool = Field(
        default=True, description="制約を自動作成するか"
    )
    auto_create_indexes: bool = Field(
        default=True, description="インデックスを自動作成するか"
    )

    @field_validator('uri')
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """URIスキームの検証"""
        if not v.startswith(('bolt://', 'neo4j://', 'neo4j+s://', 'neo4j+ssc://')):
            raise ValueError(
                f"Invalid Neo4j URI scheme: {v}. "
                "Must start with bolt://, neo4j://, neo4j+s://, or neo4j+ssc://"
            )
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """パスワード強度の検証"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    class Config:
        env_prefix = "NEO4J_"


class OllamaSettings(BaseSettings):
    """Ollama設定"""

    host: str = Field(default="http://localhost:11434", description="OllamaホストURL")
    model: str = Field(default="gpt-oss:20b", description="使用するモデル名")
    timeout: int = Field(default=120, description="タイムアウト秒数")
    temperature: float = Field(default=0.7, description="生成時の温度パラメータ")

    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """ホストURLの検証"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid Ollama host URL: {v}. Must start with http:// or https://")
        return v

    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """タイムアウト値の検証"""
        if v < 10 or v > 600:
            raise ValueError("Timeout must be between 10 and 600 seconds")
        return v

    class Config:
        env_prefix = "OLLAMA_"


class LogSettings(BaseSettings):
    """ログ設定"""

    level: str = Field(default="INFO", description="ログレベル")
    file: str = Field(default="logs/inheritance.log", description="ログファイルパス")
    max_bytes: int = Field(default=10485760, description="ログファイル最大サイズ")
    backup_count: int = Field(default=5, description="バックアップファイル数")

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """ログレベルの検証"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    class Config:
        env_prefix = "LOG_"


class AppSettings(BaseSettings):
    """アプリケーション設定"""

    env: Literal["development", "production", "test"] = Field(
        default="development", description="実行環境"
    )
    debug: bool = Field(default=False, description="デバッグモード")
    name: str = Field(default="inheritance-calculator", description="アプリケーション名")

    class Config:
        env_prefix = "APP_"


class AgentSettings(BaseSettings):
    """エージェント設定"""

    max_retries: int = Field(default=3, description="最大リトライ回数")
    timeout: int = Field(default=60, description="タイムアウト秒数")

    class Config:
        env_prefix = "AGENT_"


class OutputSettings(BaseSettings):
    """出力設定"""

    dir: str = Field(default="output", description="出力ディレクトリ")
    format: Literal["json", "yaml", "csv"] = Field(
        default="json", description="デフォルト出力形式"
    )
    enable_rich: bool = Field(default=True, description="Rich出力を有効にするか")

    class Config:
        env_prefix = "OUTPUT_"


class Settings(BaseSettings):
    """統合設定クラス"""

    neo4j: Neo4jSettings = Field(default=None)  # type: ignore
    ollama: OllamaSettings = Field(default=None)  # type: ignore
    log: LogSettings = Field(default=None)  # type: ignore
    app: AppSettings = Field(default=None)  # type: ignore
    agent: AgentSettings = Field(default=None)  # type: ignore
    output: OutputSettings = Field(default=None)  # type: ignore

    @model_validator(mode='before')
    @classmethod
    def create_nested_settings(cls, data: Any) -> Any:
        """ネストされた設定を自動生成"""
        if isinstance(data, dict):
            if 'neo4j' not in data or data['neo4j'] is None:
                data['neo4j'] = Neo4jSettings()  # type: ignore
            if 'ollama' not in data or data['ollama'] is None:
                data['ollama'] = OllamaSettings()  # type: ignore
            if 'log' not in data or data['log'] is None:
                data['log'] = LogSettings()  # type: ignore
            if 'app' not in data or data['app'] is None:
                data['app'] = AppSettings()  # type: ignore
            if 'agent' not in data or data['agent'] is None:
                data['agent'] = AgentSettings()  # type: ignore
            if 'output' not in data or data['output'] is None:
                data['output'] = OutputSettings()  # type: ignore
        return data

    @property
    def project_root(self) -> Path:
        """プロジェクトルートディレクトリを取得"""
        return PROJECT_ROOT

    @property
    def logs_dir(self) -> Path:
        """ログディレクトリを取得"""
        logs_dir = PROJECT_ROOT / "logs"
        try:
            logs_dir.mkdir(exist_ok=True)
        except OSError as e:
            raise ConfigurationError(
                f"Failed to create logs directory: {logs_dir}"
            ) from e
        return logs_dir

    @property
    def output_dir(self) -> Path:
        """出力ディレクトリを取得"""
        output_dir = PROJECT_ROOT / self.output.dir
        try:
            output_dir.mkdir(exist_ok=True)
        except OSError as e:
            raise ConfigurationError(
                f"Failed to create output directory: {output_dir}"
            ) from e
        return output_dir


# シングルトンインスタンス
# 注: 実行時にはNEO4J_PASSWORD環境変数が必須
try:
    settings = Settings()
except Exception:
    # テスト環境やインポート時のエラーを回避
    # 実際の使用時には環境変数が設定されている必要がある
    settings = None  # type: ignore
