"""ASCIIアート家系図生成

ターミナルで表示可能なASCIIアート形式の家系図を生成します。
"""
from typing import Any

from inheritance_calculator_core.models.inheritance import (
    HeritageRank,
    InheritanceResult,
)
from inheritance_calculator_core.utils.logger import get_logger

logger = get_logger(__name__)


class AsciiTreeGenerator:
    """ASCIIアート家系図生成クラス"""

    def __init__(self, max_width: int = 80):
        """初期化

        Args:
            max_width: 最大幅（文字数）
        """
        self.max_width = max_width

    def generate_simple_tree(self, result: InheritanceResult) -> str:
        """シンプルな家系図を生成

        Args:
            result: 相続計算結果

        Returns:
            str: ASCIIアート家系図
        """
        lines = []

        # タイトル
        lines.append("=" * 60)
        lines.append("家系図".center(60))
        lines.append("=" * 60)
        lines.append("")

        # 被相続人
        decedent_name = result.decedent.name
        lines.append(f"        ⚰️  {decedent_name} （被相続人）".center(60))
        lines.append("")

        # 配偶者
        if result.has_spouse:
            spouse_heirs = result.get_heirs_by_rank(HeritageRank.SPOUSE)
            for heir in spouse_heirs:
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                lines.append(
                    f"        💑 配偶者: {heir.person.name} - {share_text}".center(60)
                )
            lines.append("")

        # 第1順位（子）
        if result.has_children:
            lines.append("    ┌───────────── 子 ─────────────┐".center(60))
            child_heirs = result.get_heirs_by_rank(HeritageRank.FIRST)
            for heir in child_heirs:
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                # 代襲相続の判定
                is_substitute = "(代襲)" if heir.is_substitution else ""
                lines.append(
                    f"    👶 {heir.person.name} {is_substitute} - {share_text}".center(
                        60
                    )
                )
            lines.append("")

        # 第2順位（直系尊属）
        if result.has_parents:
            lines.append("    ┌───────────── 直系尊属 ─────────────┐".center(60))
            parent_heirs = result.get_heirs_by_rank(HeritageRank.SECOND)
            for heir in parent_heirs:
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                lines.append(f"    👴 {heir.person.name} - {share_text}".center(60))
            lines.append("")

        # 第3順位（兄弟姉妹）
        if result.has_siblings:
            lines.append("    ┌───────────── 兄弟姉妹 ─────────────┐".center(60))
            sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
            for heir in sibling_heirs:
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                # 代襲相続の判定
                is_substitute = "(代襲)" if heir.is_substitution else ""
                lines.append(
                    f"    👫 {heir.person.name} {is_substitute} - {share_text}".center(
                        60
                    )
                )
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_detailed_tree(self, result: InheritanceResult) -> str:
        """詳細な家系図を生成

        Args:
            result: 相続計算結果

        Returns:
            str: 詳細なASCIIアート家系図
        """
        lines = []

        # ヘッダー
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + "相続関係図（詳細版）".center(78) + "║")
        lines.append("╚" + "═" * 78 + "╝")
        lines.append("")

        # 被相続人情報
        decedent_info = f"⚰️  {result.decedent.name} （被相続人）"
        if result.decedent.death_date:
            decedent_info += f" - 死亡日: {result.decedent.death_date}"
        lines.append(decedent_info.center(80))
        lines.append("│".center(80))

        # 配偶者
        if result.has_spouse:
            lines.append("├─ 配偶者".center(80))
            spouse_heirs = result.get_heirs_by_rank(HeritageRank.SPOUSE)
            for i, heir in enumerate(spouse_heirs):
                connector = "└──" if i == len(spouse_heirs) - 1 else "├──"
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                person_line = f"   {connector} 💑 {heir.person.name}: {share_text}"
                lines.append(person_line.center(80))
            lines.append("")

        # 子（第1順位）
        if result.has_children:
            lines.append("├─ 子（第1順位）".center(80))
            child_heirs = result.get_heirs_by_rank(HeritageRank.FIRST)
            for i, heir in enumerate(child_heirs):
                connector = "└──" if i == len(child_heirs) - 1 else "├──"
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                suffix = " [代襲相続]" if heir.is_substitution else ""
                person_line = (
                    f"   {connector} 👶 {heir.person.name}: {share_text}{suffix}"
                )
                lines.append(person_line.center(80))
            lines.append("")

        # 直系尊属（第2順位）
        if result.has_parents:
            lines.append("├─ 直系尊属（第2順位）".center(80))
            parent_heirs = result.get_heirs_by_rank(HeritageRank.SECOND)
            for i, heir in enumerate(parent_heirs):
                connector = "└──" if i == len(parent_heirs) - 1 else "├──"
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                person_line = f"   {connector} 👴 {heir.person.name}: {share_text}"
                lines.append(person_line.center(80))
            lines.append("")

        # 兄弟姉妹（第3順位）
        if result.has_siblings:
            lines.append("└─ 兄弟姉妹（第3順位）".center(80))
            sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
            for i, heir in enumerate(sibling_heirs):
                connector = "└──" if i == len(sibling_heirs) - 1 else "├──"
                share_text = f"{heir.share} ({heir.share_percentage:.1f}%)"
                suffix = " [代襲相続]" if heir.is_substitution else ""
                person_line = (
                    f"   {connector} 👫 {heir.person.name}: {share_text}{suffix}"
                )
                lines.append(person_line.center(80))
            lines.append("")

        # フッター
        lines.append("")
        lines.append("─" * 80)
        lines.append(f"相続人総数: {result.total_heirs}名".center(80))
        lines.append("─" * 80)

        return "\n".join(lines)

    def check_complexity(self, result: InheritanceResult) -> dict[str, Any]:
        """家系図の複雑さをチェック

        Args:
            result: 相続計算結果

        Returns:
            Dict: 複雑さ情報
        """
        total_heirs = result.total_heirs
        has_substitution = any(heir.is_substitution for heir in result.heirs)

        # 複雑さレベル判定
        if total_heirs <= 3 and not has_substitution:
            complexity = "simple"
            recommendation = "シンプル版で表示可能"
        elif total_heirs <= 8:
            complexity = "moderate"
            recommendation = "詳細版での表示を推奨"
        else:
            complexity = "complex"
            recommendation = (
                "Graphviz形式での出力を推奨（ASCIIアートでは見にくい可能性）"
            )

        return {
            "complexity": complexity,
            "total_heirs": total_heirs,
            "has_substitution": has_substitution,
            "recommendation": recommendation,
        }
