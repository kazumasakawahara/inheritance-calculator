"""対話型相続計算デモ

ユーザーとの対話を通じて相続情報を収集し、相続計算を行います。
"""
from datetime import date, datetime
from typing import List, Optional, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.models.relationship import BloodType
from inheritance_calculator_core.services.inheritance_calculator import InheritanceCalculator


console = Console()


def parse_date(date_str: str) -> Optional[date]:
    """日付文字列をdateオブジェクトに変換"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        console.print("[red]無効な日付形式です。YYYY-MM-DD形式で入力してください。[/red]")
        return None


def input_person(role: str, is_decedent: bool = False) -> Optional[Person]:
    """人物情報を入力"""
    console.print()
    console.print(f"[bold cyan]{role}の情報を入力してください[/bold cyan]")

    name = Prompt.ask("氏名")

    birth_date = None
    birth_date_str = Prompt.ask("生年月日 (YYYY-MM-DD)", default="")
    if birth_date_str:
        birth_date = parse_date(birth_date_str)
        if birth_date is None:
            return None

    is_alive = True
    death_date = None

    if is_decedent:
        is_alive = False
        death_date_str = Prompt.ask("死亡日 (YYYY-MM-DD)")
        death_date = parse_date(death_date_str)
        if death_date is None:
            return None
    else:
        is_alive = Confirm.ask("存命ですか？", default=True)
        if not is_alive:
            death_date_str = Prompt.ask("死亡日 (YYYY-MM-DD)")
            death_date = parse_date(death_date_str)
            if death_date is None:
                return None

    return Person(
        name=name,
        is_alive=is_alive,
        birth_date=birth_date,
        death_date=death_date,
        is_decedent=is_decedent
    )


def input_multiple_persons(role: str) -> List[Person]:
    """複数の人物情報を入力"""
    persons = []

    has_persons = Confirm.ask(f"{role}はいますか？", default=False)
    if not has_persons:
        return persons

    count = int(Prompt.ask(f"{role}の人数", default="1"))

    for i in range(count):
        console.print(f"\n[bold]{i+1}人目の{role}[/bold]")
        person = input_person(f"{role} {i+1}")
        if person:
            persons.append(person)

    return persons


def input_blood_types(siblings: List[Person]) -> Dict[str, BloodType]:
    """兄弟姉妹の血縁タイプを入力"""
    blood_types = {}

    if not siblings:
        return blood_types

    console.print()
    console.print("[bold cyan]兄弟姉妹の血縁タイプを指定してください[/bold cyan]")
    console.print("[yellow]全血: 父母が同じ / 半血: 父または母のみが同じ[/yellow]")
    console.print()

    for sibling in siblings:
        blood_type_str = Prompt.ask(
            f"{sibling.name}の血縁タイプ",
            choices=["full", "half"],
            default="full"
        )
        blood_types[str(sibling.id)] = BloodType.FULL if blood_type_str == "full" else BloodType.HALF

    return blood_types


def display_result(result) -> None:
    """計算結果を表示"""
    console.print()
    console.print(Panel.fit(
        "[bold green]相続計算結果[/bold green]",
        border_style="green"
    ))
    console.print()

    # 相続人一覧テーブル
    table = Table(title="相続人と相続割合", show_header=True, header_style="bold magenta")
    table.add_column("氏名", style="cyan", width=25)
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

    # 計算根拠
    console.print("[bold]計算根拠:[/bold]")
    for basis in result.calculation_basis:
        console.print(f"  • {basis}")
    console.print()

    # サマリー情報
    console.print("[bold]サマリー:[/bold]")
    console.print(f"  • 相続人総数: {result.total_heirs}名")
    console.print(f"  • 配偶者: {'あり' if result.has_spouse else 'なし'}")
    console.print(f"  • 子: {'あり' if result.has_children else 'なし'}")
    console.print(f"  • 直系尊属: {'あり' if result.has_parents else 'なし'}")
    console.print(f"  • 兄弟姉妹: {'あり' if result.has_siblings else 'なし'}")
    console.print()


def main():
    """メイン実行"""
    console.print()
    console.print(Panel.fit(
        "[bold green]相続人・相続割合確定システム[/bold green]\n"
        "[cyan]対話型インターフェース[/cyan]",
        border_style="green"
    ))
    console.print()

    # 被相続人の入力
    console.print("[bold yellow]被相続人（故人）の情報[/bold yellow]")
    decedent = input_person("被相続人", is_decedent=True)
    if not decedent:
        console.print("[red]被相続人の情報入力に失敗しました。[/red]")
        return

    # 配偶者の入力
    console.print()
    console.print("[bold yellow]配偶者の情報[/bold yellow]")
    spouses = input_multiple_persons("配偶者")

    # 子の入力
    console.print()
    console.print("[bold yellow]子の情報[/bold yellow]")
    children = input_multiple_persons("子")

    # 先に死亡した子がいるか確認（代襲相続の可能性）
    if children:
        deceased_children = [c for c in children if not c.is_alive and c.death_date and c.death_date < decedent.death_date]
        if deceased_children:
            console.print()
            console.print("[yellow]※被相続人より先に死亡した子がいます。代襲相続の可能性があります。[/yellow]")
            for deceased_child in deceased_children:
                has_grandchildren = Confirm.ask(f"{deceased_child.name}に子（被相続人の孫）はいますか？")
                if has_grandchildren:
                    grandchildren = input_multiple_persons(f"{deceased_child.name}の子（代襲相続人）")
                    children.extend(grandchildren)

    # 直系尊属の入力（子がいない場合のみ）
    parents = []
    if not children:
        console.print()
        console.print("[bold yellow]直系尊属（父母・祖父母）の情報[/bold yellow]")
        console.print("[yellow]※子がいないため、第2順位として直系尊属を確認します[/yellow]")
        parents = input_multiple_persons("直系尊属")

    # 兄弟姉妹の入力（子も直系尊属もいない場合のみ）
    siblings = []
    sibling_blood_types = {}
    if not children and not parents:
        console.print()
        console.print("[bold yellow]兄弟姉妹の情報[/bold yellow]")
        console.print("[yellow]※子も直系尊属もいないため、第3順位として兄弟姉妹を確認します[/yellow]")
        siblings = input_multiple_persons("兄弟姉妹")

        if siblings:
            # 先に死亡した兄弟姉妹がいるか確認（代襲相続の可能性）
            deceased_siblings = [s for s in siblings if not s.is_alive and s.death_date and s.death_date < decedent.death_date]
            if deceased_siblings:
                console.print()
                console.print("[yellow]※被相続人より先に死亡した兄弟姉妹がいます。代襲相続の可能性があります（1代限り）。[/yellow]")
                for deceased_sibling in deceased_siblings:
                    has_nephews = Confirm.ask(f"{deceased_sibling.name}に子（被相続人の甥・姪）はいますか？")
                    if has_nephews:
                        nephews = input_multiple_persons(f"{deceased_sibling.name}の子（代襲相続人）")
                        siblings.extend(nephews)

            # 血縁タイプの入力
            sibling_blood_types = input_blood_types(siblings)

    # 相続放棄の確認
    console.print()
    has_renunciation = Confirm.ask("相続放棄をした人はいますか？", default=False)
    renounced = []
    if has_renunciation:
        console.print("[yellow]相続放棄した人の氏名をカンマ区切りで入力してください[/yellow]")
        renounced_names = Prompt.ask("氏名").split(",")
        all_persons = spouses + children + parents + siblings
        for name in renounced_names:
            name = name.strip()
            person = next((p for p in all_persons if p.name == name), None)
            if person:
                renounced.append(person)

    # 相続計算の実行
    console.print()
    console.print("[bold cyan]相続計算を実行しています...[/bold cyan]")

    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=spouses,
        children=children,
        parents=parents,
        siblings=siblings,
        renounced=renounced if renounced else None,
        sibling_blood_types=sibling_blood_types if sibling_blood_types else None
    )

    # 結果の表示
    display_result(result)

    # 終了メッセージ
    console.print(Panel(
        "[bold green]計算完了[/bold green]\n"
        "相続計算が正常に完了しました。",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    main()
