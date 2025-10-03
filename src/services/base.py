"""サービス層の基底クラス"""
from abc import ABC
from typing import Any, Generic, TypeVar

from src.utils.logger import get_logger


T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """サービスの基底クラス"""

    def __init__(self) -> None:
        """サービスを初期化"""
        self.logger = get_logger(self.__class__.__name__)

    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """
        操作をログに記録

        Args:
            operation: 操作名
            **kwargs: ログに含める追加情報
        """
        self.logger.info(f"{operation}: {kwargs}")

    def log_error(self, error: Exception, context: str = "") -> None:
        """
        エラーをログに記録

        Args:
            error: 発生した例外
            context: エラーのコンテキスト情報
        """
        error_msg = f"Error in {context}: {error}" if context else f"Error: {error}"
        self.logger.error(error_msg, exc_info=True)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """
        情報をログに記録

        Args:
            message: 情報メッセージ
            **kwargs: ログに含める追加情報
        """
        self.logger.info(f"{message}: {kwargs}" if kwargs else message)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """
        警告をログに記録

        Args:
            message: 警告メッセージ
            **kwargs: ログに含める追加情報
        """
        self.logger.warning(f"{message}: {kwargs}" if kwargs else message)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """
        デバッグ情報をログに記録

        Args:
            message: デバッグメッセージ
            **kwargs: ログに含める追加情報
        """
        self.logger.debug(f"{message}: {kwargs}" if kwargs else message)
