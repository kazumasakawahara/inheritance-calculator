"""相続計算サービスのテスト"""
from datetime import date
from fractions import Fraction
import pytest

from src.models.person import Person
from src.models.relationship import BloodType
from src.models.inheritance import HeritageRank
from src.services.inheritance_calculator import InheritanceCalculator


class TestInheritanceCalculatorBasic:
    """基本的な相続計算のテスト"""

    def test_spouse_only(self):
        """配偶者のみの場合"""
        calculator = InheritanceCalculator()

        decedent = Person(
            name="被相続人",
            is_decedent=True,
            is_alive=False,
            death_date=date(2025, 6, 15)
        )
        spouse = Person(name="配偶者", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[],
            parents=[],
            siblings=[]
        )

        assert result.total_heirs == 1
        assert result.has_spouse is True
        assert result.heirs[0].person.name == "配偶者"
        assert result.heirs[0].rank == HeritageRank.SPOUSE
        assert result.heirs[0].share == Fraction(1, 1)
        assert any("民法890条" in basis for basis in result.calculation_basis)

    def test_spouse_and_children(self):
        """配偶者と子の場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        spouse = Person(name="配偶者", is_alive=True)
        child1 = Person(name="子1", is_alive=True)
        child2 = Person(name="子2", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[child1, child2],
            parents=[],
            siblings=[]
        )

        assert result.total_heirs == 3
        assert result.has_spouse is True
        assert result.has_children is True

        # 配偶者: 1/2
        spouse_heir = result.get_heirs_by_rank(HeritageRank.SPOUSE)[0]
        assert spouse_heir.share == Fraction(1, 2)

        # 子: 各1/4
        children_heirs = result.get_heirs_by_rank(HeritageRank.FIRST)
        assert len(children_heirs) == 2
        for heir in children_heirs:
            assert heir.share == Fraction(1, 4)

        assert any("民法900条1号" in basis for basis in result.calculation_basis)

    def test_spouse_and_parents(self):
        """配偶者と直系尊属の場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        spouse = Person(name="配偶者", is_alive=True)
        father = Person(name="父", is_alive=True)
        mother = Person(name="母", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[],  # 子なし
            parents=[father, mother],
            siblings=[]
        )

        assert result.total_heirs == 3
        assert result.has_spouse is True
        assert result.has_parents is True
        assert result.has_children is False

        # 配偶者: 2/3
        spouse_heir = result.get_heirs_by_rank(HeritageRank.SPOUSE)[0]
        assert spouse_heir.share == Fraction(2, 3)

        # 直系尊属: 各1/6
        parent_heirs = result.get_heirs_by_rank(HeritageRank.SECOND)
        assert len(parent_heirs) == 2
        for heir in parent_heirs:
            assert heir.share == Fraction(1, 6)

        assert any("民法889条1項1号" in basis for basis in result.calculation_basis)
        assert any("民法900条2号" in basis for basis in result.calculation_basis)

    def test_spouse_and_siblings(self):
        """配偶者と兄弟姉妹の場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        spouse = Person(name="配偶者", is_alive=True)
        brother = Person(name="兄", is_alive=True)
        sister = Person(name="妹", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[],  # 子なし
            parents=[],   # 直系尊属なし
            siblings=[brother, sister]
        )

        assert result.total_heirs == 3
        assert result.has_spouse is True
        assert result.has_siblings is True
        assert result.has_children is False
        assert result.has_parents is False

        # 配偶者: 3/4
        spouse_heir = result.get_heirs_by_rank(HeritageRank.SPOUSE)[0]
        assert spouse_heir.share == Fraction(3, 4)

        # 兄弟姉妹: 各1/8
        sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
        assert len(sibling_heirs) == 2
        for heir in sibling_heirs:
            assert heir.share == Fraction(1, 8)

        assert any("民法889条1項2号" in basis for basis in result.calculation_basis)
        assert any("民法900条3号" in basis for basis in result.calculation_basis)


class TestInheritanceCalculatorRankPriority:
    """相続順位の優先順位テスト"""

    def test_first_rank_excludes_second_rank(self):
        """第1順位がいる場合、第2順位は相続できない"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        child = Person(name="子", is_alive=True)
        father = Person(name="父", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child],
            parents=[father],
            siblings=[]
        )

        assert result.total_heirs == 1
        assert result.has_children is True
        assert result.has_parents is False  # 父は相続できない

        child_heir = result.get_heirs_by_rank(HeritageRank.FIRST)[0]
        assert child_heir.share == Fraction(1, 1)  # 全部相続

    def test_first_rank_excludes_third_rank(self):
        """第1順位がいる場合、第3順位は相続できない"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        child = Person(name="子", is_alive=True)
        brother = Person(name="兄", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child],
            parents=[],
            siblings=[brother]
        )

        assert result.total_heirs == 1
        assert result.has_children is True
        assert result.has_siblings is False  # 兄は相続できない

    def test_second_rank_excludes_third_rank(self):
        """第2順位がいる場合、第3順位は相続できない"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        father = Person(name="父", is_alive=True)
        brother = Person(name="兄", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[],  # 子なし
            parents=[father],
            siblings=[brother]
        )

        assert result.total_heirs == 1
        assert result.has_parents is True
        assert result.has_siblings is False  # 兄は相続できない


