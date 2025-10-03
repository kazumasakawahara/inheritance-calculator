"""CLI表示ユーティリティ

Rich libraryを使った美しい表示機能を提供します。
"""
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from src.models.inheritance import InheritanceResult, HeritageRank


console = Console()


def display_result(result: InheritanceResult) -> None:
    """相続計算結果を表示

    Args:
        result: 相続計算結果
    """
    console.print()
    console.print(Panel.fit(
        "[bold green]相続計算結果[/bold green]",
        border_style="green"
    ))
    console.print()

    # 相続人一覧テーブル
    table = Table(title="相続人と相続割合", show_header=True, header_style="bold magenta")
    table.add_column("氏名", style="cyan", width=30)
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
    console.print(f"  • 被相続人: {result.decedent}")
    console.print(f"  • 相続人総数: {result.total_heirs}名")
    console.print(f"  • 配偶者: {'あり' if result.has_spouse else 'なし'}")
    console.print(f"  • 子: {'あり' if result.has_children else 'なし'}")
    console.print(f"  • 直系尊属: {'あり' if result.has_parents else 'なし'}")
    console.print(f"  • 兄弟姉妹: {'あり' if result.has_siblings else 'なし'}")
    console.print()


def display_family_tree(result: InheritanceResult) -> None:
    """家系図を表示（簡易版）

    Args:
        result: 相続計算結果
    """
    tree = Tree(f"👤 {result.decedent}")

    # 配偶者
    if result.has_spouse:
        spouse_heirs = result.get_heirs_by_rank(HeritageRank.SPOUSE)
        for heir in spouse_heirs:
            tree.add(f"💑 配偶者: {heir.person} ({heir.share})")

    # 子
    if result.has_children:
        child_branch = tree.add("👶 子")
        child_heirs = result.get_heirs_by_rank(HeritageRank.FIRST)
        for heir in child_heirs:
            child_branch.add(f"{heir.person} ({heir.share})")

    # 直系尊属
    if result.has_parents:
        parent_branch = tree.add("👴 直系尊属")
        parent_heirs = result.get_heirs_by_rank(HeritageRank.SECOND)
        for heir in parent_heirs:
            parent_branch.add(f"{heir.person} ({heir.share})")

    # 兄弟姉妹
    if result.has_siblings:
        sibling_branch = tree.add("👫 兄弟姉妹")
        sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
        for heir in sibling_heirs:
            sibling_branch.add(f"{heir.person} ({heir.share})")

    console.print()
    console.print(Panel.fit("[bold cyan]家系図[/bold cyan]", border_style="cyan"))
    console.print()
    console.print(tree)
    console.print()


def display_error(message: str) -> None:
    """エラーメッセージを表示

    Args:
        message: エラーメッセージ
    """
    console.print(f"[bold red]エラー:[/bold red] {message}")


def display_warning(message: str) -> None:
    """警告メッセージを表示

    Args:
        message: 警告メッセージ
    """
    console.print(f"[bold yellow]警告:[/bold yellow] {message}")


def display_info(message: str) -> None:
    """情報メッセージを表示

    Args:
        message: 情報メッセージ
    """
    console.print(f"[bold cyan]情報:[/bold cyan] {message}")


def display_success(message: str) -> None:
    """成功メッセージを表示

    Args:
        message: 成功メッセージ
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def display_header(title: str, subtitle: str = "") -> None:
    """ヘッダーを表示

    Args:
        title: タイトル
        subtitle: サブタイトル（オプション）
    """
    if subtitle:
        text = f"[bold green]{title}[/bold green]\n[cyan]{subtitle}[/cyan]"
    else:
        text = f"[bold green]{title}[/bold green]"

    console.print()
    console.print(Panel.fit(text, border_style="green"))
    console.print()


def display_completion(message: str = "処理が完了しました") -> None:
    """完了メッセージを表示

    Args:
        message: 完了メッセージ
    """
    console.print()
    console.print(Panel(
        f"[bold green]{message}[/bold green]",
        border_style="green"
    ))
    console.print()
