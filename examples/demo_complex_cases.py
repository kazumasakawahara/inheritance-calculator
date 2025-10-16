"""複雑な相続ケースのデモ

代襲相続、相続放棄、混合ケースなど、複雑な相続シナリオを実演します。
"""
from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.models.relationship import BloodType
from inheritance_calculator_core.services.inheritance_calculator import InheritanceCalculator


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


def demo_case1_child_substitution():
    """ケース1: 子の代襲相続"""
    print_header("ケース1: 子の代襲相続（無制限の代襲）")

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
    child2_deceased = Person(
        name="山田二郎（先に死亡）",
        is_alive=False,
        birth_date=date(1985, 8, 15),
        death_date=date(2020, 3, 10)
    )
    grandchild1 = Person(
        name="山田三郎（二郎の子）",
        is_alive=True,
        birth_date=date(2010, 4, 1)
    )
    grandchild2 = Person(
        name="山田四郎（二郎の子）",
        is_alive=True,
        birth_date=date(2015, 7, 15)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"子1: {child1}")
    console.print(f"[red]子2（先に死亡）: {child2_deceased}[/red]")
    console.print(f"孫1（代襲相続人）: {grandchild1}")
    console.print(f"孫2（代襲相続人）: {grandchild2}")
    console.print()
    console.print("[yellow]※子が被相続人より先に死亡した場合、その子（被相続人の孫）が代襲相続します[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    # 代襲相続のシミュレーション: child2が先に死亡したため、その子が代襲
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[child1, grandchild1, grandchild2],  # 孫を子として扱う
        parents=[],
        siblings=[]
    )

    print_result_table(result)


def demo_case2_sibling_substitution():
    """ケース2: 兄弟姉妹の代襲相続（1代限り）"""
    print_header("ケース2: 兄弟姉妹の代襲相続（1代限り）")

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
    brother_deceased = Person(
        name="山田次郎（先に死亡）",
        is_alive=False,
        birth_date=date(1948, 3, 15),
        death_date=date(2020, 5, 20)
    )
    sister = Person(
        name="山田春子",
        is_alive=True,
        birth_date=date(1952, 7, 25)
    )
    nephew = Person(
        name="山田五郎（次郎の子）",
        is_alive=True,
        birth_date=date(1975, 10, 10)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"[red]兄（先に死亡）: {brother_deceased}[/red]")
    console.print(f"妹: {sister}")
    console.print(f"甥（代襲相続人）: {nephew}")
    console.print()
    console.print("[yellow]※子も直系尊属もいないため、兄弟姉妹が相続人となります[/yellow]")
    console.print("[yellow]※兄が先に死亡したため、その子（甥）が代襲相続します（1代限り）[/yellow]")
    console.print()

    blood_types = {
        str(sister.id): BloodType.FULL,
        str(nephew.id): BloodType.FULL,  # 兄の代襲として全血扱い
    }

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],
        parents=[],
        siblings=[sister, nephew],  # 甥を兄弟姉妹として扱う
        sibling_blood_types=blood_types
    )

    print_result_table(result)


def demo_case3_renunciation():
    """ケース3: 相続放棄"""
    print_header("ケース3: 相続放棄（次順位への移行）")

    decedent = Person(
        name="山田太郎",
        is_decedent=True,
        is_alive=False,
        birth_date=date(1950, 1, 1),
        death_date=date(2025, 6, 15)
    )
    child1_renounced = Person(
        name="山田一郎（放棄）",
        is_alive=True,
        birth_date=date(1980, 5, 20)
    )
    child2_renounced = Person(
        name="山田二郎（放棄）",
        is_alive=True,
        birth_date=date(1985, 8, 15)
    )
    father = Person(
        name="山田三郎（父）",
        is_alive=True,
        birth_date=date(1925, 6, 5)
    )
    mother = Person(
        name="山田春子（母）",
        is_alive=True,
        birth_date=date(1928, 9, 20)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"[red]子1（相続放棄）: {child1_renounced}[/red]")
    console.print(f"[red]子2（相続放棄）: {child2_renounced}[/red]")
    console.print(f"父: {father}")
    console.print(f"母: {mother}")
    console.print()
    console.print("[yellow]※全ての子が相続放棄した場合、第2順位（直系尊属）が相続人となります[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[],
        children=[],  # 放棄したので子はいない扱い
        parents=[father, mother],  # 第2順位が相続
        siblings=[],
        renounced=[child1_renounced, child2_renounced]
    )

    print_result_table(result)


