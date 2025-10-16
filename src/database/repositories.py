"""リポジトリパターンの実装

Neo4jデータベースへのデータアクセスを抽象化するリポジトリクラス。
"""
from typing import List, Optional, Dict, Any
from datetime import date
import logging

from .neo4j_client import Neo4jClient
from .queries import PersonQueries, RelationshipQueries, InheritanceQueries, build_person_params
from ..models.person import Person, Gender
from ..models.relationship import BloodType
from ..utils.exceptions import DatabaseException


class PersonRepository:
    """
    人物(Person)のリポジトリ

    Neo4jとPydanticモデル間の変換を行う。
    """

    def __init__(self, client: Neo4jClient) -> None:
        """
        初期化

        Args:
            client: Neo4jクライアント
        """
        self.client = client
        self.logger = logging.getLogger(__name__)

    def create(self, person: Person) -> Person:
        """
        人物を作成

        Args:
            person: 作成する人物

        Returns:
            作成された人物

        Raises:
            DatabaseException: 作成に失敗した場合
        """
        params = build_person_params(
            name=person.name,
            is_alive=person.is_alive,
            is_decedent=person.is_decedent,
            birth_date=person.birth_date.isoformat() if person.birth_date else None,
            death_date=person.death_date.isoformat() if person.death_date else None,
            gender=person.gender.value if person.gender else None,
            address=person.address,
            phone=person.phone,
            email=person.email
        )

        try:
            result = self.client.execute(PersonQueries.CREATE, params)
            self.logger.info(f"Created person: {person.name}")
            return person

        except Exception as e:
            self.logger.error(f"Failed to create person {person.name}: {e}")
            raise DatabaseException(f"人物作成エラー: {str(e)}")

    def find_by_name(self, name: str) -> Optional[Person]:
        """
        名前で人物を検索

        Args:
            name: 氏名

        Returns:
            見つかった人物、存在しない場合はNone
        """
        try:
            result = self.client.execute(PersonQueries.FIND_BY_NAME, {"name": name})

            if not result:
                return None

            return self._to_person(result[0]["p"])

        except Exception as e:
            self.logger.error(f"Failed to find person {name}: {e}")
            raise DatabaseException(f"人物検索エラー: {str(e)}")

    def find_decedent(self) -> Optional[Person]:
        """
        被相続人を検索

        Returns:
            被相続人、存在しない場合はNone
        """
        try:
            result = self.client.execute(PersonQueries.FIND_DECEDENT)

            if not result:
                return None

            return self._to_person(result[0]["p"])

        except Exception as e:
            self.logger.error(f"Failed to find decedent: {e}")
            raise DatabaseException(f"被相続人検索エラー: {str(e)}")

    def find_all(self) -> List[Person]:
        """
        全ての人物を取得

        Returns:
            人物のリスト
        """
        try:
            result = self.client.execute(PersonQueries.FIND_ALL)
            return [self._to_person(record["p"]) for record in result]

        except Exception as e:
            self.logger.error(f"Failed to find all persons: {e}")
            raise DatabaseException(f"人物一覧取得エラー: {str(e)}")

    def update(self, person: Person) -> Person:
        """
        人物を更新

        Args:
            person: 更新する人物

        Returns:
            更新された人物

        Raises:
            DatabaseException: 更新に失敗した場合
        """
        params = {
            "name": person.name,
            "is_alive": person.is_alive,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "gender": person.gender.value if person.gender else None,
            "address": person.address,
            "phone": person.phone,
            "email": person.email
        }

        try:
            result = self.client.execute(PersonQueries.UPDATE, params)

            if not result:
                raise DatabaseException(f"人物が見つかりません: {person.name}")

            self.logger.info(f"Updated person: {person.name}")
            return person

        except Exception as e:
            self.logger.error(f"Failed to update person {person.name}: {e}")
            raise DatabaseException(f"人物更新エラー: {str(e)}")

    def delete(self, name: str) -> None:
        """
        人物を削除

        Args:
            name: 削除する人物の氏名

        Raises:
            DatabaseException: 削除に失敗した場合
        """
        try:
            self.client.execute(PersonQueries.DELETE, {"name": name})
            self.logger.info(f"Deleted person: {name}")

        except Exception as e:
            self.logger.error(f"Failed to delete person {name}: {e}")
            raise DatabaseException(f"人物削除エラー: {str(e)}")

    def delete_all(self) -> None:
        """
        全ての人物を削除（テスト用）

        Warning:
            本番環境では使用しないこと
        """
        try:
            self.client.execute(PersonQueries.DELETE_ALL)
            self.logger.warning("Deleted all persons")

        except Exception as e:
            self.logger.error(f"Failed to delete all persons: {e}")
            raise DatabaseException(f"全人物削除エラー: {str(e)}")

    def _to_person(self, node: Dict[str, Any]) -> Person:
        """
        Neo4jノードをPersonモデルに変換

        Args:
            node: Neo4jノード

        Returns:
            Personモデル
        """
        # Neo4jのdateオブジェクトをPythonのdateに変換
        birth_date = None
        if node.get("birth_date"):
            bd = node["birth_date"]
            birth_date = date(bd.year, bd.month, bd.day) if hasattr(bd, "year") else None

        death_date = None
        if node.get("death_date"):
            dd = node["death_date"]
            death_date = date(dd.year, dd.month, dd.day) if hasattr(dd, "year") else None

        gender = Gender(node["gender"]) if node.get("gender") else Gender.UNKNOWN

        return Person(
            name=node["name"],
            is_alive=node["is_alive"],
            is_decedent=node["is_decedent"],
            birth_date=birth_date,
            death_date=death_date,
            gender=gender,
            address=node.get("address"),
            phone=node.get("phone"),
            email=node.get("email")
        )


