"""家系図生成機能

Graphviz・Mermaid形式での家系図可視化機能を提供します。
"""
from pathlib import Path
from typing import List, Optional, Dict, Set
from graphviz import Digraph

from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.models.inheritance import InheritanceResult


class FamilyTreeGenerator:
    """家系図生成クラス"""

    @staticmethod
    def generate_graphviz(
        result: InheritanceResult,
        output_path: Path,
        format: str = 'png'
    ) -> None:
        """Graphviz形式の家系図を生成

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス（拡張子なし）
            format: 出力形式（png, pdf, svg等）
        """
        dot = Digraph(comment='家系図', format=format)
        dot.attr(rankdir='TB')  # Top to Bottom
        dot.attr('node', shape='box', style='rounded,filled')

        # 被相続人ノード
        decedent_label = FamilyTreeGenerator._create_person_label(
            result.decedent,
            is_decedent=True
        )
        dot.node(
            str(result.decedent.id),
            decedent_label,
            fillcolor='lightcoral',
            fontname='Arial'
        )

        # 相続人の情報を収集
        heirs_dict: Dict[str, Person] = {}
        for heir in result.heirs:
            heirs_dict[str(heir.person.id)] = heir.person

        # 配偶者ノード
        spouses = [h for h in result.heirs if h.rank.value == 'spouse']
        for heir in spouses:
            spouse = heir.person
            spouse_label = FamilyTreeGenerator._create_person_label(
                spouse,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            dot.node(
                str(spouse.id),
                spouse_label,
                fillcolor='lightblue',
                fontname='Arial'
            )
            # 配偶者関係（双方向）
            dot.edge(
                str(result.decedent.id),
                str(spouse.id),
                label='配偶者',
                dir='none',
                color='red',
                fontname='Arial'
            )

        # 子ノード
        children = [h for h in result.heirs if h.rank.value == 'first' and h.substitution_type.value == 'none']
        for heir in children:
            child = heir.person
            child_label = FamilyTreeGenerator._create_person_label(
                child,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            dot.node(
                str(child.id),
                child_label,
                fillcolor='lightgreen',
                fontname='Arial'
            )
            # 親子関係
            dot.edge(
                str(result.decedent.id),
                str(child.id),
                label='子',
                fontname='Arial'
            )

        # 代襲相続人（孫など）
        substitutes = [h for h in result.heirs if h.substitution_type.value != 'none']
        for heir in substitutes:
            substitute = heir.person
            substitute_label = FamilyTreeGenerator._create_person_label(
                substitute,
                share=heir.share,
                share_percentage=heir.share_percentage,
                is_substitute=True
            )
            dot.node(
                str(substitute.id),
                substitute_label,
                fillcolor='lightyellow',
                fontname='Arial'
            )
            # 代襲関係は被相続人からの線
            sub_type = "子の代襲" if heir.substitution_type.value == "child" else "兄弟姉妹の代襲"
            dot.edge(
                str(result.decedent.id),
                str(substitute.id),
                label=sub_type,
                style='dashed',
                fontname='Arial'
            )

        # 直系尊属ノード
        parents = [h for h in result.heirs if h.rank.value == 'second']
        for heir in parents:
            parent = heir.person
            parent_label = FamilyTreeGenerator._create_person_label(
                parent,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            dot.node(
                str(parent.id),
                parent_label,
                fillcolor='lavender',
                fontname='Arial'
            )
            # 親子関係（逆向き）
            dot.edge(
                str(parent.id),
                str(result.decedent.id),
                label='親',
                fontname='Arial'
            )

        # 兄弟姉妹ノード
        siblings = [h for h in result.heirs if h.rank.value == 'third' and h.substitution_type.value == 'none']
        for heir in siblings:
            sibling = heir.person
            sibling_label = FamilyTreeGenerator._create_person_label(
                sibling,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            dot.node(
                str(sibling.id),
                sibling_label,
                fillcolor='lightgray',
                fontname='Arial'
            )
            # 兄弟姉妹関係（横並び）
            dot.edge(
                str(result.decedent.id),
                str(sibling.id),
                label='兄弟姉妹',
                dir='none',
                color='gray',
                fontname='Arial'
            )

        # ファイル出力
        dot.render(str(output_path), cleanup=True)

    @staticmethod
    def _create_person_label(
        person: Person,
        share: Optional[object] = None,
        share_percentage: Optional[float] = None,
        is_decedent: bool = False,
        is_substitute: bool = False
    ) -> str:
        """人物ノードのラベルを作成

        Args:
            person: 人物
            share: 相続割合（分数）
            share_percentage: 相続割合（百分率）
            is_decedent: 被相続人かどうか
            is_substitute: 代襲相続人かどうか

        Returns:
            ノードラベル
        """
        label_parts = [person.name]

        if is_decedent:
            label_parts.append("【被相続人】")

        if person.is_alive and person.current_age is not None:
            label_parts.append(f"存命, {person.current_age}歳")
        elif not person.is_alive and person.age_at_death is not None:
            label_parts.append(f"故人, 享年{person.age_at_death}歳")

        if is_substitute:
            label_parts.append("(代襲)")

        if share is not None and share_percentage is not None:
            label_parts.append(f"相続分: {share} ({share_percentage:.2f}%)")

        return "\n".join(label_parts)

    @staticmethod
    def generate_mermaid(result: InheritanceResult, output_path: Path) -> None:
        """Mermaid形式の家系図を生成

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス
        """
        lines = []

        # Mermaidヘッダー
        lines.append("```mermaid")
        lines.append("graph TB")
        lines.append("")

        # スタイル定義
        lines.append("    classDef decedent fill:#f9a,stroke:#333,stroke-width:4px")
        lines.append("    classDef spouse fill:#9cf,stroke:#333,stroke-width:2px")
        lines.append("    classDef child fill:#9f9,stroke:#333,stroke-width:2px")
        lines.append("    classDef parent fill:#ddf,stroke:#333,stroke-width:2px")
        lines.append("    classDef sibling fill:#ddd,stroke:#333,stroke-width:2px")
        lines.append("    classDef substitute fill:#ffa,stroke:#333,stroke-width:2px")
        lines.append("")

        # 被相続人ノード
        decedent_id = f"D{result.decedent.id}"
        decedent_label = FamilyTreeGenerator._create_mermaid_label(
            result.decedent,
            is_decedent=True
        )
        lines.append(f"    {decedent_id}[\"{decedent_label}\"]")
        lines.append(f"    class {decedent_id} decedent")
        lines.append("")

        # 配偶者ノード
        spouses = [h for h in result.heirs if h.rank.value == 'spouse']
        for heir in spouses:
            spouse = heir.person
            spouse_id = f"S{spouse.id}"
            spouse_label = FamilyTreeGenerator._create_mermaid_label(
                spouse,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            lines.append(f"    {spouse_id}[\"{spouse_label}\"]")
            lines.append(f"    class {spouse_id} spouse")
            lines.append(f"    {decedent_id} <-.配偶者.-> {spouse_id}")
            lines.append("")

        # 子ノード
        children = [h for h in result.heirs if h.rank.value == 'first' and h.substitution_type.value == 'none']
        for heir in children:
            child = heir.person
            child_id = f"C{child.id}"
            child_label = FamilyTreeGenerator._create_mermaid_label(
                child,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            lines.append(f"    {child_id}[\"{child_label}\"]")
            lines.append(f"    class {child_id} child")
            lines.append(f"    {decedent_id} -->|子| {child_id}")
            lines.append("")

        # 代襲相続人
        substitutes = [h for h in result.heirs if h.substitution_type.value != 'none']
        for heir in substitutes:
            substitute = heir.person
            substitute_id = f"SUB{substitute.id}"
            substitute_label = FamilyTreeGenerator._create_mermaid_label(
                substitute,
                share=heir.share,
                share_percentage=heir.share_percentage,
                is_substitute=True
            )
            lines.append(f"    {substitute_id}[\"{substitute_label}\"]")
            lines.append(f"    class {substitute_id} substitute")
            sub_type = "子の代襲" if heir.substitution_type.value == "child" else "兄弟姉妹の代襲"
            lines.append(f"    {decedent_id} -.->|{sub_type}| {substitute_id}")
            lines.append("")

        # 直系尊属ノード
        parents = [h for h in result.heirs if h.rank.value == 'second']
        for heir in parents:
            parent = heir.person
            parent_id = f"P{parent.id}"
            parent_label = FamilyTreeGenerator._create_mermaid_label(
                parent,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            lines.append(f"    {parent_id}[\"{parent_label}\"]")
            lines.append(f"    class {parent_id} parent")
            lines.append(f"    {parent_id} -->|親| {decedent_id}")
            lines.append("")

        # 兄弟姉妹ノード
        siblings = [h for h in result.heirs if h.rank.value == 'third' and h.substitution_type.value == 'none']
        for heir in siblings:
            sibling = heir.person
            sibling_id = f"SIB{sibling.id}"
            sibling_label = FamilyTreeGenerator._create_mermaid_label(
                sibling,
                share=heir.share,
                share_percentage=heir.share_percentage
            )
            lines.append(f"    {sibling_id}[\"{sibling_label}\"]")
            lines.append(f"    class {sibling_id} sibling")
            lines.append(f"    {decedent_id} <-.兄弟姉妹.-> {sibling_id}")
            lines.append("")

        lines.append("```")

        # ファイル書き込み
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    @staticmethod
    def _create_mermaid_label(
        person: Person,
        share: Optional[object] = None,
        share_percentage: Optional[float] = None,
        is_decedent: bool = False,
        is_substitute: bool = False
    ) -> str:
        """Mermaidノードのラベルを作成

        Args:
            person: 人物
            share: 相続割合（分数）
            share_percentage: 相続割合（百分率）
            is_decedent: 被相続人かどうか
            is_substitute: 代襲相続人かどうか

        Returns:
            ノードラベル
        """
        label_parts = [person.name]

        if is_decedent:
            label_parts.append("【被相続人】")

        if person.is_alive and person.current_age is not None:
            label_parts.append(f"{person.current_age}歳")
        elif not person.is_alive and person.age_at_death is not None:
            label_parts.append(f"享年{person.age_at_death}歳")

        if is_substitute:
            label_parts.append("(代襲)")

        if share is not None and share_percentage is not None:
            label_parts.append(f"{share_percentage:.1f}%")

        return "<br>".join(label_parts)

    @staticmethod
    def generate_text_tree(result: InheritanceResult, output_path: Optional[Path] = None) -> str:
        """テキスト形式の家系図を生成

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス（オプション）

        Returns:
            家系図テキスト
        """
        lines = []

        lines.append("=" * 60)
        lines.append("家系図（テキスト形式）")
        lines.append("=" * 60)
        lines.append("")

        # 被相続人
        decedent_info = f"【被相続人】 {result.decedent.name}"
        if result.decedent.age_at_death is not None:
            decedent_info += f" (享年{result.decedent.age_at_death}歳)"
        lines.append(decedent_info)
        lines.append("")

        # 配偶者
        spouses = [h for h in result.heirs if h.rank.value == 'spouse']
        if spouses:
            lines.append("├─ 配偶者")
            for heir in spouses:
                spouse = heir.person
                spouse_info = f"│  └─ {spouse.name}"
                if spouse.current_age is not None:
                    spouse_info += f" ({spouse.current_age}歳)"
                spouse_info += f" → 相続分: {heir.share} ({heir.share_percentage:.2f}%)"
                lines.append(spouse_info)
            lines.append("│")

        # 子
        children = [h for h in result.heirs if h.rank.value == 'first' and h.substitution_type.value == 'none']
        if children:
            lines.append("├─ 子")
            for i, heir in enumerate(children):
                child = heir.person
                prefix = "│  ├─" if i < len(children) - 1 else "│  └─"
                child_info = f"{prefix} {child.name}"
                if child.current_age is not None:
                    child_info += f" ({child.current_age}歳)"
                child_info += f" → 相続分: {heir.share} ({heir.share_percentage:.2f}%)"
                lines.append(child_info)
            lines.append("│")

        # 代襲相続人
        substitutes = [h for h in result.heirs if h.substitution_type.value != 'none']
        if substitutes:
            lines.append("├─ 代襲相続人")
            for i, heir in enumerate(substitutes):
                substitute = heir.person
                prefix = "│  ├─" if i < len(substitutes) - 1 else "│  └─"
                sub_type = "子の代襲" if heir.substitution_type.value == "child" else "兄弟姉妹の代襲"
                sub_info = f"{prefix} {substitute.name} ({sub_type})"
                if substitute.current_age is not None:
                    sub_info += f" ({substitute.current_age}歳)"
                sub_info += f" → 相続分: {heir.share} ({heir.share_percentage:.2f}%)"
                lines.append(sub_info)
            lines.append("│")

        # 直系尊属
        parents = [h for h in result.heirs if h.rank.value == 'second']
        if parents:
            lines.append("├─ 直系尊属")
            for i, heir in enumerate(parents):
                parent = heir.person
                prefix = "│  ├─" if i < len(parents) - 1 else "│  └─"
                parent_info = f"{prefix} {parent.name}"
                if parent.current_age is not None:
                    parent_info += f" ({parent.current_age}歳)"
                parent_info += f" → 相続分: {heir.share} ({heir.share_percentage:.2f}%)"
                lines.append(parent_info)
            lines.append("│")

        # 兄弟姉妹
        siblings = [h for h in result.heirs if h.rank.value == 'third' and h.substitution_type.value == 'none']
        if siblings:
            lines.append("└─ 兄弟姉妹")
            for i, heir in enumerate(siblings):
                sibling = heir.person
                prefix = "   ├─" if i < len(siblings) - 1 else "   └─"
                sibling_info = f"{prefix} {sibling.name}"
                if sibling.current_age is not None:
                    sibling_info += f" ({sibling.current_age}歳)"
                sibling_info += f" → 相続分: {heir.share} ({heir.share_percentage:.2f}%)"
                lines.append(sibling_info)

        lines.append("")
        lines.append("=" * 60)

        tree_text = "\n".join(lines)

        # ファイル出力（オプション）
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tree_text)

        return tree_text