def demo_case4_mixed_renunciation():
    """ケース4: 一部相続放棄（同順位内）"""
    print_header("ケース4: 一部相続放棄（同順位内）")

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
    child2_renounced = Person(
        name="山田二郎（放棄）",
        is_alive=True,
        birth_date=date(1985, 8, 15)
    )
    child3 = Person(
        name="山田三郎",
        is_alive=True,
        birth_date=date(1990, 12, 10)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"子1: {child1}")
    console.print(f"[red]子2（相続放棄）: {child2_renounced}[/red]")
    console.print(f"子3: {child3}")
    console.print()
    console.print("[yellow]※1人が放棄しても、他の子がいるため第1順位内で分割されます[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[child1, child3],  # child2は放棄したので除外
        parents=[],
        siblings=[],
        renounced=[child2_renounced]
    )

    print_result_table(result)


def demo_case5_complex_mixed():
    """ケース5: 複雑な混合ケース（代襲+半血）"""
    print_header("ケース5: 複雑な混合ケース（代襲相続+半血兄弟姉妹）")

    decedent = Person(
        name="山田太郎",
        is_decedent=True,
        is_alive=False,
        birth_date=date(1950, 1, 1),
        death_date=date(2025, 6, 15)
    )
    child1_deceased = Person(
        name="山田一郎（先に死亡）",
        is_alive=False,
        birth_date=date(1980, 5, 20),
        death_date=date(2020, 3, 10)
    )
    grandchild = Person(
        name="山田五郎（一郎の子）",
        is_alive=True,
        birth_date=date(2005, 8, 15)
    )
    child2 = Person(
        name="山田二郎",
        is_alive=True,
        birth_date=date(1985, 8, 15)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"[red]子1（先に死亡）: {child1_deceased}[/red]")
    console.print(f"孫（代襲相続人）: {grandchild}")
    console.print(f"子2: {child2}")
    console.print()
    console.print("[yellow]※子1が先に死亡したため、その子（孫）が代襲相続します[/yellow]")
    console.print("[yellow]※代襲相続人は被代襲者の相続分を承継します[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[],
        children=[grandchild, child2],  # 孫は代襲として子扱い
        parents=[],
        siblings=[]
    )

    print_result_table(result)


def demo_case6_spouse_only_after_renunciation():
    """ケース6: 配偶者のみ（他全員放棄）"""
    print_header("ケース6: 配偶者のみ（全相続人が放棄）")

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
    child1_renounced = Person(
        name="山田一郎（放棄）",
        is_alive=True,
        birth_date=date(1980, 5, 20)
    )
    child2_renounced = Person(
        name="山田二郎（放棄）",
        is_alive=True,
        birth_date=date(1985, 8, 15)
    )

    console.print(f"被相続人: {decedent}")
    console.print(f"配偶者: {spouse}")
    console.print(f"[red]子1（相続放棄）: {child1_renounced}[/red]")
    console.print(f"[red]子2（相続放棄）: {child2_renounced}[/red]")
    console.print()
    console.print("[yellow]※全ての子が相続放棄し、他の相続人もいない場合、配偶者が全部相続します[/yellow]")
    console.print()

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[],  # 全員放棄
        parents=[],
        siblings=[],
        renounced=[child1_renounced, child2_renounced]
    )

    print_result_table(result)


def main():
    """メイン実行"""
    console.print()
    console.print(Panel.fit(
        "[bold green]日本の民法に基づく相続計算デモ[/bold green]\n"
        "[cyan]複雑な相続ケース[/cyan]",
        border_style="green"
    ))

    # 各ケースを実行
    demo_case1_child_substitution()
    demo_case2_sibling_substitution()
    demo_case3_renunciation()
    demo_case4_mixed_renunciation()
    demo_case5_complex_mixed()
    demo_case6_spouse_only_after_renunciation()

    console.print()
    console.print(Panel(
        "[bold green]デモ完了[/bold green]\n"
        "複雑な相続ケースの計算が正しく動作しました。",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    main()