class TestInheritanceCalculatorSiblingBloodTypes:
    """兄弟姉妹の血縁タイプテスト"""

    def test_full_blood_siblings_only(self):
        """全血兄弟姉妹のみの場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        brother = Person(name="兄", is_alive=True)
        sister = Person(name="妹", is_alive=True)

        blood_types = {
            str(brother.id): BloodType.FULL,
            str(sister.id): BloodType.FULL,
        }

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[],
            parents=[],
            siblings=[brother, sister],
            sibling_blood_types=blood_types
        )

        sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
        assert len(sibling_heirs) == 2
        # 均等に分割
        for heir in sibling_heirs:
            assert heir.share == Fraction(1, 2)

    def test_mixed_blood_siblings(self):
        """全血と半血が混在する場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        full_blood_brother = Person(name="全血兄", is_alive=True)
        half_blood_brother = Person(name="半血兄", is_alive=True)

        blood_types = {
            str(full_blood_brother.id): BloodType.FULL,
            str(half_blood_brother.id): BloodType.HALF,
        }

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[],
            parents=[],
            siblings=[full_blood_brother, half_blood_brother],
            sibling_blood_types=blood_types
        )

        sibling_heirs = result.get_heirs_by_rank(HeritageRank.THIRD)
        assert len(sibling_heirs) == 2

        # 全血: 2/3, 半血: 1/3
        full_heir = [h for h in sibling_heirs if h.person.name == "全血兄"][0]
        half_heir = [h for h in sibling_heirs if h.person.name == "半血兄"][0]

        assert full_heir.share == Fraction(2, 3)
        assert half_heir.share == Fraction(1, 3)


class TestInheritanceCalculatorRenunciation:
    """相続放棄のテスト"""

    def test_child_renounced(self):
        """子が相続放棄した場合"""
        calculator = InheritanceCalculator()

        decedent = Person(name="被相続人", is_decedent=True, is_alive=False)
        child1 = Person(name="子1", is_alive=True)
        child2 = Person(name="子2", is_alive=True)
        child3_renounced = Person(name="子3（放棄）", is_alive=True)

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child1, child2, child3_renounced],
            parents=[],
            siblings=[],
            renounced=[child3_renounced]
        )

        # 放棄していない子のみが相続
        assert result.total_heirs == 2
        heirs = result.get_heirs_by_rank(HeritageRank.FIRST)
        assert len(heirs) == 2
        assert all(h.person.name != "子3（放棄）" for h in heirs)

        # 均等に分割（1/2ずつ）
        for heir in heirs:
            assert heir.share == Fraction(1, 2)


class TestInheritanceCalculatorStringRepresentation:
    """文字列表現のテスト"""

    def test_result_string_output(self):
        """相続結果の文字列出力"""
        calculator = InheritanceCalculator()

        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False,
            birth_date=date(1950, 1, 1),
            death_date=date(2025, 6, 15)
        )
        spouse = Person(
            name="山田花子",
            is_alive=True,
            birth_date=date(1955, 3, 10)
        )
        child = Person(
            name="山田一郎",
            is_alive=True,
            birth_date=date(1980, 5, 20)
        )

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[child],
            parents=[],
            siblings=[]
        )

        output = str(result)

        # 基本情報が含まれているか
        assert "山田太郎" in output
        assert "山田花子" in output
        assert "山田一郎" in output
        assert "相続人総数: 2名" in output
        assert "1/2" in output
        assert "民法" in output