class RelationshipRepository:
    """
    リレーションシップのリポジトリ

    親子関係、配偶者関係、兄弟姉妹関係などを管理する。
    """

    def __init__(self, client: Neo4jClient) -> None:
        """
        初期化

        Args:
            client: Neo4jクライアント
        """
        self.client = client
        self.person_repo = PersonRepository(client)
        self.logger = logging.getLogger(__name__)

    def create_child_of(
        self,
        child_name: str,
        parent_name: str,
        adoption: bool = False,
        is_biological: bool = True
    ) -> None:
        """
        親子関係を作成

        Args:
            child_name: 子の氏名
            parent_name: 親の氏名
            adoption: 養子縁組フラグ
            is_biological: 実子フラグ
        """
        params = {
            "child_name": child_name,
            "parent_name": parent_name,
            "adoption": adoption,
            "is_biological": is_biological
        }

        try:
            self.client.execute(RelationshipQueries.CREATE_CHILD_OF, params)
            self.logger.info(f"Created CHILD_OF: {child_name} -> {parent_name}")

        except Exception as e:
            self.logger.error(f"Failed to create CHILD_OF relationship: {e}")
            raise DatabaseException(f"親子関係作成エラー: {str(e)}")

    def create_spouse_of(
        self,
        person1_name: str,
        person2_name: str,
        marriage_date: Optional[date] = None,
        divorce_date: Optional[date] = None,
        is_current: bool = True
    ) -> None:
        """
        配偶者関係を作成

        Args:
            person1_name: 配偶者1の氏名
            person2_name: 配偶者2の氏名
            marriage_date: 婚姻日
            divorce_date: 離婚日
            is_current: 現在の配偶者フラグ
        """
        params = {
            "person1_name": person1_name,
            "person2_name": person2_name,
            "marriage_date": marriage_date.isoformat() if marriage_date else None,
            "divorce_date": divorce_date.isoformat() if divorce_date else None,
            "is_current": is_current
        }

        try:
            self.client.execute(RelationshipQueries.CREATE_SPOUSE_OF, params)
            self.logger.info(f"Created SPOUSE_OF: {person1_name} <-> {person2_name}")

        except Exception as e:
            self.logger.error(f"Failed to create SPOUSE_OF relationship: {e}")
            raise DatabaseException(f"配偶者関係作成エラー: {str(e)}")

    def create_sibling_of(
        self,
        person1_name: str,
        person2_name: str,
        blood_type: BloodType = BloodType.FULL,
        shared_parent: str = "both"
    ) -> None:
        """
        兄弟姉妹関係を作成

        Args:
            person1_name: 兄弟姉妹1の氏名
            person2_name: 兄弟姉妹2の氏名
            blood_type: 血縁タイプ
            shared_parent: 共通の親
        """
        params = {
            "person1_name": person1_name,
            "person2_name": person2_name,
            "blood_type": blood_type.value,
            "shared_parent": shared_parent
        }

        try:
            self.client.execute(RelationshipQueries.CREATE_SIBLING_OF, params)
            self.logger.info(f"Created SIBLING_OF: {person1_name} <-> {person2_name}")

        except Exception as e:
            self.logger.error(f"Failed to create SIBLING_OF relationship: {e}")
            raise DatabaseException(f"兄弟姉妹関係作成エラー: {str(e)}")

    def create_renounced(
        self,
        person_name: str,
        decedent_name: str,
        renounce_date: date,
        reason: Optional[str] = None
    ) -> None:
        """
        相続放棄関係を作成

        Args:
            person_name: 放棄者の氏名
            decedent_name: 被相続人の氏名
            renounce_date: 放棄日
            reason: 理由
        """
        params = {
            "person_name": person_name,
            "decedent_name": decedent_name,
            "renounce_date": renounce_date.isoformat(),
            "reason": reason
        }

        try:
            self.client.execute(RelationshipQueries.CREATE_RENOUNCED, params)
            self.logger.info(f"Created RENOUNCED: {person_name} -> {decedent_name}")

        except Exception as e:
            self.logger.error(f"Failed to create RENOUNCED relationship: {e}")
            raise DatabaseException(f"相続放棄関係作成エラー: {str(e)}")

    def find_children(self, parent_name: str) -> List[Person]:
        """
        親の子を検索

        Args:
            parent_name: 親の氏名

        Returns:
            子のリスト
        """
        try:
            result = self.client.execute(
                RelationshipQueries.FIND_CHILDREN,
                {"parent_name": parent_name}
            )
            return [self.person_repo._to_person(record["child"]) for record in result]

        except Exception as e:
            self.logger.error(f"Failed to find children of {parent_name}: {e}")
            raise DatabaseException(f"子の検索エラー: {str(e)}")

    def find_parents(self, child_name: str) -> List[Person]:
        """
        子の親を検索

        Args:
            child_name: 子の氏名

        Returns:
            親のリスト
        """
        try:
            result = self.client.execute(
                RelationshipQueries.FIND_PARENTS,
                {"child_name": child_name}
            )
            return [self.person_repo._to_person(record["parent"]) for record in result]

        except Exception as e:
            self.logger.error(f"Failed to find parents of {child_name}: {e}")
            raise DatabaseException(f"親の検索エラー: {str(e)}")

    def find_spouse(self, person_name: str) -> Optional[Person]:
        """
        配偶者を検索

        Args:
            person_name: 氏名

        Returns:
            配偶者、存在しない場合はNone
        """
        try:
            result = self.client.execute(
                RelationshipQueries.FIND_SPOUSE,
                {"person_name": person_name}
            )

            if not result:
                return None

            return self.person_repo._to_person(result[0]["spouse"])

        except Exception as e:
            self.logger.error(f"Failed to find spouse of {person_name}: {e}")
            raise DatabaseException(f"配偶者の検索エラー: {str(e)}")

    def find_siblings(self, person_name: str) -> List[tuple[Person, BloodType]]:
        """
        兄弟姉妹を検索

        Args:
            person_name: 氏名

        Returns:
            (兄弟姉妹, 血縁タイプ)のリスト
        """
        try:
            result = self.client.execute(
                RelationshipQueries.FIND_SIBLINGS,
                {"person_name": person_name}
            )

            siblings = []
            for record in result:
                sibling = self.person_repo._to_person(record["sibling"])
                blood_type = BloodType(record["r"]["blood_type"]) if "r" in record else BloodType.FULL
                siblings.append((sibling, blood_type))

            return siblings

        except Exception as e:
            self.logger.error(f"Failed to find siblings of {person_name}: {e}")
            raise DatabaseException(f"兄弟姉妹の検索エラー: {str(e)}")


