"""Ollamaクライアント

Ollamaとの通信を管理し、LLMとのインタラクションを提供する。
"""
from typing import Optional, Dict, Any, List
import logging

import ollama
from ollama import ChatResponse

from ..utils.config import Settings
from ..utils.exceptions import ServiceException


class OllamaClient:
    """
    Ollamaクライアント

    gpt-oss:20bモデルとの通信を管理し、
    相続に関する質問応答機能を提供する。
    """

    def __init__(
        self,
        model: str = "gpt-oss:20b",
        host: Optional[str] = None,
        timeout: int = 120
    ) -> None:
        """
        初期化

        Args:
            model: 使用するモデル名
            host: OllamaホストURL（Noneの場合は設定から取得）
            timeout: タイムアウト時間（秒）
        """
        self.logger = logging.getLogger(__name__)

        # 設定の取得（Ollamaのみを初期化）
        if host is None:
            from ..utils.config import OllamaSettings
            ollama_settings = OllamaSettings()
            host = ollama_settings.host

        self.model = model
        self.host = host
        self.timeout = timeout

        # クライアントの初期化確認
        self._verify_connection()

        self.logger.info(
            f"OllamaClient initialized: model={self.model}, host={self.host}"
        )

    def _verify_connection(self) -> None:
        """
        Ollamaサーバーへの接続を確認

        Raises:
            ServiceException: 接続に失敗した場合
        """
        try:
            # モデルリストの取得で接続確認
            models = ollama.list()

            # モデルの存在確認
            model_names = [m.model for m in models.models]
            if self.model not in model_names:
                available = ", ".join(model_names)
                raise ServiceException(
                    f"Model '{self.model}' not found. "
                    f"Available models: {available}"
                )

            self.logger.info(f"Connected to Ollama successfully")

        except Exception as e:
            error_msg = f"Failed to connect to Ollama: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceException(error_msg) from e

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        チャット形式でLLMと対話

        Args:
            messages: メッセージリスト（[{"role": "user", "content": "..."}]形式）
            temperature: 生成のランダム性（0.0-1.0）
            max_tokens: 最大トークン数

        Returns:
            LLMの応答テキスト

        Raises:
            ServiceException: 通信エラーが発生した場合
        """
        try:
            self.logger.debug(f"Sending chat request with {len(messages)} messages")

            # Ollamaのchat APIを呼び出し
            options: Dict[str, Any] = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            response: ChatResponse = ollama.chat(
                model=self.model,
                messages=messages,
                options=options
            )

            # 応答の取得
            content = response.message.content

            self.logger.debug(f"Received response: {len(content)} characters")

            return content

        except Exception as e:
            error_msg = f"Chat request failed: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceException(error_msg) from e

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        プロンプトから文章を生成

        Args:
            prompt: プロンプトテキスト
            system: システムプロンプト（オプション）
            temperature: 生成のランダム性（0.0-1.0）
            max_tokens: 最大トークン数

        Returns:
            生成されたテキスト

        Raises:
            ServiceException: 通信エラーが発生した場合
        """
        messages: List[Dict[str, str]] = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def ask_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        質問に対する回答を生成

        Args:
            question: 質問テキスト
            context: 質問のコンテキスト（会話履歴など）

        Returns:
            回答テキスト

        Raises:
            ServiceException: 通信エラーが発生した場合
        """
        system_prompt = """あなたは日本の相続法に詳しい専門家です。
被相続人の相続に関する情報を収集するために、ユーザーに質問をします。
回答は簡潔で分かりやすく、必要に応じて法的な説明を加えてください。"""

        if context:
            prompt = f"コンテキスト: {context}\n\n質問: {question}"
        else:
            prompt = question

        return self.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3  # 法的情報なので低めの温度
        )

    def parse_user_input(
        self,
        user_input: str,
        expected_format: str
    ) -> str:
        """
        ユーザー入力を解析して構造化

        Args:
            user_input: ユーザーの入力
            expected_format: 期待される形式の説明

        Returns:
            解析結果（JSON形式の文字列など）

        Raises:
            ServiceException: 解析エラーが発生した場合
        """
        system_prompt = f"""ユーザーの入力を解析して、以下の形式で出力してください。
出力形式: {expected_format}

余計な説明は不要です。指定された形式のみを出力してください。"""

        return self.generate(
            prompt=user_input,
            system=system_prompt,
            temperature=0.1  # 解析タスクなので低温度
        )
