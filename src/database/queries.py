"""Cypherクエリ集

Neo4jデータベースで使用するCypherクエリを定義する。
"""
from typing import Dict, Any, Optional


class PersonQueries:
    """人物(Person)ノードに関するクエリ"""

    CREATE = """
    CREATE (p:Person {
        name: $name,
        is_alive: $is_alive,
        is_decedent: $is_decedent,
        birth_date: date($birth_date),
        death_date: CASE WHEN $death_date IS NOT NULL THEN date($death_date) ELSE NULL END,
        gender: $gender
    })
    RETURN p
    """

    FIND_BY_NAME = """
    MATCH (p:Person {name: $name})
    RETURN p
    """

    FIND_DECEDENT = """
    MATCH (p:Person {is_decedent: true})
    RETURN p
    """

    FIND_ALL = """
    MATCH (p:Person)
    RETURN p
    ORDER BY p.name
    """

    UPDATE = """
    MATCH (p:Person {name: $name})
    SET p.is_alive = $is_alive,
        p.death_date = CASE WHEN $death_date IS NOT NULL THEN date($death_date) ELSE NULL END,
        p.gender = $gender
    RETURN p
    """

    DELETE = """
    MATCH (p:Person {name: $name})
    DETACH DELETE p
    """

    DELETE_ALL = """
    MATCH (p:Person)
    DETACH DELETE p
    """


class RelationshipQueries:
    """リレーションシップに関するクエリ"""

    # 親子関係
    CREATE_CHILD_OF = """
    MATCH (child:Person {name: $child_name})
    MATCH (parent:Person {name: $parent_name})
    CREATE (child)-[r:CHILD_OF {
        adoption: $adoption,
        is_biological: $is_biological
    }]->(parent)
    RETURN r
    """

    FIND_CHILDREN = """
    MATCH (parent:Person {name: $parent_name})<-[:CHILD_OF]-(child:Person)
    RETURN child
    ORDER BY child.name
    """

    FIND_PARENTS = """
    MATCH (child:Person {name: $child_name})-[:CHILD_OF]->(parent:Person)
    RETURN parent
    ORDER BY parent.name
    """

    # 配偶者関係
    CREATE_SPOUSE_OF = """
    MATCH (person1:Person {name: $person1_name})
    MATCH (person2:Person {name: $person2_name})
    CREATE (person1)-[r:SPOUSE_OF {
        marriage_date: CASE WHEN $marriage_date IS NOT NULL THEN date($marriage_date) ELSE NULL END,
        divorce_date: CASE WHEN $divorce_date IS NOT NULL THEN date($divorce_date) ELSE NULL END,
        is_current: $is_current
    }]->(person2)
    RETURN r
    """

    FIND_SPOUSE = """
    MATCH (person:Person {name: $person_name})-[r:SPOUSE_OF]-(spouse:Person)
    WHERE r.is_current = true
    RETURN spouse
    """

    # 兄弟姉妹関係
    CREATE_SIBLING_OF = """
    MATCH (person1:Person {name: $person1_name})
    MATCH (person2:Person {name: $person2_name})
    CREATE (person1)-[r:SIBLING_OF {
        blood_type: $blood_type,
        shared_parent: $shared_parent
    }]->(person2)
    RETURN r
    """

    FIND_SIBLINGS = """
    MATCH (person:Person {name: $person_name})-[:SIBLING_OF]-(sibling:Person)
    RETURN sibling, r
    ORDER BY sibling.name
    """

    # 相続放棄
    CREATE_RENOUNCED = """
    MATCH (person:Person {name: $person_name})
    MATCH (decedent:Person {name: $decedent_name})
    CREATE (person)-[r:RENOUNCED {
        renounce_date: date($renounce_date),
        reason: $reason
    }]->(decedent)
    RETURN r
    """

    # 相続欠格
    CREATE_DISQUALIFIED = """
    MATCH (person:Person {name: $person_name})
    MATCH (decedent:Person {name: $decedent_name})
    CREATE (person)-[r:DISQUALIFIED {
        reason: $reason,
        date: date($date)
    }]->(decedent)
    RETURN r
    """

    # 相続廃除
    CREATE_DISINHERITED = """
    MATCH (person:Person {name: $person_name})
    MATCH (decedent:Person {name: $decedent_name})
    CREATE (person)-[r:DISINHERITED {
        reason: $reason,
        court_decision_date: date($court_decision_date)
    }]->(decedent)
    RETURN r
    """


