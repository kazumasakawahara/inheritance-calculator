"""HeirValidatorのユニットテスト

相続人資格検証サービスのテスト
"""
import pytest
from datetime import date

from src.services.heir_validator import HeirValidator
from src.models.person import Person, Gender
from src.models.inheritance import HeritageRank, SubstitutionType


class TestHeirValidator:
    """HeirValidator のユニットテスト"""

    @pytest.fixture
    def validator(self):
        """バリデーターのフィクスチャ"""
        return HeirValidator()

    @pytest.fixture
    def sample_decedent(self):
        """サンプル被相続人のフィクスチャ"""
        return Person(
            name="被相続人太郎",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15),
            gender=Gender.MALE
        )

    def test_set_decedent_valid(self, validator, sample_decedent):
        """被相続人設定の正常テスト"""
        validator.set_decedent(sample_decedent)

        assert validator.decedent == sample_decedent

    def test_set_decedent_without_is_decedent_flag(self, validator):
        """is_decedentフラグなしの被相続人設定テスト（警告が出る）"""
        person = Person(
            name="太郎",
            is_alive=False,
            is_decedent=False,  # フラグがFalse
            death_date=date(2025, 6, 15)
        )

        validator.set_decedent(person)
        assert validator.decedent == person

    def test_is_valid_heir_without_decedent(self, validator):
        """被相続人未設定での検証テスト"""
        person = Person(name="太郎", is_alive=True)

        with pytest.raises(ValueError) as exc_info:
            validator.is_valid_heir(person)

        assert "Decedent must be set" in str(exc_info.value)

    def test_is_valid_heir_same_as_decedent(self, validator, sample_decedent):
        """被相続人本人は相続人になれないテスト"""
        validator.set_decedent(sample_decedent)

        result = validator.is_valid_heir(sample_decedent)

        assert result is False

    def test_is_valid_heir_dead_person_not_before_division(self, validator, sample_decedent):
        """遺産分割前に死亡していない死者は相続人になれないテスト"""
        validator.set_decedent(sample_decedent)

        dead_person = Person(
            name="死亡者",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )

        result = validator.is_valid_heir(dead_person)

        assert result is False

    def test_is_valid_heir_dead_before_division(self, validator, sample_decedent):
        """遺産分割前に死亡した人は一旦有効（再転相続対象）テスト"""
        validator.set_decedent(sample_decedent)

        dead_before_division = Person(
            name="遺産分割前死亡者",
            is_alive=False,
            death_date=date(2025, 7, 1),  # 被相続人死亡後
            died_before_division=True
        )

        result = validator.is_valid_heir(dead_before_division)

        assert result is True

    def test_is_valid_heir_renounced(self, validator, sample_decedent):
        """相続放棄者は相続人になれないテスト"""
        validator.set_decedent(sample_decedent)

        renounced_person = Person(name="放棄者", is_alive=True)
        validator.renounced_persons = [renounced_person]

        result = validator.is_valid_heir(renounced_person)

        assert result is False

    def test_is_valid_heir_disqualified(self, validator, sample_decedent):
        """相続欠格者は相続人になれないテスト"""
        validator.set_decedent(sample_decedent)

        disqualified_person = Person(name="欠格者", is_alive=True)
        validator.disqualified_persons = [disqualified_person]

        result = validator.is_valid_heir(disqualified_person)

        assert result is False

    def test_is_valid_heir_disinherited(self, validator, sample_decedent):
        """相続廃除者は相続人になれないテスト"""
        validator.set_decedent(sample_decedent)

        disinherited_person = Person(name="廃除者", is_alive=True)
        validator.disinherited_persons = [disinherited_person]

        result = validator.is_valid_heir(disinherited_person)

        assert result is False

    def test_validate_spouse_valid(self, validator, sample_decedent):
        """配偶者の検証テスト（有効）"""
        validator.set_decedent(sample_decedent)

        spouse = Person(name="配偶者花子", is_alive=True, gender=Gender.FEMALE)

        result = validator.validate_spouse(spouse)

        assert result is True

    def test_validate_spouse_invalid(self, validator, sample_decedent):
        """配偶者の検証テスト（無効・放棄者）"""
        validator.set_decedent(sample_decedent)

        spouse = Person(name="放棄配偶者", is_alive=True)
        validator.renounced_persons = [spouse]

        result = validator.validate_spouse(spouse)

        assert result is False

    def test_validate_child_valid(self, validator, sample_decedent):
        """子の検証テスト（有効）"""
        validator.set_decedent(sample_decedent)

        child = Person(name="子一郎", is_alive=True, gender=Gender.MALE)

        result = validator.validate_child(child)

        assert result is True

    def test_validate_child_invalid(self, validator, sample_decedent):
        """子の検証テスト（無効・死亡）"""
        validator.set_decedent(sample_decedent)

        dead_child = Person(
            name="死亡した子",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )

        result = validator.validate_child(dead_child)

        assert result is False

    def test_validate_parent_valid_no_first_rank(self, validator, sample_decedent):
        """直系尊属の検証テスト（有効・第1順位なし）"""
        validator.set_decedent(sample_decedent)

        parent = Person(name="父", is_alive=True, gender=Gender.MALE)

        result = validator.validate_parent(parent, has_first_rank=False)

        assert result is True

    def test_validate_parent_invalid_has_first_rank(self, validator, sample_decedent):
        """直系尊属の検証テスト（無効・第1順位あり）"""
        validator.set_decedent(sample_decedent)

        parent = Person(name="母", is_alive=True, gender=Gender.FEMALE)

        result = validator.validate_parent(parent, has_first_rank=True)

        assert result is False

    def test_validate_sibling_valid_no_higher_ranks(self, validator, sample_decedent):
        """兄弟姉妹の検証テスト（有効・上位順位なし）"""
        validator.set_decedent(sample_decedent)

        sibling = Person(name="兄", is_alive=True, gender=Gender.MALE)

        result = validator.validate_sibling(sibling, has_first_rank=False, has_second_rank=False)

        assert result is True

    def test_validate_sibling_invalid_has_first_rank(self, validator, sample_decedent):
        """兄弟姉妹の検証テスト（無効・第1順位あり）"""
        validator.set_decedent(sample_decedent)

        sibling = Person(name="妹", is_alive=True, gender=Gender.FEMALE)

        result = validator.validate_sibling(sibling, has_first_rank=True, has_second_rank=False)

        assert result is False

    def test_validate_sibling_invalid_has_second_rank(self, validator, sample_decedent):
        """兄弟姉妹の検証テスト（無効・第2順位あり）"""
        validator.set_decedent(sample_decedent)

        sibling = Person(name="兄", is_alive=True, gender=Gender.MALE)

        result = validator.validate_sibling(sibling, has_first_rank=False, has_second_rank=True)

        assert result is False

    def test_can_substitute_without_decedent(self, validator):
        """被相続人未設定での代襲相続チェックテスト"""
        deceased_heir = Person(name="死亡相続人", is_alive=False)
        substitute = Person(name="代襲者", is_alive=True)

        with pytest.raises(ValueError) as exc_info:
            validator.can_substitute(deceased_heir, substitute, HeritageRank.FIRST)

        assert "Decedent must be set" in str(exc_info.value)

    def test_can_substitute_dead_substitute(self, validator, sample_decedent):
        """代襲相続人候補が死亡している場合のテスト"""
        validator.set_decedent(sample_decedent)

        deceased_heir = Person(
            name="死亡相続人",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        dead_substitute = Person(
            name="死亡代襲者",
            is_alive=False,
            death_date=date(2023, 1, 1)
        )

        result = validator.can_substitute(deceased_heir, dead_substitute, HeritageRank.FIRST)

        assert result is False

    def test_can_substitute_invalid_substitution_reason(self, validator, sample_decedent):
        """代襲原因が不適切な場合のテスト"""
        validator.set_decedent(sample_decedent)

        # 被相続人死亡後に死亡（代襲原因にならない）
        deceased_heir = Person(
            name="後に死亡",
            is_alive=False,
            death_date=date(2025, 7, 1)  # 被相続人より後
        )
        substitute = Person(name="代襲者", is_alive=True)

        result = validator.can_substitute(deceased_heir, substitute, HeritageRank.FIRST)

        assert result is False

    def test_can_substitute_renounced_no_substitution(self, validator, sample_decedent):
        """相続放棄は代襲原因にならないテスト"""
        validator.set_decedent(sample_decedent)

        renounced_heir = Person(
            name="放棄した子",
            is_alive=True
        )
        validator.renounced_persons = [renounced_heir]

        substitute = Person(name="孫", is_alive=True)

        result = validator.can_substitute(renounced_heir, substitute, HeritageRank.FIRST)

        assert result is False

    def test_can_substitute_first_rank_valid(self, validator, sample_decedent):
        """第1順位の代襲相続（有効）テスト"""
        validator.set_decedent(sample_decedent)

        deceased_child = Person(
            name="先に死亡した子",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        grandchild = Person(name="孫", is_alive=True)

        result = validator.can_substitute(deceased_child, grandchild, HeritageRank.FIRST)

        assert result is True

    def test_can_substitute_third_rank_valid(self, validator, sample_decedent):
        """第3順位の代襲相続（有効）テスト"""
        validator.set_decedent(sample_decedent)

        deceased_sibling = Person(
            name="先に死亡した兄",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        nephew = Person(name="甥", is_alive=True)

        result = validator.can_substitute(deceased_sibling, nephew, HeritageRank.THIRD)

        assert result is True

    def test_can_substitute_disqualified_valid(self, validator, sample_decedent):
        """相続欠格者の代襲相続（有効）テスト"""
        validator.set_decedent(sample_decedent)

        disqualified_child = Person(name="欠格した子", is_alive=True)
        validator.disqualified_persons = [disqualified_child]

        grandchild = Person(name="孫", is_alive=True)

        result = validator.can_substitute(disqualified_child, grandchild, HeritageRank.FIRST)

        assert result is True

    def test_can_substitute_disinherited_valid(self, validator, sample_decedent):
        """相続廃除者の代襲相続（有効）テスト"""
        validator.set_decedent(sample_decedent)

        disinherited_child = Person(name="廃除された子", is_alive=True)
        validator.disinherited_persons = [disinherited_child]

        grandchild = Person(name="孫", is_alive=True)

        result = validator.can_substitute(disinherited_child, grandchild, HeritageRank.FIRST)

        assert result is True

    def test_can_substitute_second_rank_invalid(self, validator, sample_decedent):
        """第2順位は代襲相続できないテスト"""
        validator.set_decedent(sample_decedent)

        deceased_parent = Person(
            name="死亡した父",
            is_alive=False,
            death_date=date(2020, 1, 1)
        )
        sibling_of_decedent = Person(name="被相続人の兄弟", is_alive=True)

        result = validator.can_substitute(deceased_parent, sibling_of_decedent, HeritageRank.SECOND)

        assert result is False

    def test_get_substitution_type_first_rank(self, validator):
        """第1順位の代襲タイプ取得テスト"""
        result = validator.get_substitution_type(HeritageRank.FIRST)

        assert result == SubstitutionType.CHILD

    def test_get_substitution_type_third_rank(self, validator):
        """第3順位の代襲タイプ取得テスト"""
        result = validator.get_substitution_type(HeritageRank.THIRD)

        assert result == SubstitutionType.SIBLING

    def test_get_substitution_type_second_rank(self, validator):
        """第2順位の代襲タイプ取得テスト（代襲なし）"""
        result = validator.get_substitution_type(HeritageRank.SECOND)

        assert result == SubstitutionType.NONE

    def test_get_substitution_type_spouse(self, validator):
        """配偶者の代襲タイプ取得テスト（代襲なし）"""
        result = validator.get_substitution_type(HeritageRank.SPOUSE)

        assert result == SubstitutionType.NONE
