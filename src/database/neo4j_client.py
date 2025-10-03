"""Neo4jクライアント

Neo4jデータベースへの接続と操作を管理するクライアント。
"""
from typing import Any, Dict, List, Optional, Generator
from contextlib import contextmanager
import logging

from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from .base import DatabaseClient
from ..utils.exceptions import DatabaseException
from ..utils.config import Neo4jSettings


class Neo4jClient(DatabaseClient):
    """
    Neo4jデータベースクライアント

    接続管理、トランザクション管理、クエリ実行を提供する。
    """

    def __init__(self, settings: Optional[Neo4jSettings] = None) -> None:
        """
        初期化

        Args:
            settings: Neo4j接続設定（Noneの場合は環境変数から取得）
        """
        self.logger = logging.getLogger(__name__)

        if settings is None:
            try:
                settings = Neo4jSettings()  # type: ignore[call-arg]
            except Exception:
                # テスト環境等でパスワードが設定されていない場合のフォールバック
                raise DatabaseException("Neo4j設定の初期化に失敗しました。NEO4J_PASSWORD環境変数が設定されているか確認してください。")

        self.uri = settings.uri
        self.user = settings.user
        self.password = settings.password
        self.database = settings.database

        self._driver: Optional[Driver] = None
        self._session: Optional[Session] = None
        self._transaction: Optional[Transaction] = None

        self.logger.info(f"Neo4jClient initialized for {self.uri}")

    def connect(self) -> None:
        """
        データベースに接続

        Raises:
            DatabaseException: 接続に失敗した場合
        """
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                encrypted=False  # ローカル環境のため暗号化なし
            )

            # 接続テスト
            self._driver.verify_connectivity()

            self.logger.info("Successfully connected to Neo4j")

        except AuthError as e:
            self.logger.error(f"Authentication failed: {e}")
            raise DatabaseException(f"Neo4j認証に失敗しました: {str(e)}")
        except ServiceUnavailable as e:
            self.logger.error(f"Neo4j service unavailable: {e}")
            raise DatabaseException(f"Neo4jサービスに接続できません: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}", exc_info=True)
            raise DatabaseException(f"Neo4j接続エラー: {str(e)}")

    def disconnect(self) -> None:
        """
        データベースから切断
        """
        try:
            # トランザクションをロールバック
            if self._transaction is not None:
                self._transaction.rollback()
                self._transaction = None

            # セッションを閉じる
            if self._session is not None:
                self._session.close()
                self._session = None

            # ドライバーを閉じる
            if self._driver is not None:
                self._driver.close()
                self._driver = None

            self.logger.info("Disconnected from Neo4j")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}", exc_info=True)

    def is_connected(self) -> bool:
        """
        接続状態を確認

        Returns:
            接続中の場合True
        """
        if self._driver is None:
            return False

        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        """
        ヘルスチェック

        Returns:
            データベースが正常に動作している場合True
        """
        if self._driver is None:
            return False

        try:
            with self._driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as health")
                record = result.single()
                if record is None:
                    return False
                return bool(record["health"] == 1)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def begin_transaction(self) -> Transaction:
        """
        トランザクションを開始

        Returns:
            トランザクションオブジェクト

        Raises:
            DatabaseException: トランザクション開始に失敗した場合
        """
        if self._driver is None:
            raise DatabaseException("データベースに接続されていません")

        try:
            if self._session is None:
                self._session = self._driver.session(database=self.database)

            self._transaction = self._session.begin_transaction()
            self.logger.debug("Transaction started")
            return self._transaction

        except Exception as e:
            self.logger.error(f"Failed to begin transaction: {e}", exc_info=True)
            raise DatabaseException(f"トランザクション開始エラー: {str(e)}")

    def commit_transaction(self, transaction: Any) -> None:
        """
        トランザクションをコミット

        Args:
            transaction: トランザクションオブジェクト

        Raises:
            DatabaseException: コミットに失敗した場合
        """
        if transaction is None:
            raise DatabaseException("トランザクションがNullです")

        try:
            transaction.commit()
            if self._transaction == transaction:
                self._transaction = None
            self.logger.debug("Transaction committed")

        except Exception as e:
            self.logger.error(f"Failed to commit transaction: {e}", exc_info=True)
            raise DatabaseException(f"トランザクションコミットエラー: {str(e)}")

    def rollback_transaction(self, transaction: Any) -> None:
        """
        トランザクションをロールバック

        Args:
            transaction: トランザクションオブジェクト

        Raises:
            DatabaseException: ロールバックに失敗した場合
        """
        if transaction is None:
            raise DatabaseException("トランザクションがNullです")

        try:
            transaction.rollback()
            if self._transaction == transaction:
                self._transaction = None
            self.logger.debug("Transaction rolled back")

        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {e}", exc_info=True)
            raise DatabaseException(f"トランザクションロールバックエラー: {str(e)}")

    def commit(self) -> None:
        """
        現在のトランザクションをコミット（内部メソッド）

        Raises:
            DatabaseException: コミットに失敗した場合
        """
        if self._transaction is None:
            raise DatabaseException("アクティブなトランザクションがありません")
        self.commit_transaction(self._transaction)

    def rollback(self) -> None:
        """
        現在のトランザクションをロールバック（内部メソッド）

        Raises:
            DatabaseException: ロールバックに失敗した場合
        """
        if self._transaction is None:
            raise DatabaseException("アクティブなトランザクションがありません")
        self.rollback_transaction(self._transaction)

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Cypherクエリを実行（基底クラスメソッド）

        Args:
            query: Cypherクエリ文字列
            parameters: クエリパラメータ

        Returns:
            クエリ結果のリスト

        Raises:
            DatabaseException: クエリ実行に失敗した場合
        """
        if self._driver is None:
            raise DatabaseException("データベースに接続されていません")

        try:
            # トランザクション内の場合
            if self._transaction is not None:
                result = self._transaction.run(query, parameters or {})
                return [dict(record) for record in result]

            # トランザクション外の場合
            with self._driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]

        except Neo4jError as e:
            self.logger.error(f"Neo4j query error: {e}", exc_info=True)
            raise DatabaseException(f"クエリ実行エラー: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during query execution: {e}", exc_info=True)
            raise DatabaseException(f"予期しないエラー: {str(e)}")

    def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Cypherクエリを実行（互換性メソッド）

        Args:
            query: Cypherクエリ文字列
            parameters: クエリパラメータ

        Returns:
            クエリ結果のリスト

        Raises:
            DatabaseException: クエリ実行に失敗した場合
        """
        return self.execute_query(query, parameters)

    @contextmanager
    def transaction(self) -> Generator["Neo4jClient", None, None]:
        """
        トランザクションコンテキストマネージャー

        Usage:
            with client.transaction():
                client.execute("CREATE (n:Person {name: $name})", {"name": "太郎"})

        Yields:
            Neo4jClient: 自身のインスタンス
        """
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    def clear_database(self) -> None:
        """
        データベースの全データを削除（テスト用）

        Warning:
            本番環境では使用しないこと
        """
        self.logger.warning("Clearing all data from database")
        self.execute("MATCH (n) DETACH DELETE n")

    def create_constraints(self) -> None:
        """
        制約とインデックスを作成
        """
        constraints = [
            # Personノードのname属性にユニーク制約
            "CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",

            # Personノードのnameにインデックス
            "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)",

            # is_decedentフラグにインデックス
            "CREATE INDEX person_decedent_index IF NOT EXISTS FOR (p:Person) ON (p.is_decedent)",

            # is_aliveフラグにインデックス
            "CREATE INDEX person_alive_index IF NOT EXISTS FOR (p:Person) ON (p.is_alive)",
        ]

        for constraint in constraints:
            try:
                self.execute(constraint)
                self.logger.debug(f"Constraint/Index created: {constraint[:50]}...")
            except Exception as e:
                # 制約が既に存在する場合は無視
                self.logger.debug(f"Constraint/Index already exists or failed: {e}")

    def __enter__(self) -> "Neo4jClient":
        """コンテキストマネージャーのエントリー"""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャーのイグジット"""
        self.disconnect()