class InheritanceQueries:
    """相続計算に関するクエリ"""

    # 配偶者取得
    GET_SPOUSE = """
    MATCH (decedent:Person {is_decedent: true})-[r:SPOUSE_OF]-(spouse:Person)
    WHERE spouse.is_alive = true
      AND r.is_current = true
      AND NOT EXISTS((spouse)-[:RENOUNCED]->(decedent))
    RETURN spouse
    """

    # 第1順位相続人（子）取得
    GET_FIRST_RANK_HEIRS = """
    MATCH (decedent:Person {is_decedent: true})<-[:CHILD_OF]-(child:Person)
    WHERE child.is_alive = true
      AND NOT EXISTS((child)-[:RENOUNCED]->(decedent))
      AND NOT EXISTS((child)-[:DISQUALIFIED]->(decedent))
      AND NOT EXISTS((child)-[:DISINHERITED]->(decedent))
    RETURN child
    ORDER BY child.name
    """

    # 代襲相続人取得（子の代襲）
    GET_SUBSTITUTION_HEIRS_CHILDREN = """
    MATCH (decedent:Person {is_decedent: true})<-[:CHILD_OF]-(child:Person)
    WHERE child.is_alive = false
      AND child.death_date < decedent.death_date
      AND NOT EXISTS((child)-[:RENOUNCED]->(decedent))
    MATCH (child)<-[:CHILD_OF*]-(descendant:Person)
    WHERE descendant.is_alive = true
      AND NOT EXISTS((descendant)-[:RENOUNCED]->(decedent))
      AND NOT EXISTS((descendant)-[:DISQUALIFIED]->(decedent))
      AND NOT EXISTS((descendant)-[:DISINHERITED]->(decedent))
    RETURN descendant, child, size((child)<-[:CHILD_OF*]-(descendant)) as generation
    ORDER BY generation ASC, descendant.name
    """

    # 第2順位相続人（直系尊属）取得
    GET_SECOND_RANK_HEIRS = """
    MATCH (decedent:Person {is_decedent: true})
    WHERE NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: true}))
      AND NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: false})<-[:CHILD_OF]-(:Person {is_alive: true}))
    MATCH (decedent)-[:CHILD_OF*]->(ancestor:Person)
    WHERE ancestor.is_alive = true
      AND NOT EXISTS((ancestor)-[:RENOUNCED]->(decedent))
    WITH ancestor, size((decedent)-[:CHILD_OF*]->(ancestor)) as generation
    WITH min(generation) as min_gen
    MATCH (decedent)-[:CHILD_OF*]->(ancestor:Person)
    WHERE ancestor.is_alive = true
      AND size((decedent)-[:CHILD_OF*]->(ancestor)) = min_gen
      AND NOT EXISTS((ancestor)-[:RENOUNCED]->(decedent))
    RETURN ancestor
    ORDER BY ancestor.name
    """

    # 第3順位相続人（兄弟姉妹）取得
    GET_THIRD_RANK_HEIRS = """
    MATCH (decedent:Person {is_decedent: true})
    WHERE NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: true}))
      AND NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: false})<-[:CHILD_OF]-(:Person {is_alive: true}))
      AND NOT EXISTS((decedent)-[:CHILD_OF*]->(:Person {is_alive: true}))
    MATCH (decedent)-[r:SIBLING_OF]-(sibling:Person)
    WHERE sibling.is_alive = true
      AND NOT EXISTS((sibling)-[:RENOUNCED]->(decedent))
      AND NOT EXISTS((sibling)-[:DISQUALIFIED]->(decedent))
      AND NOT EXISTS((sibling)-[:DISINHERITED]->(decedent))
    RETURN sibling, r.blood_type as blood_type
    ORDER BY sibling.name
    """

    # 代襲相続人取得（兄弟姉妹の代襲：1代限り）
    GET_SUBSTITUTION_HEIRS_SIBLINGS = """
    MATCH (decedent:Person {is_decedent: true})
    WHERE NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: true}))
      AND NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person {is_alive: false})<-[:CHILD_OF]-(:Person {is_alive: true}))
      AND NOT EXISTS((decedent)-[:CHILD_OF*]->(:Person {is_alive: true}))
    MATCH (decedent)-[r:SIBLING_OF]-(sibling:Person)
    WHERE sibling.is_alive = false
      AND sibling.death_date < decedent.death_date
      AND NOT EXISTS((sibling)-[:RENOUNCED]->(decedent))
    MATCH (sibling)<-[:CHILD_OF]-(nephew_niece:Person)
    WHERE nephew_niece.is_alive = true
      AND NOT EXISTS((nephew_niece)-[:RENOUNCED]->(decedent))
      AND NOT EXISTS((nephew_niece)-[:DISQUALIFIED]->(decedent))
      AND NOT EXISTS((nephew_niece)-[:DISINHERITED]->(decedent))
    RETURN nephew_niece, sibling, r.blood_type as blood_type
    ORDER BY nephew_niece.name
    """

    # 家系図取得（全リレーションシップ）
    GET_FAMILY_TREE = """
    MATCH (decedent:Person {is_decedent: true})
    OPTIONAL MATCH (decedent)-[r1]-(related:Person)
    OPTIONAL MATCH (related)-[r2]-(indirect:Person)
    WHERE indirect <> decedent
    RETURN decedent, r1, related, r2, indirect
    """

    # 統計情報取得
    GET_STATISTICS = """
    MATCH (p:Person)
    WITH count(p) as total_persons,
         count(CASE WHEN p.is_alive THEN 1 END) as alive_persons,
         count(CASE WHEN p.is_decedent THEN 1 END) as decedent_count
    MATCH ()-[r]->()
    WITH total_persons, alive_persons, decedent_count,
         count(r) as total_relationships
    RETURN total_persons, alive_persons, decedent_count, total_relationships
    """


