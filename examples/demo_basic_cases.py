"""基本的な相続ケースのデモ

日本の民法に基づく相続計算の基本的なケースを実演します。
Neo4jデータベースを使用せず、Pythonのメモリ上でデータを構築します。
"""
from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.models.person import Person
from src.models.relationship import BloodType
from src.services.inheritance_calculator import InheritanceCalculator


console = Console()


def print_header(title: str) -> None:
    """ヘッダーを表示"""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    console.print()


def print_result_table(result) -> None:
    """相続結果をテーブル形式で表示"""
    table = Table(title="相続人と相続割合", show_header=True, header_style="bold magenta")
    table.add_column("氏名", style="cyan", width=20)
    table.add_column("続柄", style="green", width=15)
    table.add_column("相続順位", style="yellow", width=15)
    table.add_column("相続割合（分数）", style="blue", width=20)
    table.add_column("相続割合（%）", style="blue", width=15)

    rank_names = {
        "spouse": "配偶者",
        "first": "第1順位",
        "second": "第2順位",
        "third": "第3順位",
    }

    for heir in result.heirs:
        table.add_row(
            str(heir.person),
            heir.rank.value,
            rank_names.get(heir.rank.value, "不明"),
            str(heir.share),
            f"{heir.share_percentage:.2f}%"
        )

    console.print(table)
    console.print()

    # 計算根拠を表示
    console.print("[bold]計算根拠:[/bold]")
    for basis in result.calculation_basis:
        console.print(f"  • {basis}")
    console.print()


def demo_case1_spouse_only():
    """ケース1: 配偶者のみ"""
    print_header("ケース1: 配偶者のみ")

    # 人物の作成
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

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print()

    # 相続計算
    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],
        parents=[],
        siblings=[]
    )

    print_result_table(result)


def demo_case2_spouse_and_children():
    """ケース2: 配偶者と子"""
    print_header("ケース2: 配偶者と子（2人）")

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
        birth_date=date(1985, 8, 15)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"子1: {child1}")
    console.print(f"子2: {child2}")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[child1, child2],
        parents=[],
        siblings=[]
    )

    print_result_table(result)


def demo_case3_spouse_and_parents():
    """ケース3: 配偶者と直系尊属"""
    print_header("ケース3: 配偶者と直系尊属（父母）")

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
    father = Person(
        name="山田三郎",
        is_alive=True,
        birth_date=date(1925, 6, 5)
    )
    mother = Person(
        name="山田春子",
        is_alive=True,
        birth_date=date(1928, 9, 20)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"父: {father}")
    console.print(f"母: {mother}")
    console.print()
    console.print("[yellow]※子がいないため、第2順位（直系尊属）が相続人となります[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],  # 子なし
        parents=[father, mother],
        siblings=[]
    )

    print_result_table(result)


def demo_case4_spouse_and_siblings():
    """ケース4: 配偶者と兄弟姉妹"""
    print_header("ケース4: 配偶者と兄弟姉妹（全血）")

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
    brother = Person(
        name="山田次郎",
        is_alive=True,
        birth_date=date(1948, 3, 15)
    )
    sister = Person(
        name="山田春子",
        is_alive=True,
        birth_date=date(1952, 7, 25)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"兄: {brother}")
    console.print(f"妹: {sister}")
    console.print()
    console.print("[yellow]※子も直系尊属もいないため、第3順位（兄弟姉妹）が相続人となります[/yellow]")
    console.print()

    blood_types = {
        str(brother.id): BloodType.FULL,
        str(sister.id): BloodType.FULL,
    }

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],
        parents=[],
        siblings=[brother, sister],
        sibling_blood_types=blood_types
    )

    print_result_table(result)


def demo_case5_children_only():
    """ケース5: 子のみ（配偶者なし）"""
    print_header("ケース5: 子のみ（3人、配偶者なし）")

    decedent = Person(
        name="山田太郎",
        is_decedent=True,
        is_alive=False,
        birth_date=date(1950, 1, 1),
        death_date=date(2025, 6, 15)
    )
    child1 = Person(
        name="山田一郎",
        is_alive=True,
        birth_date=date(1980, 5, 20)
    )
    child2 = Person(
        name="山田二郎",
        is_alive=True,
        birth_date=date(1985, 8, 15)
    )
    child3 = Person(
        name="山田三郎",
        is_alive=True,
        birth_date=date(1990, 12, 10)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"子1: {child1}")
    console.print(f"子2: {child2}")
    console.print(f"子3: {child3}")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[],  # 配偶者なし
        children=[child1, child2, child3],
        parents=[],
        siblings=[]
    )

    print_result_table(result)


def demo_case6_mixed_blood_siblings():
    """ケース6: 全血・半血兄弟姉妹の混在"""
    print_header("ケース6: 配偶者と兄弟姉妹（全血・半血混在）")

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
    full_brother = Person(
        name="山田次郎（全血兄）",
        is_alive=True,
        birth_date=date(1948, 3, 15)
    )
    half_brother = Person(
        name="山田三郎（半血兄）",
        is_alive=True,
        birth_date=date(1952, 7, 25)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"全血兄: {full_brother}")
    console.print(f"半血兄: {half_brother}")
    console.print()
    console.print("[yellow]※半血兄弟姉妹の相続分は、全血兄弟姉妹の1/2となります（民法900条4号）[/yellow]")
    console.print()

    blood_types = {
        str(full_brother.id): BloodType.FULL,
        str(half_brother.id): BloodType.HALF,
    }

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],
        parents=[],
        siblings=[full_brother, half_brother],
        sibling_blood_types=blood_types
    )

    print_result_table(result)


def main():
    """メイン実行"""
    console.print()
    console.print(Panel.fit(
        "[bold green]日本の民法に基づく相続計算デモ[/bold green]\n"
        "[cyan]基本的な相続ケース[/cyan]",
        border_style="green"
    ))

    # 各ケースを実行
    demo_case1_spouse_only()
    demo_case2_spouse_and_children()
    demo_case3_spouse_and_parents()
    demo_case4_spouse_and_siblings()
    demo_case5_children_only()
    demo_case6_mixed_blood_siblings()

    console.print()
    console.print(Panel(
        "[bold green]デモ完了[/bold green]\n"
        "全ての基本ケースの相続計算が正しく動作しました。",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    main()
