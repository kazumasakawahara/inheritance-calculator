"""ロギング機能のテスト"""
import pytest
import logging
from pathlib import Path
from src.utils.logger import setup_logger, get_logger, _logger_cache
from src.utils.exceptions import LoggingError


class TestSetupLogger:
    """ロガーセットアップのテスト"""

    def test_logger_creation(self, tmp_path):
        """ロガーの作成"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        assert logger.name == "test_logger"
        assert len(logger.handlers) == 2  # console + file
        assert log_file.exists()

    def test_logger_level_setting(self, tmp_path):
        """ログレベルの設定"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger_level", log_file=log_file, level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_logger_handlers_clear(self, tmp_path):
        """ハンドラのクリア（再設定）"""
        log_file = tmp_path / "test.log"
        logger1 = setup_logger("test_logger_clear", log_file=log_file)
        initial_handlers = len(logger1.handlers)

        logger2 = setup_logger("test_logger_clear", log_file=log_file)
        assert len(logger2.handlers) == initial_handlers  # 増えない
        assert logger1 is logger2  # 同じロガーインスタンス

    def test_log_directory_auto_creation(self, tmp_path):
        """ログディレクトリの自動作成"""
        # 深いディレクトリ構造
        log_file = tmp_path / "deep" / "path" / "to" / "test.log"

        logger = setup_logger("test_logger_auto_dir", log_file=log_file)
        assert log_file.exists()
        assert log_file.parent.exists()

    def test_logger_writes_to_file(self, tmp_path):
        """ログファイルへの書き込み"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger_write", log_file=log_file)

        test_message = "Test log message"
        logger.info(test_message)

        # ログファイルの内容を確認
        log_content = log_file.read_text()
        assert test_message in log_content

    def test_logger_formatting(self, tmp_path):
        """ログフォーマットの検証"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger_format", log_file=log_file)

        logger.info("Test message")

        log_content = log_file.read_text()
        # フォーマットに含まれるべき要素
        assert "test_logger_format" in log_content  # ロガー名
        assert "INFO" in log_content  # ログレベル
        assert "Test message" in log_content  # メッセージ


class TestGetLogger:
    """ロガー取得のテスト"""

    def test_logger_caching(self):
        """ロガーのキャッシュ"""
        # キャッシュをクリア
        _logger_cache.clear()

        logger1 = get_logger("cached_logger")
        logger2 = get_logger("cached_logger")

        assert logger1 is logger2  # 同じインスタンス
        assert "cached_logger" in _logger_cache

    def test_multiple_loggers(self):
        """複数ロガーの管理"""
        _logger_cache.clear()

        logger_a = get_logger("logger_a")
        logger_b = get_logger("logger_b")

        assert logger_a is not logger_b
        assert logger_a.name == "logger_a"
        assert logger_b.name == "logger_b"
        assert len(_logger_cache) == 2

    def test_logger_independence(self, tmp_path):
        """ロガーの独立性"""
        _logger_cache.clear()

        log_file_a = tmp_path / "logger_a.log"
        log_file_b = tmp_path / "logger_b.log"

        logger_a = setup_logger("independent_a", log_file=log_file_a)
        logger_b = setup_logger("independent_b", log_file=log_file_b)

        logger_a.info("Message A")
        logger_b.info("Message B")

        # 各ログファイルに正しいメッセージが書き込まれているか
        content_a = log_file_a.read_text()
        content_b = log_file_b.read_text()

        assert "Message A" in content_a
        assert "Message B" not in content_a

        assert "Message B" in content_b
        assert "Message A" not in content_b


class TestLoggerErrorHandling:
    """ロガーエラーハンドリングのテスト"""

    def test_invalid_log_level(self, tmp_path):
        """不正なログレベルの処理（フォールバックで対応）"""
        log_file = tmp_path / "test.log"

        # 無効なレベルはINFOにフォールバックされる
        logger = setup_logger("test_invalid_level", log_file=log_file, level="INVALID_LEVEL")
        assert logger.level == logging.INFO  # デフォルトのINFOレベルにフォールバック
