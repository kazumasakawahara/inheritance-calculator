"""相続情報収集インタビューエージェント

AIを使って対話形式で相続情報を収集するエージェント。
"""
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from enum import Enum
import logging
import re

from .ollama_client import OllamaClient
from .prompts import InheritancePrompts
from ..models.person import Person, Gender
from ..models.relationship import BloodType


class InterviewState(str, Enum):
    """インタビューの状態"""
    INIT = "init"
    DECEDENT_INFO = "decedent_info"
    SPOUSE_INFO = "spouse_info"
    CHILDREN_INFO = "children_info"
    PARENTS_INFO = "parents_info"
    SIBLINGS_INFO = "siblings_info"
    SPECIAL_CASES = "special_cases"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class InterviewAgent:
    """
    対話型相続情報収集エージェント

    ユーザーと対話しながら相続に必要な情報を収集し、
    Personオブジェクトとして構造化する。
    """

    def __init__(self, ollama_client: Optional[OllamaClient] = None) -> None:
        """
        初期化

        Args:
            ollama_client: Ollamaクライアント（Noneの場合は新規作成）
        """
        self.logger = logging.getLogger(__name__)
        self.client = ollama_client or OllamaClient()
        self.prompts = InheritancePrompts()

        # 状態管理
        self.state = InterviewState.INIT
        self.collected_data: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, str]] = []

        # 収集したデータ
        self.decedent: Optional[Person] = None
        self.spouses: List[Person] = []
        self.children: List[Person] = []
        self.parents: List[Person] = []
        self.siblings: List[Person] = []
        self.renounced: List[Person] = []
        self.disqualified: List[Person] = []
        self.disinherited: List[Person] = []
        self.sibling_blood_types: Dict[str, BloodType] = {}
        self.retransfer_heirs_info: Dict[str, List[Person]] = {}

        self.logger.info("InterviewAgent initialized")

    def start_interview(self) -> str:
        """
        インタビューを開始

        Returns:
            最初の質問メッセージ
        """
        self.state = InterviewState.DECEDENT_INFO
        self.logger.info("Interview started")

        welcome_message = self.prompts.DECEDENT_INTRO + "\n\n" + self.prompts.DECEDENT_NAME

        # 会話履歴に追加
        self.conversation_history.append({
            "role": "assistant",
            "content": welcome_message
        })

        return welcome_message

    def process_response(self, user_input: str) -> str:
        """
        ユーザーの応答を処理し、次の質問を返す

        Args:
            user_input: ユーザーの入力

        Returns:
            次の質問または確認メッセージ
        """
        # 会話履歴に追加
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        try:
            # 状態に応じて処理を分岐
            if self.state == InterviewState.DECEDENT_INFO:
                next_message = self._process_decedent_info(user_input)
            elif self.state == InterviewState.SPOUSE_INFO:
                next_message = self._process_spouse_info(user_input)
            elif self.state == InterviewState.CHILDREN_INFO:
                next_message = self._process_children_info(user_input)
            elif self.state == InterviewState.PARENTS_INFO:
                next_message = self._process_parents_info(user_input)
            elif self.state == InterviewState.SIBLINGS_INFO:
                next_message = self._process_siblings_info(user_input)
            elif self.state == InterviewState.SPECIAL_CASES:
                next_message = self._process_special_cases(user_input)
            elif self.state == InterviewState.CONFIRMATION:
                next_message = self._process_confirmation(user_input)
            else:
                next_message = "インタビューは完了しました。"

            # 会話履歴に追加
            self.conversation_history.append({
                "role": "assistant",
                "content": next_message
            })

            return next_message

        except Exception as e:
            self.logger.error(f"Error processing response: {e}", exc_info=True)
            error_message = "申し訳ございません。エラーが発生しました。もう一度お答えいただけますか？"
            self.conversation_history.append({
                "role": "assistant",
                "content": error_message
            })
            return error_message

    def _process_decedent_info(self, user_input: str) -> str:
        """被相続人情報を処理"""
        # まだ名前を収集していない
        if "decedent_name" not in self.collected_data:
            self.collected_data["decedent_name"] = user_input.strip()
            return self.prompts.DECEDENT_DEATH_DATE

        # まだ死亡日を収集していない
        if "decedent_death_date" not in self.collected_data:
            death_date = self._parse_date(user_input)
            if death_date:
                self.collected_data["decedent_death_date"] = death_date
                return self.prompts.DECEDENT_BIRTH_DATE
            else:
                return "申し訳ございません。日付の形式が正しくありません。\n" + self.prompts.DECEDENT_DEATH_DATE

        # まだ生年月日を収集していない
        if "decedent_birth_date" not in self.collected_data:
            if user_input.strip() in ["不明", "わからない", "分からない"]:
                birth_date = None
            else:
                birth_date = self._parse_date(user_input)

            self.collected_data["decedent_birth_date"] = birth_date

            # 被相続人オブジェクトを作成
            self.decedent = Person(
                name=self.collected_data["decedent_name"],
                is_decedent=True,
                is_alive=False,
                death_date=self.collected_data["decedent_death_date"],
                birth_date=birth_date
            )

            # 次の状態へ
            self.state = InterviewState.SPOUSE_INFO
            return "\n" + self.prompts.SPOUSE_QUESTION

        return "エラーが発生しました。"

    def _process_spouse_info(self, user_input: str) -> str:
        """配偶者情報を処理"""
        # 配偶者の有無を確認
        if "has_spouse" not in self.collected_data:
            has_spouse = self._parse_yes_no(user_input)
            self.collected_data["has_spouse"] = has_spouse

            if has_spouse:
                return self.prompts.SPOUSE_INFO
            else:
                # 次の状態へ
                self.state = InterviewState.CHILDREN_INFO
                return "\n" + self.prompts.CHILDREN_QUESTION

        # 配偶者情報を収集中
        # TODO: 詳細な解析が必要（後で実装）
        # 簡易実装: 名前のみ収集
        spouse_name = user_input.strip().split("\n")[0]
        spouse = Person(
            name=spouse_name,
            is_alive=True  # デフォルトは存命
        )
        self.spouses.append(spouse)

        # 次の状態へ
        self.state = InterviewState.CHILDREN_INFO
        return "\n" + self.prompts.CHILDREN_QUESTION

    def _process_children_info(self, user_input: str) -> str:
        """子の情報を処理"""
        if "has_children" not in self.collected_data:
            has_children = self._parse_yes_no(user_input)
            self.collected_data["has_children"] = has_children

            if has_children:
                return self.prompts.CHILDREN_COUNT
            else:
                # 次の状態へ
                self.state = InterviewState.PARENTS_INFO
                return "\n" + self.prompts.PARENTS_QUESTION

        # 子の人数を確認
        if "children_count" not in self.collected_data:
            try:
                count = int(user_input.strip())
                self.collected_data["children_count"] = count
                self.collected_data["children_collected"] = 0
                return self.prompts.format_child_info(1)
            except ValueError:
                return "申し訳ございません。数字でご入力ください。\n" + self.prompts.CHILDREN_COUNT

        # 子の情報を収集中
        # TODO: 詳細な解析が必要（後で実装）
        # 簡易実装
        collected = self.collected_data["children_collected"]
        total = self.collected_data["children_count"]

        # 名前のみ収集
        child_name = user_input.strip().split("\n")[0]
        child = Person(
            name=child_name,
            is_alive=True  # デフォルトは存命
        )
        self.children.append(child)

        collected += 1
        self.collected_data["children_collected"] = collected

        if collected < total:
            return self.prompts.format_child_info(collected + 1)
        else:
            # 次の状態へ
            self.state = InterviewState.PARENTS_INFO
            return "\n" + self.prompts.PARENTS_QUESTION

    def _process_parents_info(self, user_input: str) -> str:
        """直系尊属情報を処理"""
        if "has_parents" not in self.collected_data:
            has_parents = self._parse_yes_no(user_input)
            self.collected_data["has_parents"] = has_parents

            if not has_parents:
                # 次の状態へ
                self.state = InterviewState.SIBLINGS_INFO
                return "\n" + self.prompts.SIBLINGS_QUESTION

            return self.prompts.PARENT_INFO_TEMPLATE

        # 親の情報を収集（簡易実装）
        # 次の状態へ
        self.state = InterviewState.SIBLINGS_INFO
        return "\n" + self.prompts.SIBLINGS_QUESTION

    def _process_siblings_info(self, user_input: str) -> str:
        """兄弟姉妹情報を処理"""
        if "has_siblings" not in self.collected_data:
            has_siblings = self._parse_yes_no(user_input)
            self.collected_data["has_siblings"] = has_siblings

            # 次の状態へ（特殊ケース）
            self.state = InterviewState.SPECIAL_CASES
            self.collected_data["special_case_step"] = "renunciation"
            return "\n" + self.prompts.RENUNCIATION_QUESTION

        return "エラーが発生しました。"

    def _process_special_cases(self, user_input: str) -> str:
        """特殊ケース（相続放棄等）を処理"""
        step = self.collected_data.get("special_case_step", "renunciation")

        if step == "renunciation":
            has_renunciation = self._parse_yes_no(user_input)
            self.collected_data["has_renunciation"] = has_renunciation

            # 次のステップへ
            self.collected_data["special_case_step"] = "retransfer"
            return "\n" + self.prompts.RETRANSFER_QUESTION

        if step == "retransfer":
            has_retransfer = self._parse_yes_no(user_input)
            self.collected_data["has_retransfer"] = has_retransfer

            # 確認へ
            self.state = InterviewState.CONFIRMATION
            summary = self._generate_summary()
            return "\n" + self.prompts.format_confirmation(summary)

        return "エラーが発生しました。"

    def _process_confirmation(self, user_input: str) -> str:
        """確認を処理"""
        confirmed = self._parse_yes_no(user_input)

        if confirmed:
            self.state = InterviewState.COMPLETED
            return self.prompts.CALCULATION_START
        else:
            return "修正が必要な項目を教えてください。"

    def _parse_yes_no(self, text: str) -> bool:
        """はい/いいえを解析"""
        text = text.strip().lower()
        if text in ["はい", "yes", "y", "有", "あり", "います", "いる"]:
            return True
        return False

    def _parse_date(self, text: str) -> Optional[date]:
        """日付文字列を解析"""
        text = text.strip()

        # YYYY-MM-DD形式
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        # YYYY/MM/DD形式
        match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        # YYYY年MM月DD日形式
        match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        return None

    def _generate_summary(self) -> str:
        """収集した情報のサマリーを生成"""
        lines = []
        lines.append(f"被相続人: {self.decedent.name if self.decedent else '不明'}")
        if self.decedent and self.decedent.death_date:
            lines.append(f"死亡日: {self.decedent.death_date}")

        if self.spouses:
            lines.append(f"\n配偶者: {', '.join(s.name for s in self.spouses)}")

        if self.children:
            lines.append(f"\n子: {', '.join(c.name for c in self.children)}")

        if self.parents:
            lines.append(f"\n直系尊属: {', '.join(p.name for p in self.parents)}")

        if self.siblings:
            lines.append(f"\n兄弟姉妹: {', '.join(s.name for s in self.siblings)}")

        return "\n".join(lines)

    def get_collected_data(self) -> Dict[str, Any]:
        """
        収集したデータを取得

        Returns:
            相続計算に必要なデータ
        """
        return {
            "decedent": self.decedent,
            "spouses": self.spouses,
            "children": self.children,
            "parents": self.parents,
            "siblings": self.siblings,
            "renounced": self.renounced,
            "disqualified": self.disqualified,
            "disinherited": self.disinherited,
            "sibling_blood_types": self.sibling_blood_types,
            "retransfer_heirs_info": self.retransfer_heirs_info,
        }

    def is_completed(self) -> bool:
        """インタビューが完了したか確認"""
        return self.state == InterviewState.COMPLETED
