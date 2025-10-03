"""カスタム例外クラス"""


class InheritanceCalculatorError(Exception):
    """基底例外クラス"""
    pass


class ConfigurationError(InheritanceCalculatorError):
    """設定関連のエラー"""
    pass


class DatabaseConnectionError(InheritanceCalculatorError):
    """データベース接続エラー"""
    pass


class ValidationError(InheritanceCalculatorError):
    """バリデーションエラー"""
    pass


class LoggingError(InheritanceCalculatorError):
    """ロギング関連のエラー"""
    pass


class ServiceException(InheritanceCalculatorError):
    """サービス層のエラー"""
    pass


class DatabaseException(InheritanceCalculatorError):
    """データベース操作のエラー

    Neo4j操作、クエリ実行、トランザクション処理などで
    発生するデータベース関連のエラー。
    """
    pass
