"""Personモデルのテスト"""
from datetime import date
import pytest
from pydantic import ValidationError

from src.models.person import Person, Gender


class TestPerson:
    """Personモデルの基本テスト"""

    def test_create_person_minimal(self):
        """最小限の情報でPersonを作成"""
        person = Person(name="山田太郎")

        assert person.name == "山田太郎"
        assert person.is_alive is True
        assert person.death_date is None
        assert person.is_decedent is False
        assert person.gender == Gender.UNKNOWN

    def test_create_person_full(self):
        """完全な情報でPersonを作成"""
        person = Person(
            name="山田花子",
            birth_date=date(1980, 5, 15),
            gender=Gender.FEMALE,
            is_alive=True
        )

        assert person.name == "山田花子"
        assert person.birth_date == date(1980, 5, 15)
        assert person.gender == Gender.FEMALE
        assert person.is_alive is True

    def test_name_required(self):
        """氏名が必須であることを検証"""
        with pytest.raises(ValidationError):
            Person()

    def test_name_min_length(self):
        """氏名の最小長の検証"""
        with pytest.raises(ValidationError):
            Person(name="")

    def test_birth_date_future_invalid(self):
        """未来の生年月日は不可"""
        from datetime import date as date_class, timedelta
        future_date = date_class.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            Person(name="未来人", birth_date=future_date)
        assert "Birth date cannot be in the future" in str(exc_info.value)


class TestPersonMethods:
    """Personモデルのメソッドテスト"""

    def test_mark_as_deceased(self):
        """死亡記録メソッドのテスト"""
        person = Person(name="山田太郎", is_alive=True)
        death_date = date(2025, 6, 15)

        person.mark_as_deceased(death_date)

        assert person.is_alive is False
        assert person.death_date == death_date
        assert person.updated_at is not None

    def test_mark_as_decedent(self):
        """被相続人記録メソッドのテスト"""
        person = Person(name="山田太郎")

        person.mark_as_decedent()

        assert person.is_decedent is True
        assert person.updated_at is not None


class TestPersonAge:
    """年齢計算のテスト"""

    def test_current_age_alive(self):
        """存命中の現在年齢計算"""
        # 45歳の人を想定（誕生日前）
        person = Person(
            name="山田太郎",
            birth_date=date(1980, 12, 31),  # 年末生まれ
            is_alive=True
        )

        age = person.current_age
        assert age is not None
        assert age >= 44  # 少なくとも44歳

    def test_current_age_no_birth_date(self):
        """生年月日不明の場合"""
        person = Person(name="山田太郎")

        assert person.current_age is None

    def test_age_at_death(self):
        """死亡時年齢の計算"""
        person = Person(
            name="山田太郎",
            birth_date=date(1950, 3, 10),
            is_alive=False,
            death_date=date(2025, 6, 15)
        )

        age = person.age_at_death
        assert age == 75

    def test_age_at_death_before_birthday(self):
        """誕生日前に死亡した場合の年齢計算"""
        person = Person(
            name="山田太郎",
            birth_date=date(1950, 10, 10),
            is_alive=False,
            death_date=date(2025, 6, 15)  # 誕生日前
        )

        age = person.age_at_death
        assert age == 74  # まだ75歳になっていない

    def test_age_at_death_missing_dates(self):
        """生年月日または死亡日が不明な場合"""
        person1 = Person(name="山田太郎", death_date=date(2025, 6, 15))
        assert person1.age_at_death is None

        person2 = Person(name="山田花子", birth_date=date(1950, 3, 10))
        assert person2.age_at_death is None


class TestPersonComparisons:
    """人物比較メソッドのテスト"""

    def test_is_older_than(self):
        """年上判定のテスト"""
        older = Person(name="兄", birth_date=date(1980, 1, 1))
        younger = Person(name="弟", birth_date=date(1985, 1, 1))

        assert older.is_older_than(younger) is True
        assert younger.is_older_than(older) is False

    def test_is_older_than_no_birth_date(self):
        """生年月日不明の場合の比較"""
        person1 = Person(name="山田太郎")
        person2 = Person(name="山田花子", birth_date=date(1980, 1, 1))

        assert person1.is_older_than(person2) is False
        assert person2.is_older_than(person1) is False

    def test_died_before(self):
        """死亡順序の判定"""
        person1 = Person(
            name="先に死亡",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        person2 = Person(
            name="後に死亡",
            is_alive=False,
            death_date=date(2025, 1, 1)
        )

        assert person1.died_before(person2) is True
        assert person2.died_before(person1) is False

    def test_died_before_one_alive(self):
        """片方が存命の場合"""
        deceased = Person(
            name="故人",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        alive = Person(name="存命", is_alive=True)

        assert deceased.died_before(alive) is True
        assert alive.died_before(deceased) is False


class TestPersonStringRepresentation:
    """文字列表現のテスト"""

    def test_str_alive(self):
        """存命の場合の文字列表現"""
        person = Person(name="山田太郎", is_alive=True)
        result = str(person)

        assert "山田太郎" in result
        assert "存命" in result

    def test_str_deceased(self):
        """故人の場合の文字列表現"""
        person = Person(name="山田花子", is_alive=False)
        result = str(person)

        assert "山田花子" in result
        assert "故人" in result

    def test_str_decedent(self):
        """被相続人の場合の文字列表現"""
        person = Person(name="山田太郎", is_decedent=True)
        result = str(person)

        assert "山田太郎" in result
        assert "被相続人" in result

    def test_repr(self):
        """デバッグ用文字列表現"""
        person = Person(name="山田太郎", is_alive=True, is_decedent=False)
        result = repr(person)

        assert "Person" in result
        assert "name='山田太郎'" in result
        assert "is_alive=True" in result
        assert "is_decedent=False" in result

    def test_str_with_age_alive(self):
        """存命中で年齢ありの文字列表現"""
        person = Person(
            name="山田太郎",
            birth_date=date(1980, 5, 15),
            is_alive=True
        )
        result = str(person)

        assert "山田太郎" in result
        assert "存命" in result
        assert "歳" in result
        # 年齢は計算されるので具体的な値は検証しない

    def test_str_with_age_deceased(self):
        """故人で享年ありの文字列表現"""
        person = Person(
            name="山田花子",
            birth_date=date(1950, 3, 10),
            death_date=date(2025, 6, 15),
            is_alive=False
        )
        result = str(person)

        assert "山田花子" in result
        assert "故人" in result
        assert "享年75歳" in result

    def test_str_without_birth_date(self):
        """生年月日なしの文字列表現（年齢表示なし）"""
        person = Person(name="山田次郎", is_alive=True)
        result = str(person)

        assert "山田次郎" in result
        assert "存命" in result
        assert "歳" not in result  # 年齢情報がないので「歳」は含まれない
