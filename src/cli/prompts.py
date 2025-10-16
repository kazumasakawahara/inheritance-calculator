"""インタラクティブプロンプト

改善されたユーザー入力プロンプト機能を提供します。
保留（ペンディング）機能、入力確認、修正機能を含みます。
"""
from typing import Optional, List, Dict, Any, Callable
from datetime import date, datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pydantic import ValidationError

from src.cli.session import Session, SessionManager
from inheritance_calculator_core.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


class InteractivePrompt:
    """インタラクティブプロンプトクラス"""

    # 保留キーワード
    PENDING_KEYWORDS = ["pending", "保留", "未確定", "skip"]

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """初期化

        Args:
            session_manager: セッション管理マネージャー
        """
        self.session_manager = session_manager or SessionManager()
        self.session: Optional[Session] = None
        self.input_data: Dict[str, Any] = {}

    def prompt_text(
        self,
        prompt: str,
        key: str,
        default: Optional[str] = None,
        optional: bool = False,
        allow_pending: bool = True,
        validator: Optional[Callable[[str], bool]] = None
    ) -> Optional[str]:
        """テキスト入力プロンプト

        Args:
            prompt: プロンプトメッセージ
            key: 入力データのキー
            default: デフォルト値
            optional: オプショナル項目か
            allow_pending: 保留を許可するか
            validator: バリデーション関数

        Returns:
            str: 入力された値（保留の場合はNone）
        """
        # オプショナル表示
        if optional:
            prompt = f"{prompt} [cyan][オプション][/cyan]"

        # 保留許可の表示
        if allow_pending:
            prompt = f"{prompt} [dim](pending/保留/未確定 で保留可)[/dim]"

        while True:
            try:
                value = Prompt.ask(prompt, default=default or "")

                # 空入力でオプショナルの場合はNone
                if not value and optional:
                    return None

                # 保留キーワードチェック
                if allow_pending and value.lower() in self.PENDING_KEYWORDS:
                    if self.session:
                        self.session_manager.mark_pending(self.session, key, "未確定")
                    console.print("[yellow]→ 保留としてマークしました[/yellow]")
                    return None

                # バリデーション
                if validator and value:
                    if not validator(value):
                        console.print("[red]入力値が無効です。もう一度入力してください。[/red]")
                        continue

                return value

            except KeyboardInterrupt:
                console.print("\n[yellow]入力を中断しました[/yellow]")
                if self.session and Confirm.ask("セッションを保存しますか？"):
                    self.session_manager.save_session(self.session)
                    console.print(f"[green]セッション保存: {self.session.session_id}[/green]")
                raise

    def prompt_date(
        self,
        prompt: str,
        key: str,
        optional: bool = False,
        allow_pending: bool = True
    ) -> Optional[date]:
        """日付入力プロンプト

        Args:
            prompt: プロンプトメッセージ
            key: 入力データのキー
            optional: オプショナル項目か
            allow_pending: 保留を許可するか

        Returns:
            date: 入力された日付（保留の場合はNone）
        """
        prompt_text = f"{prompt} [dim](YYYY-MM-DD形式)[/dim]"

        def date_validator(value: str) -> bool:
            """日付バリデーター"""
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                console.print("[red]日付形式が正しくありません。YYYY-MM-DD形式で入力してください（例: 2025-06-15）[/red]")
                return False

        date_str = self.prompt_text(
            prompt_text,
            key,
            optional=optional,
            allow_pending=allow_pending,
            validator=date_validator
        )

        if date_str is None:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def prompt_bool(
        self,
        prompt: str,
        key: str,
        default: bool = False,
        allow_pending: bool = True
    ) -> Optional[bool]:
        """Yes/No入力プロンプト

        Args:
            prompt: プロンプトメッセージ
            key: 入力データのキー
            default: デフォルト値
            allow_pending: 保留を許可するか

        Returns:
            bool: 入力された値（保留の場合はNone）
        """
        if allow_pending:
            prompt = f"{prompt} [dim](pending/保留 で保留可)[/dim]"

        while True:
            try:
                value = Prompt.ask(
                    prompt,
                    choices=["y", "n", "yes", "no", "はい", "いいえ", "pending", "保留", "未確定"],
                    default="y" if default else "n"
                )

                # 保留チェック
                if allow_pending and value.lower() in self.PENDING_KEYWORDS:
                    if self.session:
                        self.session_manager.mark_pending(self.session, key, "未確定")
                    console.print("[yellow]→ 保留としてマークしました[/yellow]")
                    return None

                # Yes/No判定
                return value.lower() in ["y", "yes", "はい"]

            except KeyboardInterrupt:
                console.print("\n[yellow]入力を中断しました[/yellow]")
                if self.session and Confirm.ask("セッションを保存しますか？"):
                    self.session_manager.save_session(self.session)
                raise

    def prompt_int(
        self,
        prompt: str,
        key: str,
        default: Optional[int] = None,
        optional: bool = False,
        allow_pending: bool = True,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> Optional[int]:
        """整数入力プロンプト

        Args:
            prompt: プロンプトメッセージ
            key: 入力データのキー
            default: デフォルト値
            optional: オプショナル項目か
            allow_pending: 保留を許可するか
            min_value: 最小値
            max_value: 最大値

        Returns:
            int: 入力された値（保留の場合はNone）
        """
        def int_validator(value: str) -> bool:
            """整数バリデーター"""
            try:
                num = int(value)
                if min_value is not None and num < min_value:
                    console.print(f"[red]{min_value}以上の値を入力してください[/red]")
                    return False
                if max_value is not None and num > max_value:
                    console.print(f"[red]{max_value}以下の値を入力してください[/red]")
                    return False
                return True
            except ValueError:
                console.print("[red]整数を入力してください[/red]")
                return False

        value_str = self.prompt_text(
            prompt,
            key,
            default=str(default) if default is not None else None,
            optional=optional,
            allow_pending=allow_pending,
            validator=int_validator
        )

        if value_str is None:
            return None

        try:
            return int(value_str)
        except ValueError:
            return None

    def confirm_inputs(self, data: Dict[str, Any]) -> bool:
        """入力内容の確認と修正

        Args:
            data: 入力データ

        Returns:
            bool: 確定した場合True
        """
        while True:
            # 確認テーブルの表示
            table = Table(title="入力内容確認", show_header=True)
            table.add_column("No", style="cyan", width=5)
            table.add_column("項目", style="green", width=25)
            table.add_column("入力値", style="white", width=40)

            items = list(data.items())
            for idx, (key, value) in enumerate(items, 1):
                # 保留項目のハイライト
                if self.session and key in self.session.pending_items:
                    value_str = f"[yellow]未確定（保留）[/yellow]"
                elif value is None:
                    value_str = "[dim]（未入力）[/dim]"
                else:
                    value_str = str(value)

                table.add_row(str(idx), key, value_str)

            console.print()
            console.print(table)
            console.print()

            # 確認プロンプト
            choice = Prompt.ask(
                "修正する項目の番号を入力してください（Enterで確定）",
                default=""
            )

            if not choice:
                return True

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    key = items[idx][0]
                    console.print(f"\n[cyan]【{key}】を再入力してください[/cyan]")
                    # 再入力の実装は呼び出し側で行う
                    return False
                else:
                    console.print("[red]無効な番号です[/red]")
            except ValueError:
                console.print("[red]数字を入力してください[/red]")

    def display_pending_items(self) -> None:
        """保留項目の表示"""
        if not self.session or not self.session_manager.has_pending_items(self.session):
            return

        pending = self.session_manager.get_pending_items(self.session)

        console.print()
        console.print(Panel.fit(
            "[yellow]保留項目があります[/yellow]",
            border_style="yellow"
        ))

        table = Table(show_header=True)
        table.add_column("項目", style="yellow")
        table.add_column("状態", style="cyan")

        for key, value in pending.items():
            table.add_row(key, value)

        console.print(table)
        console.print()

    def prompt_update_pending(self) -> bool:
        """保留項目の更新確認

        Returns:
            bool: 更新する場合True
        """
        if not self.session or not self.session_manager.has_pending_items(self.session):
            return False

        self.display_pending_items()

        return Confirm.ask("保留項目を更新しますか？", default=True)

    def create_session(self, data: Optional[Dict[str, Any]] = None) -> Session:
        """新しいセッションを作成

        Args:
            data: 初期データ

        Returns:
            Session: 作成されたセッション
        """
        self.session = self.session_manager.create_session(data)
        logger.info(f"新しいセッション作成: {self.session.session_id}")
        return self.session

    def load_session(self, session_id: str) -> Optional[Session]:
        """セッションを読み込み

        Args:
            session_id: セッションID

        Returns:
            Session: 読み込まれたセッション（存在しない場合None）
        """
        self.session = self.session_manager.load_session(session_id)
        if self.session:
            logger.info(f"セッション読み込み: {session_id}")
        return self.session

    def save_current_session(self) -> None:
        """現在のセッションを保存"""
        if self.session:
            self.session_manager.save_session(self.session)
            logger.info(f"セッション保存: {self.session.session_id}")
