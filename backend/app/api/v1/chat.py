"""AI対話WebSocket API"""

import json
import sys
from pathlib import Path
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings

# 親プロジェクトのsrcディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from agents.interview_agent import InterviewAgent  # type: ignore[import-not-found]
    from agents.ollama_client import OllamaClient  # type: ignore[import-not-found]
    from utils.config import OllamaSettings  # type: ignore[import-not-found]
except ImportError:
    # テスト環境での代替処理
    InterviewAgent = None  # type: ignore[assignment, misc]
    OllamaClient = None  # type: ignore[assignment, misc]
    OllamaSettings = None  # type: ignore[assignment, misc]

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatSession:
    """チャットセッション管理クラス"""

    def __init__(self, case_id: str) -> None:
        """初期化

        Args:
            case_id: 案件ID
        """
        self.case_id = case_id

        # Ollama設定
        ollama_settings = OllamaSettings(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout,
            temperature=settings.ollama_temperature,
        )

        # OllamaクライアントとInterviewAgentを初期化
        self.ollama_client = OllamaClient(ollama_settings)
        self.agent = InterviewAgent(self.ollama_client)

        # セッション状態
        self.conversation_history: list[dict[str, str]] = []

    async def process_message(self, user_message: str) -> dict[str, Any]:
        """ユーザーメッセージを処理

        Args:
            user_message: ユーザーのメッセージ

        Returns:
            dict[str, Any]: レスポンス
        """
        # 会話履歴に追加
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            # InterviewAgentで処理
            # Note: 既存のInterviewAgentは対話的なCLI用なので、
            # ここでは簡易的にOllamaClientを直接使用
            response = self.ollama_client.generate(
                prompt=self._build_prompt(user_message),
                system_prompt=self._get_system_prompt(),
            )

            agent_message = response.strip()

            # 会話履歴に追加
            self.conversation_history.append({"role": "assistant", "content": agent_message})

            return {
                "type": "message",
                "content": agent_message,
                "case_id": self.case_id,
                "history_length": len(self.conversation_history),
            }

        except Exception as e:
            return {"type": "error", "content": f"エラーが発生しました: {str(e)}", "case_id": self.case_id}

    def _get_system_prompt(self) -> str:
        """システムプロンプトを取得

        Returns:
            str: システムプロンプト
        """
        return """あなたは相続に関する情報を聞き取る専門のアシスタントです。

ユーザーから以下の情報を丁寧に聞き取ってください：
- 被相続人（亡くなった方）の情報
- 配偶者の有無と情報
- 子の有無と情報
- 父母・祖父母の有無と情報
- 兄弟姉妹の有無と情報
- 代襲相続の可能性
- 相続放棄・相続欠格・相続廃除の有無

日本の民法に基づいた相続に関する質問を行い、必要な情報を収集してください。
ユーザーに対して親切で分かりやすい言葉で質問してください。"""

    def _build_prompt(self, user_message: str) -> str:
        """プロンプトを構築

        Args:
            user_message: ユーザーメッセージ

        Returns:
            str: 構築されたプロンプト
        """
        # 会話履歴を含めたプロンプト
        history_text = ""
        for msg in self.conversation_history[-10:]:  # 最新10件のみ
            role = "ユーザー" if msg["role"] == "user" else "アシスタント"
            history_text += f"{role}: {msg['content']}\n\n"

        return f"""これまでの会話:
{history_text}

ユーザーの最新メッセージ: {user_message}

上記を踏まえて、次に聞くべき質問を1つ提示してください。
すでに十分な情報が集まっている場合は、情報を整理して確認してください。"""


# WebSocketエンドポイント
@router.websocket("/ws/{case_id}")
async def chat_websocket(websocket: WebSocket, case_id: str) -> None:
    """WebSocket接続エンドポイント

    Args:
        websocket: WebSocket接続
        case_id: 案件ID
    """
    await websocket.accept()

    # セッション作成
    session = ChatSession(case_id)

    # 初期メッセージ送信
    await websocket.send_json(
        {
            "type": "connected",
            "message": "AI対話セッションを開始しました。相続に関する情報をお聞かせください。",
            "case_id": case_id,
        }
    )

    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()

            # JSON形式でない場合はそのままテキストとして扱う
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", data)
            except json.JSONDecodeError:
                user_message = data

            # メッセージ処理
            response = await session.process_message(user_message)

            # レスポンス送信
            await websocket.send_json(response)

    except WebSocketDisconnect:
        # 切断時の処理
        pass
    except Exception as e:
        # エラー時の処理
        try:
            await websocket.send_json({"type": "error", "content": f"サーバーエラー: {str(e)}"})
        except Exception:
            pass
        finally:
            await websocket.close()


# HTTPエンドポイント（テスト用）
@router.get("/test")
async def test_chat() -> dict[str, str]:
    """テスト用エンドポイント

    Returns:
        dict[str, str]: テストメッセージ
    """
    return {"message": "Chat API is working. Use WebSocket at /api/v1/chat/ws/{case_id}"}
