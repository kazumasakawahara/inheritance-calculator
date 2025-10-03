"""Neo4jサービス

相続計算結果をNeo4jに保存するサービス。
"""
from typing import List, Dict
from datetime import date
import logging

from ..database.neo4j_client import Neo4jClient
from ..database.repositories import PersonRepository, RelationshipRepository
from ..models.person import Person
from ..models.relationship import BloodType
from ..models.inheritance import InheritanceResult
from ..utils.exceptions import DatabaseException


class Neo4jService:
    """
    Neo4jデータ保存サービス

    相続計算に使用した人物情報と関係性をNeo4jに保存する。
    """

    def __init__(self, client: Neo4jClient) -> None:
        """
        初期化

        Args:
            client: Neo4jクライアント
        """
        self.client = client
        self.person_repo = PersonRepository(client)
        self.relationship_repo = RelationshipRepository(client)
        self.logger = logging.getLogger(__name__)

    def save_inheritance_case(
        self,
        decedent: Person,
        spouses: List[Person],
        children: List[Person],
        parents: List[Person],
        siblings: List[Person],
        renounced: List[Person],
        disqualified: List[Person],
        disinherited: List[Person],
        sibling_blood_types: Dict[str, BloodType],
        result: InheritanceResult
    ) -> None:
        """
        相続ケースをNeo4jに保存

        Args:
            decedent: 被相続人
            spouses: 配偶者リスト
            children: 子リスト
            parents: 直系尊属リスト
            siblings: 兄弟姉妹リスト
            renounced: 相続放棄者リスト
            disqualified: 相続欠格者リスト
            disinherited: 相続廃除者リスト
            sibling_blood_types: 兄弟姉妹の血縁タイプ
            result: 計算結果

        Raises:
            DatabaseException: 保存に失敗した場合
        """
        try:
            with self.client.transaction():
                # 被相続人を保存
                self.logger.info(f"Saving decedent: {decedent.name}")
                self.person_repo.create(decedent)

                # 配偶者を保存
                for spouse in spouses:
                    self.logger.info(f"Saving spouse: {spouse.name}")
                    self.person_repo.create(spouse)
                    self.relationship_repo.create_spouse_of(
                        person1_name=decedent.name,
                        person2_name=spouse.name,
                        is_current=True
                    )

                # 子を保存
                for child in children:
                    self.logger.info(f"Saving child: {child.name}")
                    self.person_repo.create(child)
                    self.relationship_repo.create_child_of(
                        child_name=child.name,
                        parent_name=decedent.name
                    )

                # 直系尊属を保存
                for parent in parents:
                    self.logger.info(f"Saving parent: {parent.name}")
                    self.person_repo.create(parent)
                    self.relationship_repo.create_child_of(
                        child_name=decedent.name,
                        parent_name=parent.name
                    )

                # 兄弟姉妹を保存
                for sibling in siblings:
                    self.logger.info(f"Saving sibling: {sibling.name}")
                    self.person_repo.create(sibling)
                    blood_type = sibling_blood_types.get(sibling.name, BloodType.FULL)
                    self.relationship_repo.create_sibling_of(
                        person1_name=decedent.name,
                        person2_name=sibling.name,
                        blood_type=blood_type
                    )

                # 相続放棄者を保存
                for person in renounced:
                    self.logger.info(f"Saving renounced: {person.name}")
                    # 既に人物ノードが存在する可能性があるため、存在チェック
                    if not self.person_repo.find_by_name(person.name):
                        self.person_repo.create(person)

                    # 放棄日は被相続人の死亡日、またはデフォルト値を使用
                    renounce_date = decedent.death_date if decedent.death_date is not None else date.today()

                    self.relationship_repo.create_renounced(
                        person_name=person.name,
                        decedent_name=decedent.name,
                        renounce_date=renounce_date
                    )

                self.logger.info("Successfully saved inheritance case to Neo4j")

        except Exception as e:
            self.logger.error(f"Failed to save inheritance case: {e}", exc_info=True)
            raise DatabaseException(f"Neo4j保存エラー: {str(e)}")

    def clear_all_data(self) -> None:
        """
        全データを削除（テスト用）

        Warning:
            本番環境では使用しないこと
        """
        self.logger.warning("Clearing all data from Neo4j")
        self.client.clear_database()
