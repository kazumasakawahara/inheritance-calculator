"""CLI表示ユーティリティ

Rich libraryを使った美しい表示機能を提供します。
"""
from typing import List, Optional, Callable, Any
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)

from src.models.inheritance import InheritanceResult, HeritageRank


console = Console()


def display_result(result: InheritanceResult, show_visual: bool = True) -> None:
    """相続計算結果を表示

    Args:
        result: 相続計算結果
        show_visual: 視覚的表示を含めるか
    """
    console.print()
    console.print(Panel.fit(
        "[bold green]相続計算結果[/bold green]",
        border_style="green"
    ))
    console.print()

    # 相続人一覧テーブル（視覚的な割合表示を追加）
    table = Table(title="相続人と相続割合", show_header=True, header_style="bold magenta")
    table.add_column("氏名", style="cyan", width=20)
    table.add_column("続柄", style="green", width=12)
    table.add_column("相続順位", style="yellow", width=12)
    table.add_column("相続割合", style="blue", width=15)
    table.add_column("割合(%)", style="blue", width=10)
    if show_visual:
        table.add_column("視覚表示", style="white", width=30)

    rank_names = {
        "spouse": "配偶者",
        "first": "第1順位",
        "second": "第2順位",
        "third": "第3順位",
    }

    rank_colors = {
        "spouse": "green",
        "first": "blue",
        "second": "yellow",
        "third": "magenta"
    }

    for heir in result.heirs:
        row_data = [
            str(heir.person.name),
            heir.rank.value,
            rank_names.get(heir.rank.value, "不明"),
            str(heir.share),
            f"{heir.share_percentage:.2f}%"
        ]

        if show_visual:
            # 視覚的なバー表示
            bar_length = int(heir.share_percentage / 100 * 20)
            bar_color = rank_colors.get(heir.rank.value, "white")
            bar = f"[{bar_color}]{'━' * bar_length}[/{bar_color}]"
            row_data.append(bar)

        table.add_row(*row_data)

    console.print(table)
    console.print()

    # 計算根拠
    console.print("[bold]計算根拠:[/bold]")
    for basis in result.calculation_basis:
        console.print(f"  • {basis}")
    console.print()

    # サマリー情報（アイコン付き）
    console.print(Panel(
        f"👤 [bold]被相続人:[/bold] {result.decedent}\n"
        f"👨‍👩‍👧‍👦 [bold]相続人総数:[/bold] {result.total_heirs}名\n"
        f"💑 [bold]配偶者:[/bold] {'あり' if result.has_spouse else 'なし'}\n"
        f"👶 [bold]子:[/bold] {'あり' if result.has_children else 'なし'}\n"
        f"👴 [bold]直系尊属:[/bold] {'あり' if result.has_parents else 'なし'}\n"
        f"👫 [bold]兄弟姉妹:[/bold] {'あり' if result.has_siblings else 'なし'}",
        title="[bold cyan]計算サマリー[/bold cyan]",
        border_style="cyan"
    ))
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


@contextmanager
def progress_context(description: str = "処理中..."):
    """プログレス表示のコンテキストマネージャー

    使用例:
        with progress_context("データ保存中") as progress:
            task = progress.add_task(description, total=100)
            for i in range(100):
                # 処理
                progress.update(task, advance=1)

    Args:
        description: 初期表示メッセージ

    Yields:
        Progress: Richのプログレスオブジェクト
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    )

    with progress:
        yield progress


def display_spinner(description: str = "処理中..."):
    """スピナー表示のコンテキストマネージャー（進捗不明な処理用）

    使用例:
        with display_spinner("接続中..."):
            # 長時間処理
            time.sleep(5)

    Args:
        description: 表示メッセージ

    Returns:
        Progress: Richのプログレスオブジェクト
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )

    task_id = progress.add_task(description, total=None)
    return progress


@contextmanager
def progress_bar(description: str, total: int):
    """プログレスバー表示のコンテキストマネージャー（シンプル版）

    使用例:
        with progress_bar("ファイル処理中", total=100) as update:
            for i in range(100):
                # 処理
                update(1)  # 1単位進める

    Args:
        description: 表示メッセージ
        total: 総処理数

    Yields:
        Callable: 進捗を更新する関数
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task(description, total=total)

        def update(advance: int = 1):
            """進捗を更新"""
            progress.update(task, advance=advance)

        yield update


def display_multi_step_progress(steps: List[str]):
    """複数ステップのプログレス表示

    使用例:
        steps = ["データ検証", "Neo4j接続", "ノード作成", "リレーション作成"]
        with display_multi_step_progress(steps) as update_step:
            for step in steps:
                # 各ステップの処理
                update_step(step)

    Args:
        steps: ステップ名のリスト

    Returns:
        Progress: Richのプログレスオブジェクト
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

    task_id = progress.add_task("処理中...", total=len(steps))

    @contextmanager
    def progress_manager():
        with progress:
            def update_step(step_name: str):
                """ステップを更新"""
                progress.update(task_id, description=f"[cyan]{step_name}[/cyan]", advance=1)

            yield update_step

    return progress_manager()


def display_file_progress(description: str, total_files: int):
    """ファイル処理のプログレス表示

    Args:
        description: 表示メッセージ
        total_files: 総ファイル数

    Returns:
        tuple: (Progress object, update function)
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    )

    task = progress.add_task(description, total=total_files)

    @contextmanager
    def progress_manager():
        with progress:
            def update(filename: str = "", advance: int = 1):
                """ファイル処理進捗を更新

                Args:
                    filename: 処理中のファイル名
                    advance: 進捗量
                """
                if filename:
                    progress.update(task, description=f"{description}: [yellow]{filename}[/yellow]", advance=advance)
                else:
                    progress.update(task, advance=advance)

            yield update

    return progress_manager()
