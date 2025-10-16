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


class RenunciationConflictError(ValidationError):
    """再転相続における相続放棄の制約違反エラー

    判例（最高裁昭和63年6月21日判決）により、再転相続において
    第2次相続（相続人の相続）を放棄した者は、第1次相続（被相続人の相続）
    のみを承認することはできない。

    この制約に違反した場合に発生する。
    """
    pass
