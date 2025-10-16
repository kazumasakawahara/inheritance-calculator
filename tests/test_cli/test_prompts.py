"""インタラクティブプロンプトのテスト"""
from unittest.mock import patch, MagicMock
from datetime import date
import tempfile
from pathlib import Path

import pytest

from src.cli.prompts import InteractivePrompt
from src.cli.session import SessionManager


class TestInteractivePrompt:
    """InteractivePromptクラスのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        import shutil
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def prompt(self, temp_dir):
        """テスト用InteractivePrompt"""
        session_manager = SessionManager(session_dir=temp_dir)
        return InteractivePrompt(session_manager=session_manager)

    def test_initialization(self, prompt):
        """初期化テスト"""
        assert prompt.session_manager is not None
        assert prompt.session is None
        assert prompt.input_data == {}

    def test_create_session(self, prompt):
        """セッション作成テスト"""
        session = prompt.create_session(data={"test": "data"})

        assert session is not None
        assert session.session_id is not None
        assert session.data["test"] == "data"
        assert prompt.session == session

    def test_load_session(self, prompt):
        """セッション読み込みテスト"""
        # セッション作成
        created_session = prompt.create_session(data={"original": "data"})
        session_id = created_session.session_id

        # 新しいpromptインスタンスで読み込み
        new_prompt = InteractivePrompt(session_manager=prompt.session_manager)
        loaded_session = new_prompt.load_session(session_id)

        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.data["original"] == "data"

    def test_save_current_session(self, prompt):
        """現在のセッション保存テスト"""
        session = prompt.create_session()
        session.data["new_key"] = "new_value"

        # 保存
        prompt.save_current_session()

        # 読み込んで確認
        loaded = prompt.session_manager.load_session(session.session_id)
        assert loaded.data["new_key"] == "new_value"

    @patch('src.cli.prompts.Prompt.ask')
    def test_prompt_text_normal_input(self, mock_ask, prompt):
        """通常のテキスト入力テスト"""
        mock_ask.return_value = "test input"

        result = prompt.prompt_text("テスト", "test_key")

        assert result == "test input"
        mock_ask.assert_called_once()

    @patch('src.cli.prompts.Prompt.ask')
    def test_prompt_text_pending_keyword(self, mock_ask, prompt):
        """保留キーワード入力テスト"""
        prompt.create_session()
        mock_ask.return_value = "pending"

        result = prompt.prompt_text("テスト", "test_key", allow_pending=True)

        assert result is None
        assert "test_key" in prompt.session.pending_items

    @patch('src.cli.prompts.Prompt.ask')
    def test_prompt_text_optional_empty(self, mock_ask, prompt):
        """オプショナル項目で空入力のテスト"""
        mock_ask.return_value = ""

        result = prompt.prompt_text("テスト", "test_key", optional=True)

        assert result is None

    @patch('src.cli.prompts.Prompt.ask')
    def test_prompt_int_valid(self, mock_ask, prompt):
        """整数入力（有効）テスト"""
        mock_ask.return_value = "42"

        result = prompt.prompt_int("数値入力", "test_key")

        assert result == 42

    @patch('src.cli.prompts.Prompt.ask')
    def test_prompt_int_with_range(self, mock_ask, prompt):
        """整数入力（範囲指定）テスト"""
        # 範囲内の値
        mock_ask.return_value = "50"

        result = prompt.prompt_int("数値入力", "test_key", min_value=1, max_value=100)

        assert result == 50

    @patch('src.cli.prompts.Confirm.ask')
    def test_prompt_update_pending_no_pending(self, mock_confirm, prompt):
        """保留項目なしの更新確認テスト"""
        prompt.create_session()

        result = prompt.prompt_update_pending()

        assert result is False
        mock_confirm.assert_not_called()

    @patch('src.cli.prompts.Confirm.ask')
    def test_prompt_update_pending_with_pending(self, mock_confirm, prompt):
        """保留項目ありの更新確認テスト"""
        prompt.create_session()
        prompt.session_manager.mark_pending(prompt.session, "test_item", "未確定")

        mock_confirm.return_value = True

        result = prompt.prompt_update_pending()

        assert result is True
        mock_confirm.assert_called_once()

    def test_display_pending_items_no_session(self, prompt):
        """セッションなしの保留項目表示テスト"""
        # エラーなく実行できることを確認
        prompt.display_pending_items()

    def test_display_pending_items_with_items(self, prompt):
        """保留項目ありの表示テスト"""
        prompt.create_session()
        prompt.session_manager.mark_pending(prompt.session, "item1", "未確定")
        prompt.session_manager.mark_pending(prompt.session, "item2", "調査中")

        # エラーなく実行できることを確認
        prompt.display_pending_items()

    def test_pending_keywords_list(self):
        """保留キーワードのリストテスト"""
        expected_keywords = ["pending", "保留", "未確定", "skip"]

        assert InteractivePrompt.PENDING_KEYWORDS == expected_keywords

    @patch('src.cli.prompts.Prompt.ask')
    def test_confirm_inputs_simple(self, mock_ask, prompt):
        """入力確認（確定）テスト"""
        mock_ask.return_value = ""  # Enter で確定

        data = {"name": "山田太郎", "age": 30}
        result = prompt.confirm_inputs(data)

        assert result is True
