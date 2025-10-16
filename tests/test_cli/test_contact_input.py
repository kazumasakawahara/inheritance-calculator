"""連絡先入力機能のテスト"""
from unittest.mock import patch, MagicMock
from datetime import date

import pytest

from src.cli.contact_input import ContactInfoCollector
from inheritance_calculator_core.models.person import Person, Gender
from inheritance_calculator_core.models.inheritance import InheritanceResult, Heir, HeritageRank
from fractions import Fraction


class TestContactInfoCollector:
    """ContactInfoCollectorクラスのテスト"""

    @pytest.fixture
    def collector(self):
        """テスト用ContactInfoCollector"""
        return ContactInfoCollector()

    @pytest.fixture
    def sample_person(self):
        """テスト用Person"""
        return Person(
            name="山田太郎",
            is_alive=True,
            gender=Gender.MALE
        )

    @pytest.fixture
    def sample_result(self):
        """テスト用InheritanceResult"""
        decedent = Person(name="山田次郎", is_alive=False, is_decedent=True)
        spouse = Person(name="山田花子", is_alive=True, gender=Gender.FEMALE)
        child = Person(name="山田三郎", is_alive=True, gender=Gender.MALE)

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 2),
                share_percentage=50.0
            ),
            Heir(
                person=child,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0
            )
        ]

        return InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["配偶者と子の相続"]
        )

    def test_initialization(self, collector):
        """初期化テスト"""
        assert collector.prompt is not None

    def test_validate_email_valid(self, collector):
        """有効なメールアドレスのバリデーション"""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.jp",
            "user+tag@subdomain.example.com"
        ]

        for email in valid_emails:
            assert collector._validate_email(email) is True

    def test_validate_email_invalid(self, collector):
        """無効なメールアドレスのバリデーション"""
        invalid_emails = [
            "not-an-email",  # @がない
            "@example.com",  # ユーザー名がない
            "user@"  # ドメインがない
        ]

        for email in invalid_emails:
            assert collector._validate_email(email) is False

    def test_validate_email_empty(self, collector):
        """空のメールアドレスのバリデーション"""
        assert collector._validate_email("") is True
        assert collector._validate_email(None) is True

    def test_validate_phone_valid(self, collector):
        """有効な電話番号のバリデーション"""
        valid_phones = [
            "03-1234-5678",
            "0312345678",
            "090-1234-5678",
            "+81-3-1234-5678",
            "(03) 1234-5678"
        ]

        for phone in valid_phones:
            assert collector._validate_phone(phone) is True

    def test_validate_phone_invalid(self, collector):
        """無効な電話番号のバリデーション"""
        invalid_phones = [
            "abc-defg-hijk",
            "電話番号",
            "phone#123"
        ]

        for phone in invalid_phones:
            assert collector._validate_phone(phone) is False

    def test_validate_phone_empty(self, collector):
        """空の電話番号のバリデーション"""
        assert collector._validate_phone("") is True
        assert collector._validate_phone(None) is True

    @patch('src.cli.contact_input.Confirm.ask')
    def test_collect_contact_info_declined(self, mock_confirm, collector, sample_result):
        """連絡先入力を拒否した場合のテスト"""
        mock_confirm.return_value = False

        result = collector.collect_contact_info_for_heirs(sample_result)

        assert result == []
        mock_confirm.assert_called_once()

    @patch('src.cli.contact_input.InteractivePrompt.prompt_text')
    @patch('src.cli.contact_input.ContactInfoCollector.prompt_email')
    @patch('src.cli.contact_input.Confirm.ask')
    def test_collect_single_contact_all_fields(
        self,
        mock_confirm,
        mock_email,
        mock_text,
        collector,
        sample_person
    ):
        """すべての連絡先フィールド入力テスト"""
        mock_confirm.return_value = True
        mock_text.side_effect = [
            "東京都渋谷区渋谷1-1-1",  # address
            "03-1234-5678"  # phone
        ]
        mock_email.return_value = "test@example.com"

        result = collector.collect_single_contact_info(sample_person)

        assert result.address == "東京都渋谷区渋谷1-1-1"
        assert result.phone == "03-1234-5678"
        assert result.email == "test@example.com"

    @patch('src.cli.contact_input.InteractivePrompt.prompt_text')
    @patch('src.cli.contact_input.ContactInfoCollector.prompt_email')
    def test_collect_single_contact_partial_fields(
        self,
        mock_email,
        mock_text,
        collector,
        sample_person
    ):
        """部分的な連絡先フィールド入力テスト"""
        mock_text.side_effect = [
            "東京都渋谷区渋谷1-1-1",  # address
            None  # phone (skip)
        ]
        mock_email.return_value = None  # email (skip)

        result = collector.collect_single_contact_info(sample_person)

        assert result.address == "東京都渋谷区渋谷1-1-1"
        assert result.phone is None
        assert result.email is None

    def test_display_contact_summary_empty(self, collector):
        """空の連絡先サマリー表示テスト"""
        # エラーなく実行できることを確認
        collector.display_contact_summary([])

    def test_display_contact_summary_with_data(self, collector, sample_person):
        """データありの連絡先サマリー表示テスト"""
        sample_person.set_contact_info(
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="test@example.com"
        )

        # エラーなく実行できることを確認
        collector.display_contact_summary([sample_person])

    @patch('src.cli.contact_input.InteractivePrompt.prompt_text')
    def test_prompt_email_valid_input(self, mock_text, collector):
        """有効なメールアドレス入力テスト"""
        mock_text.return_value = "valid@example.com"

        result = collector.prompt_email("山田太郎")

        assert result == "valid@example.com"

    @patch('src.cli.contact_input.InteractivePrompt.prompt_text')
    def test_prompt_email_skip(self, mock_text, collector):
        """メールアドレス入力スキップテスト"""
        mock_text.return_value = None

        result = collector.prompt_email("山田太郎")

        assert result is None
