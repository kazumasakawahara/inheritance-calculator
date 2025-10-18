"""連絡先入力機能

相続人確定後の連絡先情報（住所、電話番号、メール）入力機能を提供します。
"""
from inheritance_calculator_core.models.inheritance import InheritanceResult
from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from src.cli.prompts import InteractivePrompt

logger = get_logger(__name__)
console = Console()


class ContactInfoCollector:
    """連絡先情報収集クラス"""

    def __init__(self) -> None:
        """初期化"""
        self.prompt = InteractivePrompt()

    def collect_contact_info_for_heirs(self, result: InheritanceResult) -> list[Person]:
        """相続人の連絡先情報を収集

        Args:
            result: 相続計算結果

        Returns:
            List[Person]: 連絡先情報が更新された相続人リスト
        """
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]相続人の連絡先情報入力[/bold cyan]", border_style="cyan"
            )
        )
        console.print()

        # 連絡先入力の確認
        if not Confirm.ask("相続人の連絡先情報を入力しますか？", default=True):
            console.print("[dim]連絡先情報の入力をスキップしました[/dim]")
            return []

        updated_persons = []

        for heir in result.heirs:
            console.print()
            console.print(
                f"[bold green]【{heir.person.name}】の連絡先情報[/bold green]"
            )
            console.print()

            # 住所
            address = self.prompt.prompt_text(
                "住所",
                key=f"address_{heir.person.name}",
                optional=True,
                allow_pending=False,
            )

            # 電話番号
            phone = self.prompt.prompt_text(
                "電話番号",
                key=f"phone_{heir.person.name}",
                optional=True,
                allow_pending=False,
                validator=self._validate_phone,
            )

            # メールアドレス
            email = self.prompt_email(heir.person.name)

            # 連絡先情報を設定
            if address or phone or email:
                heir.person.set_contact_info(address=address, phone=phone, email=email)
                updated_persons.append(heir.person)
                console.print("[green]✓ 連絡先情報を登録しました[/green]")
            else:
                console.print("[dim]連絡先情報の入力をスキップしました[/dim]")

        if updated_persons:
            console.print()
            console.print(
                f"[bold green]✓ {len(updated_persons)}名の連絡先情報を"
                "登録しました[/bold green]"
            )

        return updated_persons

    def prompt_email(self, person_name: str) -> str | None:
        """メールアドレス入力プロンプト（バリデーション付き）

        Args:
            person_name: 人物名

        Returns:
            str: メールアドレス（スキップの場合None）
        """
        while True:
            email = self.prompt.prompt_text(
                "メールアドレス",
                key=f"email_{person_name}",
                optional=True,
                allow_pending=False,
            )

            if email is None:
                return None

            # メールアドレスのバリデーション
            if self._validate_email(email):
                return str(email)  # 型を明示的に変換
            else:
                console.print(
                    "[red]メールアドレスの形式が正しくありません"
                    "（例: example@example.com）[/red]"
                )

    def _validate_email(self, email: str) -> bool:
        """メールアドレスバリデーション

        Args:
            email: メールアドレス

        Returns:
            bool: 有効な場合True
        """
        # 簡易的な検証（@と.が含まれているか）
        if not email:
            return True  # 空は許可

        # @で分割してユーザー名とドメインを取得
        if "@" not in email:
            return False

        parts = email.split("@")
        if len(parts) != 2:
            return False

        username, domain = parts

        # ユーザー名とドメインが空でないこと
        if not username or not domain:
            return False

        # ドメインに.が含まれること
        return "." in domain

    def _validate_phone(self, phone: str) -> bool:
        """電話番号バリデーション（柔軟な検証）

        Args:
            phone: 電話番号

        Returns:
            bool: 有効な場合True
        """
        if not phone:
            return True  # 空は許可

        # 数字、ハイフン、+、括弧、スペースのみ許可
        allowed_chars = "0123456789-+() "
        return all(c in allowed_chars for c in phone)

    def display_contact_summary(self, persons: list[Person]) -> None:
        """連絡先情報のサマリー表示

        Args:
            persons: 連絡先情報を持つ人物リスト
        """
        from rich.table import Table

        if not persons:
            return

        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]登録された連絡先情報[/bold cyan]", border_style="cyan"
            )
        )
        console.print()

        table = Table(show_header=True)
        table.add_column("氏名", style="cyan", width=20)
        table.add_column("住所", style="green", width=30)
        table.add_column("電話番号", style="yellow", width=15)
        table.add_column("メールアドレス", style="blue", width=25)

        for person in persons:
            table.add_row(
                person.name,
                person.address or "-",
                person.phone or "-",
                person.email or "-",
            )

        console.print(table)
        console.print()

    def collect_single_contact_info(self, person: Person) -> Person:
        """単一の人物の連絡先情報を収集

        Args:
            person: 人物

        Returns:
            Person: 連絡先情報が更新された人物
        """
        console.print()
        console.print(f"[bold green]【{person.name}】の連絡先情報[/bold green]")
        console.print()

        # 住所
        address = self.prompt.prompt_text(
            "住所", key=f"address_{person.name}", optional=True, allow_pending=False
        )

        # 電話番号
        phone = self.prompt.prompt_text(
            "電話番号",
            key=f"phone_{person.name}",
            optional=True,
            allow_pending=False,
            validator=self._validate_phone,
        )

        # メールアドレス
        email = self.prompt_email(person.name)

        # 連絡先情報を設定
        if address or phone or email:
            person.set_contact_info(address=address, phone=phone, email=email)
            console.print("[green]✓ 連絡先情報を登録しました[/green]")

        return person
