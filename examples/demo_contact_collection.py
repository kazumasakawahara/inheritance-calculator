"""連絡先情報収集のデモスクリプト

相続計算後の連絡先情報収集機能をデモンストレーションします。
"""
from datetime import date
from fractions import Fraction

from src.models.person import Person
from src.models.inheritance import InheritanceResult, Heir, HeritageRank, SubstitutionType
from src.cli.contact_input import ContactInfoCollector
from src.cli.report_generator import ReportGenerator
from src.cli.display import display_result, display_info
from pathlib import Path
from rich.console import Console

console = Console()


def main():
    """デモメイン関数"""

    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  連絡先情報収集機能 デモンストレーション[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # Step 1: サンプル相続ケースの作成
    console.print("[bold green]Step 1: サンプル相続ケースの作成[/bold green]\n")

    decedent = Person(
        name="山田太郎",
        is_decedent=True,
        is_alive=False,
        birth_date=date(1950, 1, 1),
        death_date=date(2025, 6, 15)
    )

    spouse = Person(
        name="山田花子",
        is_alive=True,
        birth_date=date(1955, 3, 10)
    )

    child1 = Person(
        name="山田一郎",
        is_alive=True,
        birth_date=date(1980, 5, 20)
    )

    child2 = Person(
        name="山田二郎",
        is_alive=True,
        birth_date=date(1983, 11, 12)
    )

    # 相続計算結果の構築
    heirs = [
        Heir(
            person=spouse,
            rank=HeritageRank.SPOUSE,
            share=Fraction(1, 2),
            share_percentage=50.0,
            substitution_type=SubstitutionType.NONE
        ),
        Heir(
            person=child1,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0,
            substitution_type=SubstitutionType.NONE
        ),
        Heir(
            person=child2,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0,
            substitution_type=SubstitutionType.NONE
        ),
    ]

    result = InheritanceResult(
        decedent=decedent,
        heirs=heirs,
        calculation_basis=[
            "民法890条（配偶者の相続権）",
            "民法887条1項（子の相続権）",
            "民法900条1号（配偶者1/2、子1/2）",
        ]
    )

    # 相続計算結果の表示
    console.print("[dim]被相続人: 山田太郎（故人）[/dim]")
    console.print("[dim]相続人: 山田花子（配偶者）、山田一郎（子）、山田二郎（子）[/dim]")
    console.print("[dim]相続割合: 花子 1/2、一郎 1/4、二郎 1/4[/dim]\n")

    # Step 2: 相続計算結果の表示
    console.print("[bold green]Step 2: 相続計算結果の表示[/bold green]\n")
    display_result(result)

    # Step 3: 連絡先情報の収集
    console.print("\n[bold green]Step 3: 連絡先情報の収集[/bold green]\n")

    collector = ContactInfoCollector()
    updated_persons = collector.collect_contact_info_for_heirs(result)

    if updated_persons:
        # Step 4: 連絡先サマリーの表示
        console.print("\n[bold green]Step 4: 連絡先サマリーの表示[/bold green]\n")
        collector.display_contact_summary(updated_persons)
    else:
        console.print("\n[yellow]連絡先情報は収集されませんでした。[/yellow]")
        return

    # Step 5: レポート生成
    console.print("\n[bold green]Step 5: レポート生成[/bold green]\n")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Markdownレポート
    md_path = output_dir / "contact_demo_report.md"
    ReportGenerator.generate_markdown(result, md_path)
    display_info(f"✓ Markdownレポート: {md_path}")

    # PDFレポート
    pdf_path = output_dir / "contact_demo_report.pdf"
    ReportGenerator.generate_pdf(result, pdf_path)
    display_info(f"✓ PDFレポート: {pdf_path}")

    # CSV連絡先エクスポート
    csv_path = output_dir / "contact_demo_contacts.csv"
    ReportGenerator.export_contact_csv(result, csv_path)
    display_info(f"✓ CSV連絡先: {csv_path}")

    console.print("\n[bold green]✓ デモ完了！[/bold green]")
    console.print(f"[dim]生成されたファイルは {output_dir}/ ディレクトリに保存されています。[/dim]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]デモを中断しました。[/yellow]")
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {str(e)}[/red]")
        console.print_exception(show_locals=True)
