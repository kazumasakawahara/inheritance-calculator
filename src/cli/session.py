"""セッション管理

相続計算の作業セッションを保存・再開する機能を提供します。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from inheritance_calculator_core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Session:
    """セッションデータクラス"""
    session_id: str
    created_at: str
    updated_at: str
    decedent_name: Optional[str] = None
    progress_percentage: int = 0
    data: Dict[str, Any] = None
    pending_items: Dict[str, str] = None

    def __post_init__(self):
        """初期化後の処理"""
        if self.data is None:
            self.data = {}
        if self.pending_items is None:
            self.pending_items = {}


class SessionManager:
    """セッション管理クラス"""

    def __init__(self, session_dir: Optional[Path] = None):
        """初期化

        Args:
            session_dir: セッションディレクトリ（Noneの場合はデフォルト）
        """
        if session_dir is None:
            session_dir = Path.home() / ".inheritance-calculator" / "sessions"

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # セッションファイルのパーミッションを0600に設定
        try:
            self.session_dir.chmod(0o700)
        except Exception as e:
            logger.warning(f"セッションディレクトリのパーミッション設定に失敗: {e}")

    def create_session(self, data: Optional[Dict[str, Any]] = None) -> Session:
        """新しいセッションを作成

        Args:
            data: セッションデータ

        Returns:
            Session: 作成されたセッション
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        now = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            data=data or {},
            pending_items={}
        )

        self.save_session(session)
        logger.info(f"セッション作成: {session_id}")

        return session

    def save_session(self, session: Session) -> None:
        """セッションを保存

        Args:
            session: 保存するセッション
        """
        session.updated_at = datetime.now().isoformat()
        session_file = self.session_dir / f"{session.session_id}.json"

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, ensure_ascii=False, indent=2)

            # セッションファイルのパーミッションを0600に設定（所有者のみ読み書き可能）
            session_file.chmod(0o600)

            logger.info(f"セッション保存: {session.session_id}")
        except Exception as e:
            logger.error(f"セッション保存エラー: {e}")
            raise

    def load_session(self, session_id: str) -> Optional[Session]:
        """セッションを読み込み

        Args:
            session_id: セッションID

        Returns:
            Session: 読み込まれたセッション（存在しない場合はNone）
        """
        session_file = self.session_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"セッションが見つかりません: {session_id}")
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session = Session(**data)
            logger.info(f"セッション読み込み: {session_id}")
            return session

        except Exception as e:
            logger.error(f"セッション読み込みエラー: {e}")
            return None

    def list_sessions(self) -> List[Session]:
        """すべてのセッションを一覧表示

        Returns:
            List[Session]: セッションのリスト
        """
        sessions = []

        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append(Session(**data))
            except Exception as e:
                logger.warning(f"セッション読み込み失敗 ({session_file.name}): {e}")
                continue

        # 更新日時の降順でソート
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """セッションを削除

        Args:
            session_id: セッションID

        Returns:
            bool: 削除成功の場合True
        """
        session_file = self.session_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"削除対象のセッションが見つかりません: {session_id}")
            return False

        try:
            session_file.unlink()
            logger.info(f"セッション削除: {session_id}")
            return True
        except Exception as e:
            logger.error(f"セッション削除エラー: {e}")
            return False

    def clean_old_sessions(self, days: int = 30) -> int:
        """古いセッションを削除

        Args:
            days: この日数より古いセッションを削除

        Returns:
            int: 削除されたセッション数
        """
        now = datetime.now()
        deleted_count = 0

        for session in self.list_sessions():
            updated_at = datetime.fromisoformat(session.updated_at)
            age_days = (now - updated_at).days

            if age_days > days:
                if self.delete_session(session.session_id):
                    deleted_count += 1

        logger.info(f"{days}日以上経過したセッションを{deleted_count}件削除しました")
        return deleted_count

    def get_total_size(self) -> int:
        """セッションディレクトリの合計サイズを取得

        Returns:
            int: 合計サイズ（バイト）
        """
        total_size = 0

        for session_file in self.session_dir.glob("*.json"):
            try:
                total_size += session_file.stat().st_size
            except Exception:
                continue

        return total_size

    def mark_pending(self, session: Session, key: str, value: str = "未確定") -> None:
        """項目を保留としてマーク

        Args:
            session: セッション
            key: 保留項目のキー
            value: 保留の理由や状態（デフォルト: "未確定"）
        """
        session.pending_items[key] = value
        logger.info(f"保留項目追加: {key} = {value}")

    def remove_pending(self, session: Session, key: str) -> None:
        """保留項目を解除

        Args:
            session: セッション
            key: 保留項目のキー
        """
        if key in session.pending_items:
            del session.pending_items[key]
            logger.info(f"保留項目解除: {key}")

    def has_pending_items(self, session: Session) -> bool:
        """保留項目があるか確認

        Args:
            session: セッション

        Returns:
            bool: 保留項目がある場合True
        """
        return len(session.pending_items) > 0

    def get_pending_items(self, session: Session) -> Dict[str, str]:
        """保留項目を取得

        Args:
            session: セッション

        Returns:
            Dict[str, str]: 保留項目の辞書
        """
        return session.pending_items.copy()
