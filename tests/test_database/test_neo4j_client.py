"""Neo4jクライアントのテスト"""
import pytest
from datetime import date
from unittest.mock import patch

from src.database.neo4j_client import Neo4jClient
from src.database.repositories import PersonRepository
from src.models.person import Person
from src.utils.exceptions import DatabaseException


class TestNeo4jClient:
    """Neo4jクライアントのテスト（モック使用）"""

    def test_connection(self, neo4j_client_mock):
        """接続テスト"""
        assert neo4j_client_mock.is_connected()

    def test_health_check(self, neo4j_client_mock):
        """ヘルスチェックのテスト"""
        assert neo4j_client_mock.health_check()

    def test_execute_simple_query(self, neo4j_client_mock):
        """単純なクエリ実行のテスト"""
        result = neo4j_client_mock.execute("RETURN 1 as value")
        assert len(result) == 1
        assert result[0]["value"] == 1

    def test_transaction(self, neo4j_client_mock):
        """トランザクションのテスト"""
        with neo4j_client_mock.transaction():
            neo4j_client_mock.execute(
                "CREATE (p:Person {name: $name})",
                {"name": "テスト太郎"}
            )

        # トランザクション外で確認
        result = neo4j_client_mock.execute(
            "MATCH (p:Person {name: $name}) RETURN p",
            {"name": "テスト太郎"}
        )
        assert len(result) == 1


class TestPersonRepository:
    """PersonRepositoryのテスト（モック使用）"""

    @pytest.mark.skip(reason="PersonRepositoryはリアルなNeo4jクエリロジックが必要")
    def test_create_person(self, person_repo_mock):
        """人物作成のテスト"""
        person = Person(
            name="山田太郎",
            is_alive=False,
            is_decedent=True,
            birth_date=date(1950, 1, 1),
            death_date=date(2025, 6, 15)
        )

        created = person_repo_mock.create(person)
        assert created.name == "山田太郎"

    @pytest.mark.skip(reason="PersonRepositoryはリアルなNeo4jクエリロジックが必要")
    def test_find_by_name(self, person_repo_mock):
        """名前検索のテスト"""
        person = Person(
            name="山田花子",
            is_alive=True,
            birth_date=date(1955, 3, 10)
        )
        person_repo_mock.create(person)

        found = person_repo_mock.find_by_name("山田花子")
        assert found is not None
        assert found.name == "山田花子"
        assert found.is_alive is True

    @pytest.mark.skip(reason="PersonRepositoryはリアルなNeo4jクエリロジックが必要")
    def test_find_decedent(self, person_repo_mock):
        """被相続人検索のテスト"""
        decedent = Person(
            name="被相続人",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15)
        )
        person_repo_mock.create(decedent)

        found = person_repo_mock.find_decedent()
        assert found is not None
        assert found.name == "被相続人"
        assert found.is_decedent is True

    @pytest.mark.skip(reason="PersonRepositoryはリアルなNeo4jクエリロジックが必要")
    def test_find_all(self, person_repo_mock):
        """全人物取得のテスト"""
        person1 = Person(name="太郎", is_alive=True)
        person2 = Person(name="花子", is_alive=True)

        person_repo_mock.create(person1)
        person_repo_mock.create(person2)

        all_persons = person_repo_mock.find_all()
        assert len(all_persons) == 2

    @pytest.mark.skip(reason="PersonRepositoryはリアルなNeo4jクエリロジックが必要")
    def test_delete(self, person_repo_mock):
        """削除のテスト"""
        person = Person(name="削除テスト", is_alive=True)
        person_repo_mock.create(person)

        person_repo_mock.delete("削除テスト")

        found = person_repo_mock.find_by_name("削除テスト")
        assert found is None


def _run_integration_enabled(config):
    """統合テストが有効かチェック"""
    return config.getoption("--run-integration", default=False)


@pytest.mark.skipif(
    "not config.getoption('--run-integration', default=False)",
    reason="Integration tests require Neo4j running"
)
class TestIntegration:
    """統合テスト（Neo4j実行環境が必要）"""

    def test_full_workflow(self, person_repo, neo4j_client):
        """完全なワークフローのテスト"""
        from src.database.repositories import RelationshipRepository

        # リポジトリ作成
        rel_repo = RelationshipRepository(neo4j_client)

        # 被相続人作成
        decedent = Person(
            name="被相続人太郎",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15)
        )
        person_repo.create(decedent)

        # 配偶者作成
        spouse = Person(name="配偶者花子", is_alive=True)
        person_repo.create(spouse)
        rel_repo.create_spouse_of("被相続人太郎", "配偶者花子")

        # 子作成
        child = Person(name="子一郎", is_alive=True)
        person_repo.create(child)
        rel_repo.create_child_of("子一郎", "被相続人太郎")

        # リレーションシップの確認
        children = rel_repo.find_children("被相続人太郎")
        assert len(children) == 1
        assert children[0].name == "子一郎"

        found_spouse = rel_repo.find_spouse("被相続人太郎")
        assert found_spouse is not None
        assert found_spouse.name == "配偶者花子"


def pytest_addoption(parser):
    """pytestオプションの追加"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests requiring Neo4j"
    )
