"""Neo4jサービス - 既存のNeo4jClientをバックエンドAPIから利用"""

import sys
from pathlib import Path
from typing import Any, Optional

# 親プロジェクトのsrcディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from database.neo4j_client import Neo4jClient  # type: ignore[import-not-found]
    from utils.config import Neo4jSettings  # type: ignore[import-not-found]
except ImportError:
    # テスト環境での代替処理
    Neo4jClient = None  # type: ignore[assignment, misc]
    Neo4jSettings = None  # type: ignore[assignment, misc]
from app.core.config import settings


class Neo4jService:
    """Neo4jサービスクラス"""

    def __init__(self) -> None:
        """初期化"""
        # バックエンド設定から既存のNeo4jClientを初期化
        neo4j_settings = Neo4jSettings(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        self.client = Neo4jClient(neo4j_settings)

    def connect(self) -> None:
        """Neo4j接続"""
        self.client.connect()

    def close(self) -> None:
        """Neo4j切断"""
        self.client.close()

    def execute_query(self, query: str, parameters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """クエリ実行

        Args:
            query: Cypherクエリ
            parameters: クエリパラメータ

        Returns:
            list[dict[str, Any]]: クエリ結果
        """
        result: list[dict[str, Any]] = self.client.execute_query(query, parameters)
        return result

    def health_check(self) -> bool:
        """ヘルスチェック

        Returns:
            bool: 接続が正常ならTrue
        """
        try:
            result = self.execute_query("RETURN 1 as health")
            return len(result) > 0 and result[0].get("health") == 1
        except Exception:
            return False

    # Case管理用メソッド
    def create_case_node(self, case_id: str, title: str, description: Optional[str] = None) -> dict[str, Any]:
        """Case節点作成

        Args:
            case_id: 案件ID
            title: 案件名
            description: 説明

        Returns:
            dict[str, Any]: 作成されたCase節点
        """
        query = """
        CREATE (c:Case {
            id: $case_id,
            title: $title,
            description: $description,
            status: 'draft',
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN c
        """
        result = self.execute_query(query, {"case_id": case_id, "title": title, "description": description})
        return result[0]["c"] if result else {}

    def get_case_by_id(self, case_id: str) -> Optional[dict[str, Any]]:
        """Case節点取得

        Args:
            case_id: 案件ID

        Returns:
            Optional[dict[str, Any]]: Case節点、存在しない場合None
        """
        query = """
        MATCH (c:Case {id: $case_id})
        RETURN c
        """
        result = self.execute_query(query, {"case_id": case_id})
        return result[0]["c"] if result else None

    def get_all_cases(self) -> list[dict[str, Any]]:
        """全Case取得

        Returns:
            list[dict[str, Any]]: Case節点リスト
        """
        query = """
        MATCH (c:Case)
        RETURN c
        ORDER BY c.created_at DESC
        """
        result = self.execute_query(query)
        return [record["c"] for record in result]

    def update_case(self, case_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Case更新

        Args:
            case_id: 案件ID
            updates: 更新内容

        Returns:
            Optional[dict[str, Any]]: 更新後のCase節点
        """
        # SET句を動的生成
        set_clauses = [f"c.{key} = ${key}" for key in updates.keys()]
        set_clauses.append("c.updated_at = datetime()")
        set_clause = ", ".join(set_clauses)

        query = f"""
        MATCH (c:Case {{id: $case_id}})
        SET {set_clause}
        RETURN c
        """
        params = {"case_id": case_id, **updates}
        result = self.execute_query(query, params)
        return result[0]["c"] if result else None

    def delete_case(self, case_id: str) -> bool:
        """Case削除（関連する全節点と関係も削除）

        Args:
            case_id: 案件ID

        Returns:
            bool: 削除成功したらTrue
        """
        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (c)-[:HAS_PERSON]->(p:Person)
        DETACH DELETE c, p
        """
        self.execute_query(query, {"case_id": case_id})
        return True

    # Person管理用メソッド
    def create_person_node(
        self, person_id: str, case_id: str, name: str, is_alive: bool, is_decedent: bool, **kwargs: Any
    ) -> dict[str, Any]:
        """Person節点作成

        Args:
            person_id: 人物ID
            case_id: 所属案件ID
            name: 氏名
            is_alive: 生存状態
            is_decedent: 被相続人フラグ
            **kwargs: その他属性

        Returns:
            dict[str, Any]: 作成されたPerson節点
        """
        properties = {
            "id": person_id,
            "name": name,
            "is_alive": is_alive,
            "is_decedent": is_decedent,
            **kwargs,
        }

        # プロパティ文字列生成
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])

        query = f"""
        MATCH (c:Case {{id: $case_id}})
        CREATE (p:Person {{{props_str}}})
        CREATE (c)-[:HAS_PERSON]->(p)
        RETURN p
        """
        params = {"case_id": case_id, **properties}
        result = self.execute_query(query, params)
        return result[0]["p"] if result else {}

    def get_persons_by_case(self, case_id: str) -> list[dict[str, Any]]:
        """Case配下の全Person取得

        Args:
            case_id: 案件ID

        Returns:
            list[dict[str, Any]]: Person節点リスト
        """
        query = """
        MATCH (c:Case {id: $case_id})-[:HAS_PERSON]->(p:Person)
        RETURN p
        """
        result = self.execute_query(query, {"case_id": case_id})
        return [record["p"] for record in result]

    def create_relationship(
        self, from_person_id: str, to_person_id: str, rel_type: str, properties: Optional[dict[str, Any]] = None
    ) -> bool:
        """Person間の関係性作成

        Args:
            from_person_id: 起点人物ID
            to_person_id: 終点人物ID
            rel_type: 関係性タイプ
            properties: 関係性の属性

        Returns:
            bool: 作成成功したらTrue
        """
        props = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""

        query = f"""
        MATCH (from:Person {{id: $from_id}})
        MATCH (to:Person {{id: $to_id}})
        CREATE (from)-[r:{rel_type} {{{props_str}}}]->(to)
        RETURN r
        """
        params = {"from_id": from_person_id, "to_id": to_person_id, **props}
        result = self.execute_query(query, params)
        return len(result) > 0


# グローバルインスタンス（依存性注入用）
_neo4j_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """Neo4jServiceのシングルトンインスタンス取得

    Returns:
        Neo4jService: Neo4jServiceインスタンス
    """
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
        _neo4j_service.connect()
    return _neo4j_service


def close_neo4j_service() -> None:
    """Neo4jService接続をクローズ"""
    global _neo4j_service
    if _neo4j_service is not None:
        _neo4j_service.close()
        _neo4j_service = None