class GraphQueries:
    """グラフ全体に関するクエリ"""

    # 全ノード・リレーションシップ削除（テスト用）
    DELETE_ALL = """
    MATCH (n)
    DETACH DELETE n
    """

    # 制約とインデックスの作成
    CREATE_CONSTRAINTS = [
        "CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
        "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)",
        "CREATE INDEX person_decedent_index IF NOT EXISTS FOR (p:Person) ON (p.is_decedent)",
        "CREATE INDEX person_alive_index IF NOT EXISTS FOR (p:Person) ON (p.is_alive)",
    ]

    # データベース情報取得
    GET_DATABASE_INFO = """
    CALL dbms.components() YIELD name, versions, edition
    RETURN name, versions, edition
    """


def build_person_params(
    name: str,
    is_alive: bool = True,
    is_decedent: bool = False,
    birth_date: Optional[str] = None,
    death_date: Optional[str] = None,
    gender: Optional[str] = None
) -> Dict[str, Any]:
    """
    Person作成用のパラメータを構築

    Args:
        name: 氏名
        is_alive: 生存状態
        is_decedent: 被相続人フラグ
        birth_date: 生年月日（YYYY-MM-DD形式）
        death_date: 死亡日（YYYY-MM-DD形式）
        gender: 性別

    Returns:
        Cypherクエリ用のパラメータ辞書
    """
    return {
        "name": name,
        "is_alive": is_alive,
        "is_decedent": is_decedent,
        "birth_date": birth_date,
        "death_date": death_date,
        "gender": gender
    }
