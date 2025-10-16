"""データベーステスト用の共通フィクスチャとモック"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from typing import Any, Dict, List, Optional

from src.database.neo4j_client import Neo4jClient
from src.database.repositories import PersonRepository


class MockNeo4jDriver:
    """Neo4jドライバーのモック"""

    def __init__(self):
        self.connected = True
        self.sessions = []
        # 全セッションで共有するデータストア
        self.shared_data: Dict[str, Any] = {}

    def verify_connectivity(self):
        """接続確認（モック）"""
        if not self.connected:
            raise Exception("Not connected")

    def session(self, database: Optional[str] = None):
        """セッション作成（モック）"""
        session = MockNeo4jSession(self.shared_data)
        self.sessions.append(session)
        return session

    def close(self):
        """ドライバーを閉じる"""
        self.connected = False


class MockNeo4jSession:
    """Neo4jセッションのモック"""

    def __init__(self, shared_data: Dict[str, Any]):
        self.closed = False
        self.transaction_active = False
        # 共有データストアへの参照
        self.data: Dict[str, Any] = shared_data
        self.current_transaction: Optional['MockTransaction'] = None

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """クエリ実行（モック）"""
        # 単純な健全性チェッククエリ
        if query == "RETURN 1 as health":
            return MockResult([{"health": 1}])

        # 単純な値返却クエリ
        if query == "RETURN 1 as value":
            return MockResult([{"value": 1}])

        # CREATE クエリ
        if "CREATE" in query and "Person" in query:
            params = parameters or {}
            name = params.get("name", "unknown")
            self.data[name] = params
            return MockResult([])

        # MATCH クエリ
        if "MATCH" in query and "Person" in query:
            params = parameters or {}
            name = params.get("name")
            if name and name in self.data:
                return MockResult([{"p": self.data[name]}])
            return MockResult([])

        # DETACH DELETE クエリ（データベースクリア）
        if "DETACH DELETE" in query:
            self.data.clear()
            return MockResult([])

        # 制約作成クエリ
        if "CREATE CONSTRAINT" in query or "CREATE INDEX" in query:
            return MockResult([])

        # デフォルトは空の結果
        return MockResult([])

    def begin_transaction(self):
        """トランザクション開始（モック）"""
        self.transaction_active = True
        self.current_transaction = MockTransaction(self)
        return self.current_transaction

    def close(self):
        """セッションを閉じる"""
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MockTransaction:
    """Neo4jトランザクションのモック"""

    def __init__(self, session: MockNeo4jSession):
        self.session = session
        self.committed = False
        self.rolled_back = False
        self.pending_data: Dict[str, Any] = {}

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """トランザクション内でのクエリ実行（モック）"""
        # CREATE クエリの場合、pending_dataに保存
        if "CREATE" in query and "Person" in query:
            params = parameters or {}
            name = params.get("name", "unknown")
            self.pending_data[name] = params
            return MockResult([])

        # MATCH クエリの場合、pending_dataとcommittedデータの両方を確認
        if "MATCH" in query and "Person" in query:
            params = parameters or {}
            name = params.get("name")
            if name:
                # pending_dataを優先的に確認
                if name in self.pending_data:
                    return MockResult([{"p": self.pending_data[name]}])
                # session.dataも確認
                if name in self.session.data:
                    return MockResult([{"p": self.session.data[name]}])
            return MockResult([])

        # その他のクエリはsessionに委譲
        return self.session.run(query, parameters)

    def commit(self):
        """コミット"""
        self.committed = True
        # pending_dataをsession.dataにマージ
        self.session.data.update(self.pending_data)
        self.pending_data.clear()
        self.session.transaction_active = False
        self.session.current_transaction = None

    def rollback(self):
        """ロールバック"""
        self.rolled_back = True
        # pending_dataを破棄
        self.pending_data.clear()
        self.session.transaction_active = False
        self.session.current_transaction = None


class MockResult:
    """Neo4jクエリ結果のモック"""

    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records
        self._index = 0

    def single(self):
        """単一レコードの取得"""
        if self.records:
            return self.records[0]
        return None

    def __iter__(self):
        return iter(self.records)

    def __next__(self):
        if self._index < len(self.records):
            record = self.records[self._index]
            self._index += 1
            return record
        raise StopIteration


@pytest.fixture
def mock_neo4j_driver():
    """モックNeo4jドライバーのフィクスチャ"""
    return MockNeo4jDriver()


@pytest.fixture
def neo4j_client_mock(mock_neo4j_driver):
    """モックを使用したNeo4jクライアントのフィクスチャ"""
    with patch('src.database.neo4j_client.GraphDatabase.driver', return_value=mock_neo4j_driver):
        client = Neo4jClient()
        client.connect()
        yield client
        if client.is_connected():
            client.disconnect()


@pytest.fixture
def person_repo_mock(neo4j_client_mock):
    """モックを使用したPersonRepositoryのフィクスチャ"""
    return PersonRepository(neo4j_client_mock)
