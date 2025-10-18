"""レポート生成機能

PDF・Markdown・CSV形式でのレポート出力機能を提供します。
"""
import csv
from datetime import datetime
from pathlib import Path

from inheritance_calculator_core.models.inheritance import InheritanceResult
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportGenerator:
    """レポート生成クラス"""

    @staticmethod
    def generate_markdown(result: InheritanceResult, output_path: Path) -> None:
        """Markdown形式のレポートを生成

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス
        """
        lines = []

        # ヘッダー
        lines.append("# 相続計算レポート\n")
        lines.append(
            f"**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
        )

        # 被相続人情報
        lines.append("## 被相続人情報\n")
        lines.append(f"- **氏名**: {result.decedent.name}\n")
        if result.decedent.birth_date:
            lines.append(
                f"- **生年月日**: "
                f"{result.decedent.birth_date.strftime('%Y年%m月%d日')}\n"
            )
        if result.decedent.death_date:
            lines.append(
                f"- **死亡日**: {result.decedent.death_date.strftime('%Y年%m月%d日')}\n"
            )
            age = result.decedent.age_at_death
            if age is not None:
                lines.append(f"- **享年**: {age}歳\n")
        lines.append("\n")

        # 相続人サマリー
        lines.append("## 相続人サマリー\n")
        lines.append(f"- **相続人総数**: {result.total_heirs}名\n")
        lines.append(f"- **配偶者**: {'あり' if result.has_spouse else 'なし'}\n")
        lines.append(f"- **子**: {'あり' if result.has_children else 'なし'}\n")
        lines.append(f"- **直系尊属**: {'あり' if result.has_parents else 'なし'}\n")
        lines.append(f"- **兄弟姉妹**: {'あり' if result.has_siblings else 'なし'}\n")
        lines.append("\n")

        # 相続人一覧
        lines.append("## 相続人一覧\n")
        lines.append("| 氏名 | 続柄 | 相続順位 | 相続割合（分数） | 相続割合（%） |\n")
        lines.append("|------|------|----------|------------------|---------------|\n")

        for heir in result.heirs:
            person_name = heir.person.name
            if heir.person.is_alive and heir.person.current_age is not None:
                person_name += f" (存命, {heir.person.current_age}歳)"
            elif not heir.person.is_alive and heir.person.age_at_death is not None:
                person_name += f" (故人, 享年{heir.person.age_at_death}歳)"

            rank_name = {
                "spouse": "配偶者",
                "first": "第1順位",
                "second": "第2順位",
                "third": "第3順位",
            }.get(heir.rank.value, heir.rank.value)

            relation = heir.rank.value
            if heir.substitution_type:
                sub_type_name = {"child": "子の代襲", "sibling": "兄弟姉妹の代襲"}.get(
                    heir.substitution_type.value, "代襲"
                )
                relation += f" ({sub_type_name})"

            lines.append(
                f"| {person_name} | {relation} | {rank_name} | "
                f"{heir.share} | {heir.share_percentage:.2f}% |\n"
            )

        lines.append("\n")

        # 連絡先情報（データがある場合のみ表示）
        heirs_with_contact = [
            heir
            for heir in result.heirs
            if heir.person.address or heir.person.phone or heir.person.email
        ]

        if heirs_with_contact:
            lines.append("## 相続人連絡先情報\n")
            lines.append("| 氏名 | 住所 | 電話番号 | メールアドレス |\n")
            lines.append("|------|------|----------|----------------|\n")

            for heir in heirs_with_contact:
                lines.append(
                    f"| {heir.person.name} | "
                    f"{heir.person.address or '-'} | "
                    f"{heir.person.phone or '-'} | "
                    f"{heir.person.email or '-'} |\n"
                )

            lines.append("\n")

        # 計算根拠
        lines.append("## 計算根拠\n")
        for basis in result.calculation_basis:
            lines.append(f"- {basis}\n")
        lines.append("\n")

        # 注記
        lines.append("## 注記\n")
        lines.append("- このレポートは相続実務の補助ツールとして作成されたものです。\n")
        lines.append(
            "- 実際の相続手続きは専門家（弁護士、司法書士等）に相談してください。\n"
        )
        lines.append("- 計算結果は日本の民法第5編「相続」に基づいています。\n")

        # ファイル書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    @staticmethod
    def generate_pdf(result: InheritanceResult, output_path: Path) -> None:
        """PDF形式のレポートを生成

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス
        """
        # PDFドキュメント作成
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # ストーリー（コンテンツ）
        story = []

        # スタイル設定
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=10,
        )
        normal_style = styles["Normal"]

        # タイトル
        story.append(Paragraph("相続計算レポート", title_style))
        story.append(Spacer(1, 12))

        # 作成日時
        created_at = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        story.append(Paragraph(f"作成日時: {created_at}", normal_style))
        story.append(Spacer(1, 20))

        # 被相続人情報
        story.append(Paragraph("被相続人情報", heading_style))
        decedent_info = [
            f"氏名: {result.decedent.name}",
        ]
        if result.decedent.birth_date:
            decedent_info.append(
                f"生年月日: {result.decedent.birth_date.strftime('%Y年%m月%d日')}"
            )
        if result.decedent.death_date:
            decedent_info.append(
                f"死亡日: {result.decedent.death_date.strftime('%Y年%m月%d日')}"
            )
            age = result.decedent.age_at_death
            if age is not None:
                decedent_info.append(f"享年: {age}歳")

        for info in decedent_info:
            story.append(Paragraph(info, normal_style))
        story.append(Spacer(1, 15))

        # 相続人サマリー
        story.append(Paragraph("相続人サマリー", heading_style))
        summary_data = [
            ["相続人総数", f"{result.total_heirs}名"],
            ["配偶者", "あり" if result.has_spouse else "なし"],
            ["子", "あり" if result.has_children else "なし"],
            ["直系尊属", "あり" if result.has_parents else "なし"],
            ["兄弟姉妹", "あり" if result.has_siblings else "なし"],
        ]

        summary_table = Table(summary_data, colWidths=[60 * mm, 60 * mm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # 相続人一覧
        story.append(Paragraph("相続人一覧", heading_style))

        heir_data = [["氏名", "続柄", "相続順位", "相続割合（分数）", "相続割合（%）"]]

        # 連絡先情報がある相続人を収集
        heirs_with_contact = [
            heir
            for heir in result.heirs
            if heir.person.address or heir.person.phone or heir.person.email
        ]

        for heir in result.heirs:
            person_name = heir.person.name
            if heir.person.is_alive and heir.person.current_age is not None:
                person_name += f" ({heir.person.current_age}歳)"
            elif not heir.person.is_alive and heir.person.age_at_death is not None:
                person_name += f" (享年{heir.person.age_at_death}歳)"

            rank_name = {
                "spouse": "配偶者",
                "first": "第1順位",
                "second": "第2順位",
                "third": "第3順位",
            }.get(heir.rank.value, heir.rank.value)

            relation = heir.rank.value
            if heir.substitution_type:
                sub_type_name = {"child": "子の代襲", "sibling": "兄弟姉妹の代襲"}.get(
                    heir.substitution_type.value, "代襲"
                )
                relation += f"\n({sub_type_name})"

            heir_data.append(
                [
                    person_name,
                    relation,
                    rank_name,
                    str(heir.share),
                    f"{heir.share_percentage:.2f}%",
                ]
            )

        heir_table = Table(
            heir_data, colWidths=[40 * mm, 30 * mm, 30 * mm, 35 * mm, 35 * mm]
        )
        heir_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(heir_table)
        story.append(Spacer(1, 15))

        # 連絡先情報（データがある場合のみ表示）
        if heirs_with_contact:
            story.append(Paragraph("相続人連絡先情報", heading_style))

            contact_data = [["氏名", "住所", "電話番号", "メールアドレス"]]

            for heir in heirs_with_contact:
                contact_data.append(
                    [
                        heir.person.name,
                        heir.person.address or "-",
                        heir.person.phone or "-",
                        heir.person.email or "-",
                    ]
                )

            contact_table = Table(
                contact_data, colWidths=[40 * mm, 50 * mm, 35 * mm, 45 * mm]
            )
            contact_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("ALIGN", (0, 0), (0, -1), "CENTER"),
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),
                        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(contact_table)
            story.append(Spacer(1, 15))

        # 計算根拠
        story.append(Paragraph("計算根拠", heading_style))
        for basis in result.calculation_basis:
            story.append(Paragraph(f"• {basis}", normal_style))
        story.append(Spacer(1, 15))

        # 注記
        story.append(Paragraph("注記", heading_style))
        notes = [
            "このレポートは相続実務の補助ツールとして作成されたものです。",
            "実際の相続手続きは専門家（弁護士、司法書士等）に相談してください。",
            "計算結果は日本の民法第5編「相続」に基づいています。",
        ]
        for note in notes:
            story.append(Paragraph(f"• {note}", normal_style))

        # PDF生成
        doc.build(story)

    @staticmethod
    def export_contact_csv(result: InheritanceResult, output_path: Path) -> None:
        """連絡先情報をCSV形式でエクスポート

        Args:
            result: 相続計算結果
            output_path: 出力ファイルパス
        """
        # 連絡先情報がある相続人のみ抽出
        heirs_with_contact = [
            heir
            for heir in result.heirs
            if heir.person.address or heir.person.phone or heir.person.email
        ]

        if not heirs_with_contact:
            # 連絡先情報がない場合は空のCSVを作成
            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["氏名", "続柄", "住所", "電話番号", "メールアドレス", "備考"]
                )
                writer.writerow(
                    ["", "", "", "", "", "連絡先情報が登録されている相続人はありません"]
                )
            return

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # ヘッダー行
            writer.writerow(
                [
                    "氏名",
                    "続柄",
                    "相続順位",
                    "相続割合（分数）",
                    "相続割合（%）",
                    "住所",
                    "電話番号",
                    "メールアドレス",
                ]
            )

            # データ行
            for heir in heirs_with_contact:
                rank_name = {
                    "spouse": "配偶者",
                    "first": "第1順位",
                    "second": "第2順位",
                    "third": "第3順位",
                }.get(heir.rank.value, heir.rank.value)

                relation = heir.rank.value
                if heir.substitution_type:
                    sub_type_name = {
                        "child": "子の代襲",
                        "sibling": "兄弟姉妹の代襲",
                    }.get(heir.substitution_type.value, "代襲")
                    relation += f"（{sub_type_name}）"

                writer.writerow(
                    [
                        heir.person.name,
                        relation,
                        rank_name,
                        str(heir.share),
                        f"{heir.share_percentage:.2f}",
                        heir.person.address or "",
                        heir.person.phone or "",
                        heir.person.email or "",
                    ]
                )
