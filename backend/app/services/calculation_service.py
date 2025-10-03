"""相続計算サービス - 既存のInheritanceCalculatorをバックエンドAPIから利用"""

import sys
from pathlib import Path
from typing import Any
from fractions import Fraction

# 親プロジェクトのsrcディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from services.inheritance_calculator import InheritanceCalculator  # type: ignore[import-not-found]
    from services.share_calculator import ShareCalculator  # type: ignore[import-not-found]
    from database.repositories import PersonRepository  # type: ignore[import-not-found]
    from utils.config import Neo4jSettings  # type: ignore[import-not-found]
except ImportError:
    # テスト環境での代替処理
    InheritanceCalculator = None  # type: ignore[assignment, misc]
    ShareCalculator = None  # type: ignore[assignment, misc]
    PersonRepository = None  # type: ignore[assignment, misc]
    Neo4jSettings = None  # type: ignore[assignment, misc]
from app.core.config import settings
from app.schemas.calculation_schema import HeirInfo, CalculationResult
from app.services.neo4j_service import Neo4jService


class CalculationService:
    """相続計算サービスクラス"""

    def __init__(self, neo4j_service: Neo4jService) -> None:
        """初期化

        Args:
            neo4j_service: Neo4jServiceインスタンス
        """
        self.neo4j_service = neo4j_service

        # 既存のNeo4j設定でInheritanceCalculatorを初期化
        neo4j_settings = Neo4jSettings(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        self.calculator = InheritanceCalculator(neo4j_settings)
        self.share_calculator = ShareCalculator()

    def calculate_inheritance(self, case_id: str) -> CalculationResult:
        """相続計算実行

        Args:
            case_id: 案件ID

        Returns:
            CalculationResult: 計算結果

        Raises:
            ValueError: 案件が見つからない場合
        """
        # Case存在確認
        case_node = self.neo4j_service.get_case_by_id(case_id)
        if not case_node:
            raise ValueError(f"案件が見つかりません: {case_id}")

        # 被相続人を取得
        persons = self.neo4j_service.get_persons_by_case(case_id)
        decedent = next((p for p in persons if p.get("is_decedent")), None)
        if not decedent:
            raise ValueError("被相続人が見つかりません")

        decedent_name = decedent["name"]

        # 相続人を判定（既存のInheritanceCalculatorを使用）
        # Note: 既存のcalculatorはPersonRepositoryを使ってデータを取得するため、
        # Neo4jに保存されているデータを利用できる
        inheritance_result = self.calculator.calculate_inheritance(decedent_name)

        # 相続割合を計算（ShareCalculatorを使用）
        heirs_list = inheritance_result.heirs
        shares = self.share_calculator.calculate_shares(heirs_list)

        # 結果をAPIスキーマに変換
        heir_infos: list[HeirInfo] = []
        for heir_model in heirs_list:
            # 相続割合を取得
            share_fraction = shares.get(heir_model.name, Fraction(0, 1))

            # 続柄の日本語表記
            relationship_map = {
                "spouse": "配偶者",
                "child": "子",
                "parent": "直系尊属",
                "grandparent": "祖父母",
                "sibling": "兄弟姉妹",
            }
            relationship_jp = relationship_map.get(heir_model.relationship, heir_model.relationship)

            # 相続順位
            rank_map = {"spouse": 0, "child": 1, "parent": 2, "grandparent": 2, "sibling": 3}
            rank = rank_map.get(heir_model.relationship, 0)

            heir_info = HeirInfo(
                person_id=f"person-{heir_model.name}",  # 仮のID（実際はNeo4jから取得すべき）
                name=heir_model.name,
                relationship=relationship_jp,
                rank=rank,
                share_numerator=share_fraction.numerator,
                share_denominator=share_fraction.denominator,
                share_percentage=float(share_fraction) * 100,
                is_substitute=heir_model.is_substitute_heir,
                substitute_for=heir_model.original_heir if heir_model.is_substitute_heir else None,
            )
            heir_infos.append(heir_info)

        # 計算根拠の生成
        calculation_basis = self._generate_calculation_basis(heir_infos)

        return CalculationResult(
            case_id=case_id,
            decedent_name=decedent_name,
            heirs=heir_infos,
            total_heirs=len(heir_infos),
            calculation_basis=calculation_basis,
        )

    def _generate_calculation_basis(self, heirs: list[HeirInfo]) -> str:
        """計算根拠を生成

        Args:
            heirs: 相続人リスト

        Returns:
            str: 計算根拠の説明
        """
        bases = []

        # 配偶者がいるかチェック
        has_spouse = any(h.relationship == "配偶者" for h in heirs)
        if has_spouse:
            bases.append("民法890条（配偶者の相続権）")

        # 第1順位（子）がいるかチェック
        has_children = any(h.rank == 1 for h in heirs)
        if has_children:
            bases.append("民法887条1項（子の相続権）")
            # 代襲相続があるかチェック
            has_substitute = any(h.is_substitute and h.rank == 1 for h in heirs)
            if has_substitute:
                bases.append("民法887条2項（代襲相続）")

        # 第2順位（直系尊属）がいるかチェック
        has_parents = any(h.rank == 2 for h in heirs)
        if has_parents:
            bases.append("民法889条1項1号（直系尊属の相続権）")

        # 第3順位（兄弟姉妹）がいるかチェック
        has_siblings = any(h.rank == 3 for h in heirs)
        if has_siblings:
            bases.append("民法889条1項2号（兄弟姉妹の相続権）")
            # 代襲相続があるかチェック
            has_substitute_sibling = any(h.is_substitute and h.rank == 3 for h in heirs)
            if has_substitute_sibling:
                bases.append("民法889条2項（兄弟姉妹の代襲相続）")

        # 相続割合の根拠
        bases.append("民法900条（法定相続分）")

        if has_substitute:
            bases.append("民法901条（代襲相続人の相続分）")

        return "、".join(bases)
