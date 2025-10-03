"""Inheritanceモデルのテスト"""
from fractions import Fraction
import pytest
from pydantic import ValidationError

from src.models.person import Person
from src.models.inheritance import (
    Heir,
    InheritanceResult,
    HeritageRank,
    SubstitutionType,
)


class TestHeir:
    """Heirモデルのテスト"""

    def test_create_heir_spouse(self):
        """配偶者相続人の作成"""
        person = Person(name="配偶者")

        heir = Heir(
            person=person,
            rank=HeritageRank.SPOUSE,
            share=Fraction(1, 2),
            share_percentage=50.0
        )

        assert heir.person.name == "配偶者"
        assert heir.rank == HeritageRank.SPOUSE
        assert heir.share == Fraction(1, 2)
        assert heir.share_percentage == 50.0
        assert heir.is_substitution is False
        assert heir.substitution_type == SubstitutionType.NONE

    def test_create_heir_child(self):
        """子相続人の作成"""
        person = Person(name="子")

        heir = Heir(
            person=person,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0
        )

        assert heir.rank == HeritageRank.FIRST
        assert heir.share == Fraction(1, 4)
        assert heir.share_percentage == 25.0

    def test_create_heir_with_substitution(self):
        """代襲相続人の作成"""
        person = Person(name="孫")
        substituted = Person(name="子", is_alive=False)

        heir = Heir(
            person=person,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0,
            is_substitution=True,
            substitution_type=SubstitutionType.CHILD,
            substituted_person=substituted,
            generation=2
        )

        assert heir.is_substitution is True
        assert heir.substitution_type == SubstitutionType.CHILD
        assert heir.substituted_person.name == "子"
        assert heir.generation == 2

    def test_share_percentage_auto_calculation(self):
        """相続割合の百分率自動計算"""
        person = Person(name="相続人")

        heir = Heir(
            person=person,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 3),
            share_percentage=0.0  # ダミー値、自動計算される
        )

        # share_percentageはshareから自動計算される
        assert abs(heir.share_percentage - 33.333333) < 0.01

    def test_non_substitution_must_have_none_type(self):
        """代襲相続でない場合、タイプはNONEでなければならない"""
        person = Person(name="相続人")

        with pytest.raises(ValidationError) as exc_info:
            Heir(
                person=person,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0,
                is_substitution=False,
                substitution_type=SubstitutionType.CHILD
            )
        assert "Non-substitution heir must have NONE type" in str(exc_info.value)

    def test_substitution_must_have_valid_type(self):
        """代襲相続の場合、タイプはNONE以外でなければならない"""
        person = Person(name="孫")

        with pytest.raises(ValidationError) as exc_info:
            Heir(
                person=person,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                is_substitution=True,
                substitution_type=SubstitutionType.NONE
            )
        assert "Substitution heir must have valid substitution type" in str(exc_info.value)

    def test_heir_string_representation(self):
        """相続人の文字列表現"""
        person = Person(name="山田太郎")
        heir = Heir(
            person=person,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 2),
            share_percentage=50.0
        )

        result = str(heir)
        assert "山田太郎" in result
        assert "first" in result
        assert "1/2" in result
        assert "50.00%" in result

    def test_heir_string_with_substitution(self):
        """代襲相続人の文字列表現"""
        person = Person(name="孫")
        substituted = Person(name="子")

        heir = Heir(
            person=person,
            rank=HeritageRank.FIRST,
            share=Fraction(1, 4),
            share_percentage=25.0,
            is_substitution=True,
            substitution_type=SubstitutionType.CHILD,
            substituted_person=substituted
        )

        result = str(heir)
        assert "孫" in result
        assert "代襲" in result
        assert "子" in result


