"""リポジトリ層のユニットテスト

PersonRepository, RelationshipRepository, InheritanceRepositoryのテスト
モックを使用してNeo4jに依存しないユニットテストを実装
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch, call
from neo4j.exceptions import Neo4jError

from src.database.repositories import PersonRepository, RelationshipRepository, InheritanceRepository
from src.models.person import Person, Gender
from src.models.relationship import BloodType
from src.utils.exceptions import DatabaseException


class TestPersonRepository:
    """PersonRepositoryのユニットテスト"""

    @pytest.fixture
    def mock_client(self):
        """モッククライアントのフィクスチャ"""
        return Mock()

    @pytest.fixture
    def person_repo(self, mock_client):
        """PersonRepositoryのフィクスチャ"""
        return PersonRepository(mock_client)

    @pytest.fixture
    def sample_person(self):
        """サンプルPersonのフィクスチャ"""
        return Person(
            name="山田太郎",
            is_alive=False,
            is_decedent=True,
            birth_date=date(1950, 1, 1),
            death_date=date(2025, 6, 15),
            gender=Gender.MALE
        )

    def test_create_person_success(self, person_repo, mock_client, sample_person):
        """人物作成の成功テスト"""
        mock_client.execute.return_value = [{"p": {}}]

        result = person_repo.create(sample_person)

        assert result == sample_person
        assert mock_client.execute.call_count == 1
        # クエリパラメータの検証
        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["name"] == "山田太郎"
        assert params["is_alive"] is False
        assert params["is_decedent"] is True

    def test_create_person_without_optional_fields(self, person_repo, mock_client):
        """オプショナルフィールドなしの人物作成テスト"""
        person = Person(
            name="山田花子",
            is_alive=True,
            is_decedent=False
        )
        mock_client.execute.return_value = [{"p": {}}]

        result = person_repo.create(person)

        assert result.name == "山田花子"
        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["birth_date"] is None
        assert params["death_date"] is None

    def test_create_person_failure(self, person_repo, mock_client, sample_person):
        """人物作成の失敗テスト"""
        mock_client.execute.side_effect = Neo4jError("Database error")

        with pytest.raises(DatabaseException) as exc_info:
            person_repo.create(sample_person)

        assert "人物作成エラー" in str(exc_info.value)

    def test_find_by_name_found(self, person_repo, mock_client):
        """名前検索の成功テスト"""
        mock_node = {
            "name": "山田太郎",
            "is_alive": False,
            "is_decedent": True,
            "birth_date": Mock(year=1950, month=1, day=1),
            "death_date": Mock(year=2025, month=6, day=15),
            "gender": "male"
        }
        mock_client.execute.return_value = [{"p": mock_node}]

        result = person_repo.find_by_name("山田太郎")

        assert result is not None
        assert result.name == "山田太郎"
        assert result.is_alive is False
        assert result.is_decedent is True
        assert result.gender == Gender.MALE

    def test_find_by_name_not_found(self, person_repo, mock_client):
        """名前検索で見つからない場合のテスト"""
        mock_client.execute.return_value = []

        result = person_repo.find_by_name("存在しない人")

        assert result is None

    def test_find_by_name_database_error(self, person_repo, mock_client):
        """名前検索のデータベースエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Connection error")

        with pytest.raises(DatabaseException) as exc_info:
            person_repo.find_by_name("山田太郎")

        assert "人物検索エラー" in str(exc_info.value)

    def test_find_decedent_found(self, person_repo, mock_client):
        """被相続人検索の成功テスト"""
        mock_node = {
            "name": "被相続人",
            "is_alive": False,
            "is_decedent": True,
            "birth_date": None,
            "death_date": Mock(year=2025, month=6, day=15),
            "gender": None
        }
        mock_client.execute.return_value = [{"p": mock_node}]

        result = person_repo.find_decedent()

        assert result is not None
        assert result.name == "被相続人"
        assert result.is_decedent is True

    def test_find_decedent_not_found(self, person_repo, mock_client):
        """被相続人が存在しない場合のテスト"""
        mock_client.execute.return_value = []

        result = person_repo.find_decedent()

        assert result is None

    def test_find_all_success(self, person_repo, mock_client):
        """全人物取得の成功テスト"""
        mock_nodes = [
            {"p": {"name": "太郎", "is_alive": True, "is_decedent": False}},
            {"p": {"name": "花子", "is_alive": True, "is_decedent": False}},
            {"p": {"name": "次郎", "is_alive": False, "is_decedent": True,
                   "death_date": Mock(year=2025, month=6, day=15)}}
        ]
        mock_client.execute.return_value = mock_nodes

        result = person_repo.find_all()

        assert len(result) == 3
        assert result[0].name == "太郎"
        assert result[1].name == "花子"
        assert result[2].name == "次郎"

    def test_find_all_empty(self, person_repo, mock_client):
        """全人物取得で結果が空の場合のテスト"""
        mock_client.execute.return_value = []

        result = person_repo.find_all()

        assert len(result) == 0

    def test_update_person_success(self, person_repo, mock_client, sample_person):
        """人物更新の成功テスト"""
        mock_client.execute.return_value = [{"p": {}}]

        result = person_repo.update(sample_person)

        assert result == sample_person
        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["name"] == "山田太郎"
        assert params["is_alive"] is False

    def test_update_person_not_found(self, person_repo, mock_client, sample_person):
        """人物更新で対象が見つからない場合のテスト"""
        mock_client.execute.return_value = []

        with pytest.raises(DatabaseException) as exc_info:
            person_repo.update(sample_person)

        assert "人物が見つかりません" in str(exc_info.value)

    def test_delete_person_success(self, person_repo, mock_client):
        """人物削除の成功テスト"""
        mock_client.execute.return_value = []

        person_repo.delete("山田太郎")

        assert mock_client.execute.call_count == 1

    def test_delete_person_error(self, person_repo, mock_client):
        """人物削除のエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Delete failed")

        with pytest.raises(DatabaseException) as exc_info:
            person_repo.delete("山田太郎")

        assert "人物削除エラー" in str(exc_info.value)

    def test_delete_all_success(self, person_repo, mock_client):
        """全人物削除の成功テスト"""
        mock_client.execute.return_value = []

        person_repo.delete_all()

        assert mock_client.execute.call_count == 1

    def test_to_person_conversion_full_data(self, person_repo):
        """_to_personメソッドの完全データ変換テスト"""
        node = {
            "name": "山田太郎",
            "is_alive": False,
            "is_decedent": True,
            "birth_date": Mock(year=1950, month=1, day=1),
            "death_date": Mock(year=2025, month=6, day=15),
            "gender": "male"
        }

        result = person_repo._to_person(node)

        assert result.name == "山田太郎"
        assert result.is_alive is False
        assert result.is_decedent is True
        assert result.birth_date == date(1950, 1, 1)
        assert result.death_date == date(2025, 6, 15)
        assert result.gender == Gender.MALE

    def test_to_person_conversion_minimal_data(self, person_repo):
        """_to_personメソッドの最小データ変換テスト"""
        node = {
            "name": "山田花子",
            "is_alive": True,
            "is_decedent": False
        }

        result = person_repo._to_person(node)

        assert result.name == "山田花子"
        assert result.is_alive is True
        assert result.birth_date is None
        assert result.death_date is None
        assert result.gender == Gender.UNKNOWN

    def test_create_person_with_contact_info(self, person_repo, mock_client):
        """連絡先情報付き人物作成テスト"""
        person = Person(
            name="山田三郎",
            is_alive=True,
            is_decedent=False,
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="saburo@example.com"
        )
        mock_client.execute.return_value = [{"p": {}}]

        result = person_repo.create(person)

        assert result.name == "山田三郎"
        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["address"] == "東京都渋谷区渋谷1-1-1"
        assert params["phone"] == "03-1234-5678"
        assert params["email"] == "saburo@example.com"

    def test_update_person_with_contact_info(self, person_repo, mock_client):
        """連絡先情報付き人物更新テスト"""
        person = Person(
            name="山田四郎",
            is_alive=True,
            is_decedent=False,
            address="大阪府大阪市北区梅田1-1-1",
            phone="06-9876-5432",
            email="shiro@example.com"
        )
        mock_client.execute.return_value = [{"p": {}}]

        result = person_repo.update(person)

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["address"] == "大阪府大阪市北区梅田1-1-1"
        assert params["phone"] == "06-9876-5432"
        assert params["email"] == "shiro@example.com"

    def test_to_person_conversion_with_contact_info(self, person_repo):
        """連絡先情報を含む_to_personメソッドの変換テスト"""
        node = {
            "name": "山田五郎",
            "is_alive": True,
            "is_decedent": False,
            "address": "愛知県名古屋市中区栄1-1-1",
            "phone": "052-123-4567",
            "email": "goro@example.com"
        }

        result = person_repo._to_person(node)

        assert result.name == "山田五郎"
        assert result.address == "愛知県名古屋市中区栄1-1-1"
        assert result.phone == "052-123-4567"
        assert result.email == "goro@example.com"

    def test_to_person_conversion_partial_contact_info(self, person_repo):
        """部分的な連絡先情報を含む_to_personメソッドの変換テスト"""
        node = {
            "name": "山田六郎",
            "is_alive": True,
            "is_decedent": False,
            "address": "福岡県福岡市博多区博多駅前1-1-1",
            "phone": None,
            "email": None
        }

        result = person_repo._to_person(node)

        assert result.name == "山田六郎"
        assert result.address == "福岡県福岡市博多区博多駅前1-1-1"
        assert result.phone is None
        assert result.email is None


class TestRelationshipRepository:
    """RelationshipRepositoryのユニットテスト"""

    @pytest.fixture
    def mock_client(self):
        """モッククライアントのフィクスチャ"""
        return Mock()

    @pytest.fixture
    def rel_repo(self, mock_client):
        """RelationshipRepositoryのフィクスチャ"""
        return RelationshipRepository(mock_client)

    def test_create_child_of_success(self, rel_repo, mock_client):
        """親子関係作成の成功テスト"""
        mock_client.execute.return_value = []

        rel_repo.create_child_of("子", "親")

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["child_name"] == "子"
        assert params["parent_name"] == "親"
        assert params["adoption"] is False
        assert params["is_biological"] is True

    def test_create_child_of_with_adoption(self, rel_repo, mock_client):
        """養子縁組での親子関係作成テスト"""
        mock_client.execute.return_value = []

        rel_repo.create_child_of("養子", "養親", adoption=True, is_biological=False)

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["adoption"] is True
        assert params["is_biological"] is False

    def test_create_child_of_error(self, rel_repo, mock_client):
        """親子関係作成のエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Constraint violation")

        with pytest.raises(DatabaseException) as exc_info:
            rel_repo.create_child_of("子", "親")

        assert "親子関係作成エラー" in str(exc_info.value)

    def test_create_spouse_of_success(self, rel_repo, mock_client):
        """配偶者関係作成の成功テスト"""
        mock_client.execute.return_value = []

        rel_repo.create_spouse_of("配偶者1", "配偶者2")

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["person1_name"] == "配偶者1"
        assert params["person2_name"] == "配偶者2"
        assert params["is_current"] is True

    def test_create_spouse_of_with_dates(self, rel_repo, mock_client):
        """婚姻日・離婚日付きの配偶者関係作成テスト"""
        mock_client.execute.return_value = []
        marriage_date = date(2000, 4, 1)
        divorce_date = date(2010, 6, 15)

        rel_repo.create_spouse_of(
            "配偶者1",
            "配偶者2",
            marriage_date=marriage_date,
            divorce_date=divorce_date,
            is_current=False
        )

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["marriage_date"] == "2000-04-01"
        assert params["divorce_date"] == "2010-06-15"
        assert params["is_current"] is False

    def test_create_sibling_of_full_blood(self, rel_repo, mock_client):
        """全血兄弟姉妹関係作成テスト"""
        mock_client.execute.return_value = []

        rel_repo.create_sibling_of("兄", "妹", blood_type=BloodType.FULL)

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["person1_name"] == "兄"
        assert params["person2_name"] == "妹"
        assert params["blood_type"] == "full"
        assert params["shared_parent"] == "both"

    def test_create_sibling_of_half_blood(self, rel_repo, mock_client):
        """半血兄弟姉妹関係作成テスト"""
        mock_client.execute.return_value = []

        rel_repo.create_sibling_of("兄", "妹", blood_type=BloodType.HALF, shared_parent="mother")

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["blood_type"] == "half"
        assert params["shared_parent"] == "mother"

    def test_create_renounced_success(self, rel_repo, mock_client):
        """相続放棄関係作成の成功テスト"""
        mock_client.execute.return_value = []
        renounce_date = date(2025, 7, 1)

        rel_repo.create_renounced("放棄者", "被相続人", renounce_date, reason="経済的理由")

        call_args = mock_client.execute.call_args
        params = call_args[0][1]
        assert params["person_name"] == "放棄者"
        assert params["decedent_name"] == "被相続人"
        assert params["renounce_date"] == "2025-07-01"
        assert params["reason"] == "経済的理由"

    def test_find_children_success(self, rel_repo, mock_client):
        """子検索の成功テスト"""
        mock_children = [
            {"child": {"name": "子1", "is_alive": True, "is_decedent": False}},
            {"child": {"name": "子2", "is_alive": True, "is_decedent": False}}
        ]
        mock_client.execute.return_value = mock_children

        result = rel_repo.find_children("親")

        assert len(result) == 2
        assert result[0].name == "子1"
        assert result[1].name == "子2"

    def test_find_children_none(self, rel_repo, mock_client):
        """子が存在しない場合のテスト"""
        mock_client.execute.return_value = []

        result = rel_repo.find_children("親")

        assert len(result) == 0

    def test_find_parents_success(self, rel_repo, mock_client):
        """親検索の成功テスト"""
        mock_parents = [
            {"parent": {"name": "父", "is_alive": True, "is_decedent": False}},
            {"parent": {"name": "母", "is_alive": True, "is_decedent": False}}
        ]
        mock_client.execute.return_value = mock_parents

        result = rel_repo.find_parents("子")

        assert len(result) == 2
        assert result[0].name == "父"
        assert result[1].name == "母"

    def test_find_spouse_found(self, rel_repo, mock_client):
        """配偶者検索の成功テスト"""
        mock_spouse = [{"spouse": {"name": "配偶者", "is_alive": True, "is_decedent": False}}]
        mock_client.execute.return_value = mock_spouse

        result = rel_repo.find_spouse("本人")

        assert result is not None
        assert result.name == "配偶者"

    def test_find_spouse_not_found(self, rel_repo, mock_client):
        """配偶者が存在しない場合のテスト"""
        mock_client.execute.return_value = []

        result = rel_repo.find_spouse("本人")

        assert result is None

    def test_find_siblings_full_blood(self, rel_repo, mock_client):
        """全血兄弟姉妹検索のテスト"""
        mock_siblings = [
            {
                "sibling": {"name": "兄", "is_alive": True, "is_decedent": False},
                "r": {"blood_type": "full"}
            },
            {
                "sibling": {"name": "妹", "is_alive": True, "is_decedent": False},
                "r": {"blood_type": "full"}
            }
        ]
        mock_client.execute.return_value = mock_siblings

        result = rel_repo.find_siblings("本人")

        assert len(result) == 2
        assert result[0][0].name == "兄"
        assert result[0][1] == BloodType.FULL
        assert result[1][0].name == "妹"
        assert result[1][1] == BloodType.FULL

    def test_find_siblings_mixed_blood(self, rel_repo, mock_client):
        """全血・半血混在の兄弟姉妹検索のテスト"""
        mock_siblings = [
            {
                "sibling": {"name": "全血兄", "is_alive": True, "is_decedent": False},
                "r": {"blood_type": "full"}
            },
            {
                "sibling": {"name": "半血妹", "is_alive": True, "is_decedent": False},
                "r": {"blood_type": "half"}
            }
        ]
        mock_client.execute.return_value = mock_siblings

        result = rel_repo.find_siblings("本人")

        assert len(result) == 2
        assert result[0][1] == BloodType.FULL
        assert result[1][1] == BloodType.HALF


