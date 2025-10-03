"""
ログ管理モジュール

アプリケーション全体で使用するロガーを提供します。
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import settings
from .exceptions import LoggingError


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    ロガーをセットアップします。

    Args:
        name: ロガー名
        log_file: ログファイルパス（Noneの場合は設定ファイルから取得）
        level: ログレベル（Noneの場合は設定ファイルから取得）

    Returns:
        設定済みのロガー

    Raises:
        LoggingError: ロガーのセットアップに失敗した場合
    """
    try:
        logger = logging.getLogger(name)

        # 既にハンドラが設定されている場合はクリア（再設定可能に）
        if logger.handlers:
            logger.handlers.clear()

        # ログレベルの設定
        try:
            log_level = level or (settings.log.level if settings else "INFO")
            logger.setLevel(getattr(logging, log_level.upper()))
        except AttributeError:
            # settingsがNoneの場合のフォールバック
            logger.setLevel(logging.INFO)
            log_level = "INFO"

        # フォーマッタの設定
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # コンソールハンドラの設定
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # ファイルハンドラの設定（settingsがある場合のみ）
        if log_file is None and settings:
            try:
                log_file = settings.logs_dir / settings.log.file.split("/")[-1]
            except AttributeError:
                # settingsの属性にアクセスできない場合はファイルハンドラをスキップ
                log_file = None

        if log_file is not None:
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise LoggingError(f"Failed to create log directory: {log_file.parent}") from e

            try:
                max_bytes = settings.log.max_bytes if settings else 10485760
                backup_count = settings.log.backup_count if settings else 5

                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.setLevel(getattr(logging, log_level.upper()))
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except OSError as e:
                raise LoggingError(f"Failed to create log file handler: {log_file}") from e

        # プロパゲーションを無効化（重複ログ防止）
        logger.propagate = False

        return logger

    except Exception as e:
        if isinstance(e, LoggingError):
            raise
        raise LoggingError(f"Failed to setup logger '{name}'") from e


# ロガーキャッシュ
_logger_cache: dict[str, logging.Logger] = {}

# デフォルトロガー
default_logger = setup_logger("inheritance_calculator")
_logger_cache["inheritance_calculator"] = default_logger


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得します（キャッシュ付き）。

    Args:
        name: ロガー名

    Returns:
        ロガー
    """
    if name not in _logger_cache:
        _logger_cache[name] = setup_logger(name)
    return _logger_cache[name]
