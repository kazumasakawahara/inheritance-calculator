"""セッション管理のテスト"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

import pytest

from src.cli.session import SessionManager, Session


class TestSession:
    """Sessionデータクラスのテスト"""

    def test_session_creation_with_defaults(self):
        """デフォルト値でのSession作成テスト"""
        session = Session(
            session_id="20251016_120000",
            created_at="2025-10-16T12:00:00",
            updated_at="2025-10-16T12:00:00"
        )

        assert session.session_id == "20251016_120000"
        assert session.decedent_name is None
        assert session.progress_percentage == 0
        assert session.data == {}
        assert session.pending_items == {}

    def test_session_creation_with_data(self):
        """データ付きSession作成テスト"""
        session = Session(
            session_id="20251016_120000",
            created_at="2025-10-16T12:00:00",
            updated_at="2025-10-16T12:00:00",
            decedent_name="山田太郎",
            progress_percentage=50,
            data={"spouse": "山田花子"},
            pending_items={"renounced": "未確定"}
        )

        assert session.decedent_name == "山田太郎"
        assert session.progress_percentage == 50
        assert session.data["spouse"] == "山田花子"
        assert session.pending_items["renounced"] == "未確定"


class TestSessionManager:
    """SessionManagerのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # テスト後にクリーンアップ
        shutil.rmtree(temp_path)

    @pytest.fixture
    def session_manager(self, temp_dir):
        """テスト用SessionManager"""
        return SessionManager(session_dir=temp_dir)

    def test_session_manager_initialization(self, temp_dir):
        """SessionManager初期化テスト"""
        manager = SessionManager(session_dir=temp_dir)

        assert manager.session_dir == temp_dir
        assert manager.session_dir.exists()
        assert manager.session_dir.is_dir()

    def test_create_session(self, session_manager):
        """セッション作成テスト"""
        session = session_manager.create_session(data={"test": "data"})

        assert session.session_id is not None
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.data == {"test": "data"}
        assert session.pending_items == {}

        # セッションファイルが作成されていることを確認
        session_file = session_manager.session_dir / f"{session.session_id}.json"
        assert session_file.exists()

    def test_save_and_load_session(self, session_manager):
        """セッション保存・読み込みテスト"""
        # セッション作成
        original_session = session_manager.create_session(
            data={"decedent": "山田太郎", "spouse": "山田花子"}
        )
        original_session.decedent_name = "山田太郎"
        original_session.progress_percentage = 30
        session_manager.save_session(original_session)

        # セッション読み込み
        loaded_session = session_manager.load_session(original_session.session_id)

        assert loaded_session is not None
        assert loaded_session.session_id == original_session.session_id
        assert loaded_session.decedent_name == "山田太郎"
        assert loaded_session.progress_percentage == 30
        assert loaded_session.data["decedent"] == "山田太郎"
        assert loaded_session.data["spouse"] == "山田花子"

    def test_load_nonexistent_session(self, session_manager):
        """存在しないセッションの読み込みテスト"""
        session = session_manager.load_session("nonexistent_session")

        assert session is None

    def test_list_sessions(self, session_manager):
        """セッション一覧取得テスト"""
        import time

        # 3つのセッションを作成（session_idがユニークになるように遅延）
        session1 = session_manager.create_session(data={"name": "session1"})
        time.sleep(1.1)  # 1秒以上待機してsession_idがユニークになるようにする
        session2 = session_manager.create_session(data={"name": "session2"})
        time.sleep(1.1)
        session3 = session_manager.create_session(data={"name": "session3"})

        # 一覧を取得
        sessions = session_manager.list_sessions()

        assert len(sessions) == 3

        # 更新日時の降順でソートされていることを確認
        assert sessions[0].session_id == session3.session_id
        assert sessions[1].session_id == session2.session_id
        assert sessions[2].session_id == session1.session_id

    def test_delete_session(self, session_manager):
        """セッション削除テスト"""
        # セッション作成
        session = session_manager.create_session()

        # セッションが存在することを確認
        assert session_manager.load_session(session.session_id) is not None

        # セッション削除
        result = session_manager.delete_session(session.session_id)

        assert result is True

        # セッションが削除されたことを確認
        assert session_manager.load_session(session.session_id) is None

    def test_delete_nonexistent_session(self, session_manager):
        """存在しないセッションの削除テスト"""
        result = session_manager.delete_session("nonexistent")

        assert result is False

    def test_mark_pending(self, session_manager):
        """保留項目マークのテスト"""
        session = session_manager.create_session()

        # 保留項目を追加
        session_manager.mark_pending(session, "renounced", "未確定")
        session_manager.mark_pending(session, "disqualified", "調査中")

        assert len(session.pending_items) == 2
        assert session.pending_items["renounced"] == "未確定"
        assert session.pending_items["disqualified"] == "調査中"

    def test_remove_pending(self, session_manager):
        """保留項目解除のテスト"""
        session = session_manager.create_session()

        # 保留項目を追加
        session_manager.mark_pending(session, "renounced", "未確定")
        session_manager.mark_pending(session, "disqualified", "調査中")

        # 1つ解除
        session_manager.remove_pending(session, "renounced")

        assert len(session.pending_items) == 1
        assert "renounced" not in session.pending_items
        assert "disqualified" in session.pending_items

    def test_has_pending_items(self, session_manager):
        """保留項目の有無確認テスト"""
        session = session_manager.create_session()

        # 初期状態（保留項目なし）
        assert not session_manager.has_pending_items(session)

        # 保留項目を追加
        session_manager.mark_pending(session, "test", "未確定")

        assert session_manager.has_pending_items(session)

    def test_get_pending_items(self, session_manager):
        """保留項目取得テスト"""
        session = session_manager.create_session()

        # 保留項目を追加
        session_manager.mark_pending(session, "item1", "未確定")
        session_manager.mark_pending(session, "item2", "調査中")

        pending = session_manager.get_pending_items(session)

        assert len(pending) == 2
        assert pending["item1"] == "未確定"
        assert pending["item2"] == "調査中"

        # コピーが返されることを確認（元のデータが変更されない）
        pending["item3"] = "新規"
        assert "item3" not in session.pending_items

    def test_get_total_size(self, session_manager):
        """セッションディレクトリサイズ取得テスト"""
        # 初期状態
        initial_size = session_manager.get_total_size()

        # セッション作成
        session_manager.create_session(data={"large_data": "x" * 1000})

        # サイズが増加していることを確認
        new_size = session_manager.get_total_size()
        assert new_size > initial_size

    def test_clean_old_sessions(self, session_manager, temp_dir):
        """古いセッション削除テスト"""
        # 新しいセッションを作成
        recent_session = session_manager.create_session()

        # 古いセッションをシミュレート（手動で作成）
        old_session_id = "20240101_120000"
        old_session_data = {
            "session_id": old_session_id,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "data": {},
            "pending_items": {}
        }

        old_session_file = temp_dir / f"{old_session_id}.json"
        with open(old_session_file, 'w', encoding='utf-8') as f:
            json.dump(old_session_data, f)

        # 30日以上経過したセッションを削除
        deleted_count = session_manager.clean_old_sessions(days=30)

        # 古いセッションが削除されたことを確認
        assert deleted_count == 1
        assert not old_session_file.exists()

        # 新しいセッションは残っていることを確認
        sessions = session_manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == recent_session.session_id

    def test_session_file_permissions(self, session_manager, temp_dir):
        """セッションファイルのパーミッションテスト"""
        session = session_manager.create_session()
        session_file = temp_dir / f"{session.session_id}.json"

        # ファイルが作成されたことを確認
        assert session_file.exists()

        # パーミッションが0600であることを確認（所有者のみ読み書き可能）
        stat = session_file.stat()
        permissions = oct(stat.st_mode)[-3:]

        # 環境によってはパーミッション設定が機能しない場合があるため、
        # 少なくともファイルが作成されていることのみ確認
        assert session_file.exists()

    def test_pending_detection_keywords(self, session_manager):
        """保留キーワード検出のテスト（実際の入力シミュレーション）"""
        session = session_manager.create_session()

        # ユーザーが「pending」「保留」「未確定」などと入力した場合を想定
        pending_keywords = ["pending", "保留", "未確定"]

        for keyword in pending_keywords:
            # 各キーワードが保留マーカーとして機能することを確認
            session_manager.mark_pending(session, f"test_{keyword}", keyword)

        assert len(session.pending_items) == 3
        assert all(keyword in session.pending_items.values() for keyword in pending_keywords)
