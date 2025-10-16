"""display.pyのユニットテスト

Rich libraryを使った表示機能のテスト
"""
import pytest
from datetime import date
from fractions import Fraction
from unittest.mock import patch, MagicMock
from io import StringIO

from src.cli.display import (
    display_result,
    display_family_tree,
    display_error,
    display_warning,
    display_info,
    display_success,
    display_header,
    display_completion
)
from inheritance_calculator_core.models.inheritance import InheritanceResult, Heir, HeritageRank
from inheritance_calculator_core.models.person import Person, Gender


class TestDisplayFunctions:
    """display.pyの関数のテスト"""

    @pytest.fixture
    def sample_result(self):
        """サンプル計算結果のフィクスチャ"""
        decedent = Person(
            name="被相続人太郎",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15),
            gender=Gender.MALE
        )

        spouse = Person(name="配偶者花子", is_alive=True, gender=Gender.FEMALE)
        child1 = Person(name="子一郎", is_alive=True, gender=Gender.MALE)
        child2 = Person(name="子二郎", is_alive=True, gender=Gender.MALE)

        heir1 = Heir(
            person=spouse,
            rank=HeritageRank.SPOUSE,
            share=Fraction(1, 2),
            share_percentage=50.0
        )
        heir2 = Heir(
            person=child1,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0
        )
        heir3 = Heir(
            person=child2,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0
        )

        return InheritanceResult(
            decedent=decedent,
            heirs=[heir1, heir2, heir3],
            calculation_basis=["民法第900条1号（配偶者1/2、子1/2）"]
        )

    @pytest.fixture
    def mock_console(self):
        """モックコンソールのフィクスチャ"""
        with patch('src.cli.display.console') as mock:
            yield mock

    def test_display_result(self, sample_result, mock_console):
        """display_result関数のテスト"""
        display_result(sample_result)

        # console.printが呼ばれたことを確認
        assert mock_console.print.called
        # 複数回呼ばれていることを確認（ヘッダー、テーブル、計算根拠、サマリーなど）
        assert mock_console.print.call_count > 5

    def test_display_family_tree_with_spouse_and_children(self, sample_result, mock_console):
        """配偶者と子がいる場合のdisplay_family_tree関数のテスト"""
        display_family_tree(sample_result)

        # console.printが呼ばれたことを確認
        assert mock_console.print.called

    def test_display_family_tree_with_parents(self, mock_console):
        """直系尊属がいる場合のdisplay_family_tree関数のテスト"""
        decedent = Person(
            name="被相続人",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15)
        )

        parent1 = Person(name="父", is_alive=True, gender=Gender.MALE)
        parent2 = Person(name="母", is_alive=True, gender=Gender.FEMALE)

        heir1 = Heir(
            person=parent1,
            rank=HeritageRank.SECOND,
            share=Fraction(1, 2),
            share_percentage=50.0
        )
        heir2 = Heir(
            person=parent2,
            rank=HeritageRank.SECOND,
            share=Fraction(1, 2),
            share_percentage=50.0
        )

        result = InheritanceResult(
            decedent=decedent,
            heirs=[heir1, heir2],
            calculation_basis=["民法第900条2号（配偶者なし、直系尊属のみ）"]
        )

        display_family_tree(result)

        assert mock_console.print.called

    def test_display_family_tree_with_siblings(self, mock_console):
        """兄弟姉妹がいる場合のdisplay_family_tree関数のテスト"""
        decedent = Person(
            name="被相続人",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15)
        )

        sibling1 = Person(name="兄", is_alive=True, gender=Gender.MALE)
        sibling2 = Person(name="妹", is_alive=True, gender=Gender.FEMALE)

        heir1 = Heir(
            person=sibling1,
            rank=HeritageRank.THIRD,
            share=Fraction(1, 2),
            share_percentage=50.0
        )
        heir2 = Heir(
            person=sibling2,
            rank=HeritageRank.THIRD,
            share=Fraction(1, 2),
            share_percentage=50.0
        )

        result = InheritanceResult(
            decedent=decedent,
            heirs=[heir1, heir2],
            calculation_basis=["民法第900条3号（配偶者なし、兄弟姉妹のみ）"]
        )

        display_family_tree(result)

        assert mock_console.print.called

    def test_display_error(self, mock_console):
        """display_error関数のテスト"""
        error_message = "エラーが発生しました"

        display_error(error_message)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "エラー" in call_args
        assert error_message in call_args

    def test_display_warning(self, mock_console):
        """display_warning関数のテスト"""
        warning_message = "警告メッセージ"

        display_warning(warning_message)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "警告" in call_args
        assert warning_message in call_args

    def test_display_info(self, mock_console):
        """display_info関数のテスト"""
        info_message = "情報メッセージ"

        display_info(info_message)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "情報" in call_args
        assert info_message in call_args

    def test_display_success(self, mock_console):
        """display_success関数のテスト"""
        success_message = "成功しました"

        display_success(success_message)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert success_message in call_args

    def test_display_header_with_subtitle(self, mock_console):
        """サブタイトル付きdisplay_header関数のテスト"""
        title = "メインタイトル"
        subtitle = "サブタイトル"

        display_header(title, subtitle)

        # console.printが3回呼ばれる（空行、パネル、空行）
        assert mock_console.print.call_count == 3

    def test_display_header_without_subtitle(self, mock_console):
        """サブタイトルなしdisplay_header関数のテスト"""
        title = "メインタイトル"

        display_header(title)

        # console.printが3回呼ばれる（空行、パネル、空行）
        assert mock_console.print.call_count == 3

    def test_display_completion_default_message(self, mock_console):
        """デフォルトメッセージのdisplay_completion関数のテスト"""
        display_completion()

        # console.printが3回呼ばれる（空行、パネル、空行）
        assert mock_console.print.call_count == 3

    def test_display_completion_custom_message(self, mock_console):
        """カスタムメッセージのdisplay_completion関数のテスト"""
        custom_message = "カスタム完了メッセージ"

        display_completion(custom_message)

        # console.printが3回呼ばれる（空行、パネル、空行）
        assert mock_console.print.call_count == 3
