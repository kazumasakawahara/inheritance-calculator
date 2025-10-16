"""Neo4jServiceのユニットテスト

相続ケースのNeo4j保存機能のテスト
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch, call
from neo4j.exceptions import Neo4jError

from src.services.neo4j_service import Neo4jService
from src.models.person import Person, Gender
from src.models.relationship import BloodType
from src.models.inheritance import InheritanceResult, Heir, HeritageRank
from src.utils.exceptions import DatabaseException


class TestNeo4jService:
    """Neo4jServiceのユニットテスト"""

    @pytest.fixture
    def mock_client(self):
        """モッククライアントのフィクスチャ"""
        client = Mock()
        client.transaction.return_value.__enter__ = Mock(return_value=client)
        client.transaction.return_value.__exit__ = Mock(return_value=False)
        return client

    @pytest.fixture
    def neo4j_service(self, mock_client):
        """Neo4jServiceのフィクスチャ"""
        return Neo4jService(mock_client)

    @pytest.fixture
    def sample_decedent(self):
        """サンプル被相続人のフィクスチャ"""
        return Person(
            name="被相続人太郎",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15),
            gender=Gender.MALE
        )

    @pytest.fixture
    def sample_spouse(self):
        """サンプル配偶者のフィクスチャ"""
        return Person(
            name="配偶者花子",
            is_alive=True,
            gender=Gender.FEMALE
        )

    @pytest.fixture
    def sample_children(self):
        """サンプル子リストのフィクスチャ"""
        return [
            Person(name="子一郎", is_alive=True, gender=Gender.MALE),
            Person(name="子二郎", is_alive=True, gender=Gender.MALE)
        ]

    @pytest.fixture
    def sample_result(self, sample_spouse, sample_children):
        """サンプル計算結果のフィクスチャ"""
        from fractions import Fraction

        heir1 = Heir(
            person=sample_spouse,
            rank=HeritageRank.SPOUSE,
            share=Fraction(1, 2),
            share_percentage=50.0
        )
        heir2 = Heir(
            person=sample_children[0],
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0
        )
        heir3 = Heir(
            person=sample_children[1],
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0
        )

        return InheritanceResult(
            decedent=Person(
                name="被相続人太郎",
                is_alive=False,
                is_decedent=True,
                death_date=date(2025, 6, 15)
            ),
            heirs=[heir1, heir2, heir3],
            calculation_basis=["民法第900条"]
        )

    def test_save_inheritance_case_with_spouse_and_children(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_spouse,
        sample_children,
        sample_result
    ):
        """配偶者と子がいるケースの保存テスト"""
        # PersonRepositoryとRelationshipRepositoryのモック設定
        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.relationship_repo, 'create_spouse_of') as mock_spouse_rel, \
             patch.object(neo4j_service.relationship_repo, 'create_child_of') as mock_child_rel:

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[sample_spouse],
                children=sample_children,
                parents=[],
                siblings=[],
                renounced=[],
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 被相続人、配偶者、子の作成が呼ばれたか確認
            assert mock_create.call_count == 4  # decedent + spouse + 2 children
            assert mock_spouse_rel.call_count == 1
            assert mock_child_rel.call_count == 2

    def test_save_inheritance_case_with_parents(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """直系尊属がいるケースの保存テスト"""
        parents = [
            Person(name="父", is_alive=True, gender=Gender.MALE),
            Person(name="母", is_alive=True, gender=Gender.FEMALE)
        ]

        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.relationship_repo, 'create_child_of') as mock_child_rel:

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=parents,
                siblings=[],
                renounced=[],
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 被相続人と親の作成が呼ばれたか確認
            assert mock_create.call_count == 3  # decedent + 2 parents
            # 親子関係は被相続人が子として登録される
            assert mock_child_rel.call_count == 2

    def test_save_inheritance_case_with_siblings(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """兄弟姉妹がいるケースの保存テスト"""
        siblings = [
            Person(name="兄", is_alive=True, gender=Gender.MALE),
            Person(name="妹", is_alive=True, gender=Gender.FEMALE)
        ]
        sibling_blood_types = {
            "兄": BloodType.FULL,
            "妹": BloodType.HALF
        }

        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.relationship_repo, 'create_sibling_of') as mock_sibling_rel:

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=[],
                siblings=siblings,
                renounced=[],
                disqualified=[],
                disinherited=[],
                sibling_blood_types=sibling_blood_types,
                result=sample_result
            )

            # 被相続人と兄弟姉妹の作成が呼ばれたか確認
            assert mock_create.call_count == 3  # decedent + 2 siblings
            assert mock_sibling_rel.call_count == 2

            # 血縁タイプが正しく渡されているか確認
            calls = mock_sibling_rel.call_args_list
            assert calls[0][1]['blood_type'] == BloodType.FULL
            assert calls[1][1]['blood_type'] == BloodType.HALF

    def test_save_inheritance_case_with_renounced(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """相続放棄者がいるケースの保存テスト"""
        renounced = [
            Person(name="放棄者", is_alive=True)
        ]

        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.person_repo, 'find_by_name') as mock_find, \
             patch.object(neo4j_service.relationship_repo, 'create_renounced') as mock_renounced_rel:

            # 放棄者がまだ登録されていない場合
            mock_find.return_value = None

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=[],
                siblings=[],
                renounced=renounced,
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 被相続人と放棄者の作成が呼ばれたか確認
            assert mock_create.call_count == 2  # decedent + renounced person
            assert mock_renounced_rel.call_count == 1

            # 放棄日が被相続人の死亡日になっているか確認
            call_args = mock_renounced_rel.call_args
            assert call_args[1]['renounce_date'] == sample_decedent.death_date

    def test_save_inheritance_case_with_existing_renounced_person(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """既に登録されている放棄者の保存テスト"""
        renounced = [
            Person(name="既存放棄者", is_alive=True)
        ]

        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.person_repo, 'find_by_name') as mock_find, \
             patch.object(neo4j_service.relationship_repo, 'create_renounced') as mock_renounced_rel:

            # 放棄者が既に登録されている場合
            mock_find.return_value = renounced[0]

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=[],
                siblings=[],
                renounced=renounced,
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 被相続人のみ作成（放棄者は既存なので作成されない）
            assert mock_create.call_count == 1  # decedent only
            # 放棄関係は作成される
            assert mock_renounced_rel.call_count == 1

    def test_save_inheritance_case_transaction_rollback_on_error(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """エラー発生時のトランザクションロールバックテスト"""
        with patch.object(neo4j_service.person_repo, 'create') as mock_create:
            # 2回目の作成でエラーを発生させる
            mock_create.side_effect = [None, DatabaseException("エラー")]

            with pytest.raises(DatabaseException) as exc_info:
                neo4j_service.save_inheritance_case(
                    decedent=sample_decedent,
                    spouses=[Person(name="配偶者", is_alive=True)],
                    children=[],
                    parents=[],
                    siblings=[],
                    renounced=[],
                    disqualified=[],
                    disinherited=[],
                    sibling_blood_types={},
                    result=sample_result
                )

            assert "Neo4j保存エラー" in str(exc_info.value)

    def test_save_inheritance_case_complex_scenario(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_spouse,
        sample_children,
        sample_result
    ):
        """複雑なケースの保存テスト（配偶者、子、親、兄弟、放棄者）"""
        parents = [Person(name="父", is_alive=True)]
        siblings = [Person(name="兄", is_alive=True)]
        renounced = [Person(name="放棄者", is_alive=True)]
        sibling_blood_types = {"兄": BloodType.FULL}

        with patch.object(neo4j_service.person_repo, 'create') as mock_create, \
             patch.object(neo4j_service.person_repo, 'find_by_name') as mock_find, \
             patch.object(neo4j_service.relationship_repo, 'create_spouse_of') as mock_spouse_rel, \
             patch.object(neo4j_service.relationship_repo, 'create_child_of') as mock_child_rel, \
             patch.object(neo4j_service.relationship_repo, 'create_sibling_of') as mock_sibling_rel, \
             patch.object(neo4j_service.relationship_repo, 'create_renounced') as mock_renounced_rel:

            mock_find.return_value = None

            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[sample_spouse],
                children=sample_children,
                parents=parents,
                siblings=siblings,
                renounced=renounced,
                disqualified=[],
                disinherited=[],
                sibling_blood_types=sibling_blood_types,
                result=sample_result
            )

            # 全ての人物が作成されたか確認
            # decedent + spouse + 2 children + parent + sibling + renounced = 7
            assert mock_create.call_count == 7

            # 全ての関係が作成されたか確認
            assert mock_spouse_rel.call_count == 1
            assert mock_child_rel.call_count == 3  # 2 children + 1 parent
            assert mock_sibling_rel.call_count == 1
            assert mock_renounced_rel.call_count == 1

    def test_clear_all_data(self, neo4j_service, mock_client):
        """全データ削除のテスト"""
        neo4j_service.clear_all_data()

        assert mock_client.clear_database.call_count == 1

    def test_save_inheritance_case_uses_transaction(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """トランザクションが使用されることの確認テスト"""
        with patch.object(neo4j_service.person_repo, 'create'):
            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=[],
                siblings=[],
                renounced=[],
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # トランザクションが開始されたことを確認
            assert mock_client.transaction.call_count == 1

    def test_save_inheritance_case_empty_lists(
        self,
        neo4j_service,
        mock_client,
        sample_decedent,
        sample_result
    ):
        """空リストを渡した場合のテスト"""
        with patch.object(neo4j_service.person_repo, 'create') as mock_create:
            neo4j_service.save_inheritance_case(
                decedent=sample_decedent,
                spouses=[],
                children=[],
                parents=[],
                siblings=[],
                renounced=[],
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 被相続人のみ作成される
            assert mock_create.call_count == 1

    def test_save_inheritance_case_default_renounce_date(
        self,
        neo4j_service,
        mock_client,
        sample_result
    ):
        """被相続人の死亡日がNoneの場合の放棄日テスト"""
        decedent_no_death_date = Person(
            name="被相続人",
            is_alive=False,
            is_decedent=True,
            death_date=None  # 死亡日なし
        )
        renounced = [Person(name="放棄者", is_alive=True)]

        with patch.object(neo4j_service.person_repo, 'create'), \
             patch.object(neo4j_service.person_repo, 'find_by_name', return_value=None), \
             patch.object(neo4j_service.relationship_repo, 'create_renounced') as mock_renounced_rel, \
             patch('src.services.neo4j_service.date') as mock_date:

            # date.today()をモック
            mock_today = date(2025, 10, 16)
            mock_date.today.return_value = mock_today

            neo4j_service.save_inheritance_case(
                decedent=decedent_no_death_date,
                spouses=[],
                children=[],
                parents=[],
                siblings=[],
                renounced=renounced,
                disqualified=[],
                disinherited=[],
                sibling_blood_types={},
                result=sample_result
            )

            # 放棄日がtoday()になっているか確認
            call_args = mock_renounced_rel.call_args
            assert call_args[1]['renounce_date'] == mock_today