class InheritanceRepository:
    """
    相続計算用のリポジトリ

    相続人の取得など、相続計算に特化したクエリを実行する。
    """

    def __init__(self, client: Neo4jClient) -> None:
        """
        初期化

        Args:
            client: Neo4jクライアント
        """
        self.client = client
        self.person_repo = PersonRepository(client)
        self.logger = logging.getLogger(__name__)

    def get_spouse(self) -> Optional[Person]:
        """
        配偶者を取得

        Returns:
            配偶者、存在しない場合はNone
        """
        try:
            result = self.client.execute(InheritanceQueries.GET_SPOUSE)

            if not result:
                return None

            return self.person_repo._to_person(result[0]["spouse"])

        except Exception as e:
            self.logger.error(f"Failed to get spouse: {e}")
            raise DatabaseException(f"配偶者取得エラー: {str(e)}")

    def get_first_rank_heirs(self) -> List[Person]:
        """
        第1順位相続人（子）を取得

        Returns:
            子のリスト
        """
        try:
            result = self.client.execute(InheritanceQueries.GET_FIRST_RANK_HEIRS)
            return [self.person_repo._to_person(record["child"]) for record in result]

        except Exception as e:
            self.logger.error(f"Failed to get first rank heirs: {e}")
            raise DatabaseException(f"第1順位相続人取得エラー: {str(e)}")

    def get_second_rank_heirs(self) -> List[Person]:
        """
        第2順位相続人（直系尊属）を取得

        Returns:
            直系尊属のリスト
        """
        try:
            result = self.client.execute(InheritanceQueries.GET_SECOND_RANK_HEIRS)
            return [self.person_repo._to_person(record["ancestor"]) for record in result]

        except Exception as e:
            self.logger.error(f"Failed to get second rank heirs: {e}")
            raise DatabaseException(f"第2順位相続人取得エラー: {str(e)}")

    def get_third_rank_heirs(self) -> List[tuple[Person, BloodType]]:
        """
        第3順位相続人（兄弟姉妹）を取得

        Returns:
            (兄弟姉妹, 血縁タイプ)のリスト
        """
        try:
            result = self.client.execute(InheritanceQueries.GET_THIRD_RANK_HEIRS)

            heirs = []
            for record in result:
                sibling = self.person_repo._to_person(record["sibling"])
                blood_type = BloodType(record["blood_type"])
                heirs.append((sibling, blood_type))

            return heirs

        except Exception as e:
            self.logger.error(f"Failed to get third rank heirs: {e}")
            raise DatabaseException(f"第3順位相続人取得エラー: {str(e)}")