class TestInheritanceRepository:
    """InheritanceRepositoryのユニットテスト"""

    @pytest.fixture
    def mock_client(self):
        """モッククライアントのフィクスチャ"""
        return Mock()

    @pytest.fixture
    def inheritance_repo(self, mock_client):
        """InheritanceRepositoryのフィクスチャ"""
        return InheritanceRepository(mock_client)

    def test_get_spouse_found(self, inheritance_repo, mock_client):
        """配偶者取得の成功テスト"""
        mock_spouse = [{"spouse": {"name": "配偶者", "is_alive": True, "is_decedent": False}}]
        mock_client.execute.return_value = mock_spouse

        result = inheritance_repo.get_spouse()

        assert result is not None
        assert result.name == "配偶者"

    def test_get_spouse_not_found(self, inheritance_repo, mock_client):
        """配偶者が存在しない場合のテスト"""
        mock_client.execute.return_value = []

        result = inheritance_repo.get_spouse()

        assert result is None

    def test_get_first_rank_heirs_success(self, inheritance_repo, mock_client):
        """第1順位相続人取得の成功テスト"""
        mock_children = [
            {"child": {"name": "子1", "is_alive": True, "is_decedent": False}},
            {"child": {"name": "子2", "is_alive": True, "is_decedent": False}}
        ]
        mock_client.execute.return_value = mock_children

        result = inheritance_repo.get_first_rank_heirs()

        assert len(result) == 2
        assert result[0].name == "子1"
        assert result[1].name == "子2"

    def test_get_second_rank_heirs_success(self, inheritance_repo, mock_client):
        """第2順位相続人取得の成功テスト"""
        mock_ancestors = [
            {"ancestor": {"name": "父", "is_alive": True, "is_decedent": False}},
            {"ancestor": {"name": "母", "is_alive": True, "is_decedent": False}}
        ]
        mock_client.execute.return_value = mock_ancestors

        result = inheritance_repo.get_second_rank_heirs()

        assert len(result) == 2
        assert result[0].name == "父"
        assert result[1].name == "母"

    def test_get_third_rank_heirs_success(self, inheritance_repo, mock_client):
        """第3順位相続人取得の成功テスト"""
        mock_siblings = [
            {"sibling": {"name": "兄", "is_alive": True, "is_decedent": False}, "blood_type": "full"},
            {"sibling": {"name": "妹", "is_alive": True, "is_decedent": False}, "blood_type": "half"}
        ]
        mock_client.execute.return_value = mock_siblings

        result = inheritance_repo.get_third_rank_heirs()

        assert len(result) == 2
        assert result[0][0].name == "兄"
        assert result[0][1] == BloodType.FULL
        assert result[1][0].name == "妹"
        assert result[1][1] == BloodType.HALF

    def test_get_third_rank_heirs_empty(self, inheritance_repo, mock_client):
        """第3順位相続人が存在しない場合のテスト"""
        mock_client.execute.return_value = []

        result = inheritance_repo.get_third_rank_heirs()

        assert len(result) == 0

    def test_get_spouse_database_error(self, inheritance_repo, mock_client):
        """配偶者取得のデータベースエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Connection error")

        with pytest.raises(DatabaseException) as exc_info:
            inheritance_repo.get_spouse()

        assert "配偶者取得エラー" in str(exc_info.value)

    def test_get_first_rank_heirs_database_error(self, inheritance_repo, mock_client):
        """第1順位相続人取得のデータベースエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Query error")

        with pytest.raises(DatabaseException) as exc_info:
            inheritance_repo.get_first_rank_heirs()

        assert "第1順位相続人取得エラー" in str(exc_info.value)

    def test_get_second_rank_heirs_database_error(self, inheritance_repo, mock_client):
        """第2順位相続人取得のデータベースエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Query error")

        with pytest.raises(DatabaseException) as exc_info:
            inheritance_repo.get_second_rank_heirs()

        assert "第2順位相続人取得エラー" in str(exc_info.value)

    def test_get_third_rank_heirs_database_error(self, inheritance_repo, mock_client):
        """第3順位相続人取得のデータベースエラーテスト"""
        mock_client.execute.side_effect = Neo4jError("Query error")

        with pytest.raises(DatabaseException) as exc_info:
            inheritance_repo.get_third_rank_heirs()

        assert "第3順位相続人取得エラー" in str(exc_info.value)