class TestInheritanceResult:
    """InheritanceResultモデルのテスト"""

    def test_create_empty_result(self):
        """空の相続結果の作成"""
        decedent = Person(name="被相続人", is_decedent=True)

        result = InheritanceResult(decedent=decedent)

        assert result.decedent.name == "被相続人"
        assert len(result.heirs) == 0
        assert result.has_spouse is False
        assert result.has_children is False
        assert result.has_parents is False
        assert result.has_siblings is False

    def test_add_heir(self):
        """相続人追加メソッドのテスト"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        spouse = Person(name="配偶者")
        result.add_heir(
            person=spouse,
            rank=HeritageRank.SPOUSE,
            share=Fraction(1, 1)
        )

        assert len(result.heirs) == 1
        assert result.heirs[0].person.name == "配偶者"
        assert result.heirs[0].share == Fraction(1, 1)

    def test_add_calculation_basis(self):
        """計算根拠追加メソッドのテスト"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        result.add_calculation_basis("民法890条")
        result.add_calculation_basis("民法900条1号")

        assert len(result.calculation_basis) == 2
        assert "民法890条" in result.calculation_basis
        assert "民法900条1号" in result.calculation_basis

    def test_get_heirs_by_rank(self):
        """順位別相続人取得メソッドのテスト"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        spouse = Person(name="配偶者")
        child1 = Person(name="子1")
        child2 = Person(name="子2")

        result.add_heir(spouse, HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(child1, HeritageRank.FIRST, Fraction(1, 4))
        result.add_heir(child2, HeritageRank.FIRST, Fraction(1, 4))

        spouses = result.get_heirs_by_rank(HeritageRank.SPOUSE)
        children = result.get_heirs_by_rank(HeritageRank.FIRST)

        assert len(spouses) == 1
        assert len(children) == 2
        assert spouses[0].person.name == "配偶者"

    def test_get_substitution_heirs(self):
        """代襲相続人取得メソッドのテスト"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        child = Person(name="子")
        grandchild = Person(name="孫")
        substituted = Person(name="死亡した子", is_alive=False)

        result.add_heir(child, HeritageRank.FIRST, Fraction(1, 2))
        result.add_heir(
            grandchild,
            HeritageRank.FIRST,
            Fraction(1, 2),
            is_substitution=True,
            substitution_type=SubstitutionType.CHILD,
            substituted_person=substituted
        )

        substitution_heirs = result.get_substitution_heirs()

        assert len(substitution_heirs) == 1
        assert substitution_heirs[0].person.name == "孫"
        assert substitution_heirs[0].is_substitution is True

    def test_total_heirs_property(self):
        """相続人総数プロパティのテスト"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        assert result.total_heirs == 0

        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(Person(name="子"), HeritageRank.FIRST, Fraction(1, 2))

        assert result.total_heirs == 2

    def test_total_share_validation_success(self):
        """相続割合合計が100%の場合は成功"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(Person(name="子1"), HeritageRank.FIRST, Fraction(1, 4))
        result.add_heir(Person(name="子2"), HeritageRank.FIRST, Fraction(1, 4))

        # バリデーションが通ればOK
        assert result.total_heirs == 3

    def test_total_share_validation_failure(self):
        """相続割合合計が100%でない場合はエラー"""
        decedent = Person(name="被相続人", is_decedent=True)

        with pytest.raises(ValidationError) as exc_info:
            InheritanceResult(
                decedent=decedent,
                heirs=[
                    Heir(
                        person=Person(name="配偶者"),
                        rank=HeritageRank.SPOUSE,
                        share=Fraction(1, 2),
                        share_percentage=50.0
                    ),
                    Heir(
                        person=Person(name="子"),
                        rank=HeritageRank.FIRST,
                        share=Fraction(1, 3),  # 合計が100%にならない
                        share_percentage=33.33
                    )
                ]
            )
        assert "Total share must be 1 (100%)" in str(exc_info.value)

    def test_string_representation(self):
        """相続結果の文字列表現"""
        decedent = Person(name="山田太郎", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        result.add_heir(Person(name="山田花子"), HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(Person(name="山田一郎"), HeritageRank.FIRST, Fraction(1, 2))
        result.add_calculation_basis("民法890条")

        output = str(result)

        assert "山田太郎" in output
        assert "山田花子" in output
        assert "山田一郎" in output
        assert "相続人総数: 2名" in output
        assert "民法890条" in output


class TestComplexInheritanceScenarios:
    """複雑な相続シナリオのテスト"""

    def test_spouse_and_children(self):
        """配偶者と子のケース"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        # 配偶者: 1/2, 子2人: 各1/4
        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(Person(name="子1"), HeritageRank.FIRST, Fraction(1, 4))
        result.add_heir(Person(name="子2"), HeritageRank.FIRST, Fraction(1, 4))

        assert result.total_heirs == 3
        total = sum(heir.share for heir in result.heirs)
        assert total == Fraction(1, 1)

    def test_spouse_and_parents(self):
        """配偶者と直系尊属のケース"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        # 配偶者: 2/3, 父母: 各1/6
        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(2, 3))
        result.add_heir(Person(name="父"), HeritageRank.SECOND, Fraction(1, 6))
        result.add_heir(Person(name="母"), HeritageRank.SECOND, Fraction(1, 6))

        assert result.total_heirs == 3
        total = sum(heir.share for heir in result.heirs)
        assert total == Fraction(1, 1)

    def test_spouse_and_siblings(self):
        """配偶者と兄弟姉妹のケース"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        # 配偶者: 3/4, 兄弟姉妹2人: 各1/8
        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(3, 4))
        result.add_heir(Person(name="兄"), HeritageRank.THIRD, Fraction(1, 8))
        result.add_heir(Person(name="妹"), HeritageRank.THIRD, Fraction(1, 8))

        assert result.total_heirs == 3
        total = sum(heir.share for heir in result.heirs)
        assert total == Fraction(1, 1)

    def test_child_substitution(self):
        """子の代襲相続のケース"""
        decedent = Person(name="被相続人", is_decedent=True)
        result = InheritanceResult(decedent=decedent)

        substituted = Person(name="死亡した子", is_alive=False)

        # 配偶者: 1/2, 存命の子: 1/4, 孫(代襲): 1/4
        result.add_heir(Person(name="配偶者"), HeritageRank.SPOUSE, Fraction(1, 2))
        result.add_heir(Person(name="存命の子"), HeritageRank.FIRST, Fraction(1, 4))
        result.add_heir(
            Person(name="孫"),
            HeritageRank.FIRST,
            Fraction(1, 4),
            is_substitution=True,
            substitution_type=SubstitutionType.CHILD,
            substituted_person=substituted
        )

        substitution_heirs = result.get_substitution_heirs()
        assert len(substitution_heirs) == 1
        assert substitution_heirs[0].person.name == "孫"

        total = sum(heir.share for heir in result.heirs)
        assert total == Fraction(1, 1)
