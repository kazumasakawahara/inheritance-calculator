"""Person モデルの連絡先情報テスト

連絡先フィールド（address, phone, email）のテスト
"""
import pytest
from pydantic import ValidationError

from src.models.person import Person, Gender


class TestPersonContactInfo:
    """Person モデルの連絡先情報テスト"""

    def test_create_person_with_contact_info(self):
        """連絡先情報を含むPerson作成テスト"""
        person = Person(
            name="山田太郎",
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="taro@example.com"
        )

        assert person.name == "山田太郎"
        assert person.address == "東京都渋谷区渋谷1-1-1"
        assert person.phone == "03-1234-5678"
        assert person.email == "taro@example.com"

    def test_create_person_without_contact_info(self):
        """連絡先情報なしでPerson作成テスト（後方互換性）"""
        person = Person(name="山田花子")

        assert person.name == "山田花子"
        assert person.address is None
        assert person.phone is None
        assert person.email is None

    def test_create_person_with_partial_contact_info(self):
        """部分的な連絡先情報でPerson作成テスト"""
        person = Person(
            name="山田一郎",
            address="大阪府大阪市北区梅田1-1-1",
            # phone and email are None
        )

        assert person.address == "大阪府大阪市北区梅田1-1-1"
        assert person.phone is None
        assert person.email is None

    def test_valid_email_format(self):
        """有効なメールアドレス形式のテスト"""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.jp",
            "user+tag@subdomain.example.com",
        ]

        for email in valid_emails:
            person = Person(name="テストユーザー", email=email)
            assert person.email == email

    def test_invalid_email_format(self):
        """無効なメールアドレス形式のテスト"""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",  # space
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                Person(name="テストユーザー", email=email)

    def test_phone_number_flexibility(self):
        """電話番号の柔軟な形式テスト"""
        valid_phones = [
            "03-1234-5678",
            "0312345678",
            "090-1234-5678",
            "09012345678",
            "+81-3-1234-5678",
            "+81312345678",
        ]

        for phone in valid_phones:
            person = Person(name="テストユーザー", phone=phone)
            assert person.phone == phone

    def test_address_flexibility(self):
        """住所の柔軟性テスト"""
        addresses = [
            "東京都渋谷区渋谷1-1-1",
            "〒150-0002 東京都渋谷区渋谷1-1-1 マンション名101号室",
            "大阪府大阪市北区梅田1-1-1\n(注: 郵便物はこちらへ)",  # 複数行
        ]

        for address in addresses:
            person = Person(name="テストユーザー", address=address)
            assert person.address == address

    def test_set_contact_info_method(self):
        """set_contact_info メソッドのテスト"""
        person = Person(name="山田太郎")

        # 初期状態は None
        assert person.address is None
        assert person.phone is None
        assert person.email is None

        # 連絡先情報を設定
        person.set_contact_info(
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="taro@example.com"
        )

        assert person.address == "東京都渋谷区渋谷1-1-1"
        assert person.phone == "03-1234-5678"
        assert person.email == "taro@example.com"

    def test_set_contact_info_partial(self):
        """set_contact_info で部分的に設定するテスト"""
        person = Person(
            name="山田花子",
            address="初期住所",
            phone="初期電話",
            email="initial@example.com"
        )

        # 住所のみ更新
        person.set_contact_info(address="新しい住所")

        assert person.address == "新しい住所"
        assert person.phone == "初期電話"  # 変更されない
        assert person.email == "initial@example.com"  # 変更されない

    def test_contact_info_serialization(self):
        """連絡先情報のシリアライゼーションテスト"""
        person = Person(
            name="山田太郎",
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="taro@example.com"
        )

        # model_dump()で辞書化
        data = person.model_dump()

        assert data["name"] == "山田太郎"
        assert data["address"] == "東京都渋谷区渋谷1-1-1"
        assert data["phone"] == "03-1234-5678"
        assert data["email"] == "taro@example.com"

    def test_contact_info_deserialization(self):
        """連絡先情報のデシリアライゼーションテスト"""
        data = {
            "name": "山田花子",
            "address": "大阪府大阪市北区梅田1-1-1",
            "phone": "06-1234-5678",
            "email": "hanako@example.com"
        }

        person = Person(**data)

        assert person.name == "山田花子"
        assert person.address == "大阪府大阪市北区梅田1-1-1"
        assert person.phone == "06-1234-5678"
        assert person.email == "hanako@example.com"

    def test_backward_compatibility_deserialization(self):
        """後方互換性: 連絡先フィールドなしのデータからデシリアライゼーション"""
        # 既存データ（連絡先フィールドなし）
        legacy_data = {
            "name": "山田一郎",
            "is_alive": True,
            "gender": "male"
        }

        # エラーなく作成できる
        person = Person(**legacy_data)

        assert person.name == "山田一郎"
        assert person.is_alive is True
        assert person.gender == Gender.MALE
        assert person.address is None
        assert person.phone is None
        assert person.email is None
