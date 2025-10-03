"""再転相続のテスト"""
from datetime import date
from fractions import Fraction

import pytest

from src.models.person import Person
from src.services.inheritance_calculator import InheritanceCalculator


class TestRetransferInheritance:
    """再転相続のテストクラス"""

    def test_retransfer_basic(self) -> None:
        """基本的な再転相続のテスト

        ケース8: 再転相続
        - 被相続人: A（2025年1月死亡）
        - 子B（2025年2月死亡、遺産分割前）、Bの配偶者C、Bの子D
        - 期待結果: Bの相続分（全部）がCとDに再転相続される
        """
        # 被相続人A
        decedent = Person(
            name="A",
            is_decedent=True,
            is_alive=False,
            death_date=date(2025, 1, 15)
        )

        # 子B（遺産分割前に死亡）
        child_b = Person(
            name="B",
            is_alive=False,
            death_date=date(2025, 2, 10),
            died_before_division=True  # 遺産分割前に死亡
        )

        # Bの配偶者C
        spouse_c = Person(
            name="C",
            is_alive=True
        )

        # Bの子D
        child_d = Person(
            name="D",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # 再転相続先の情報を設定
        retransfer_info = {
            str(child_b.id): [spouse_c, child_d]
        }

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child_b],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info
        )

        # 検証
        assert result.total_heirs == 2
        assert "再転相続" in str(result.calculation_basis) or "民法第896条" in str(result.calculation_basis)

        # CとDがそれぞれ1/2ずつ相続
        heirs_by_name = {heir.person.name: heir for heir in result.heirs}
        assert "C" in heirs_by_name
        assert "D" in heirs_by_name
        assert heirs_by_name["C"].share == Fraction(1, 2)
        assert heirs_by_name["D"].share == Fraction(1, 2)
        assert heirs_by_name["C"].is_retransfer is True
        assert heirs_by_name["D"].is_retransfer is True

    def test_retransfer_with_spouse_and_retransfer_heir(self) -> None:
        """配偶者と再転相続が混在するケース"""
        # 被相続人A
        decedent = Person(
            name="A",
            is_decedent=True,
            is_alive=False,
            death_date=date(2025, 1, 15)
        )

        # 配偶者（存命）
        spouse = Person(
            name="配偶者",
            is_alive=True
        )

        # 子B（遺産分割前に死亡）
        child_b = Person(
            name="B",
            is_alive=False,
            death_date=date(2025, 2, 10),
            died_before_division=True
        )

        # Bの子C
        grandchild_c = Person(
            name="C（Bの子）",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # 再転相続先の情報
        retransfer_info = {
            str(child_b.id): [grandchild_c]
        }

        result = calculator.calculate(
            decedent=decedent,
            spouses=[spouse],
            children=[child_b],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info
        )

        # 検証: 配偶者1/2、子Bの分1/2がCに再転相続
        assert result.total_heirs == 2
        heirs_by_name = {heir.person.name: heir for heir in result.heirs}

        assert "配偶者" in heirs_by_name
        assert heirs_by_name["配偶者"].share == Fraction(1, 2)
        assert heirs_by_name["配偶者"].is_retransfer is False

        assert "C（Bの子）" in heirs_by_name
        assert heirs_by_name["C（Bの子）"].share == Fraction(1, 2)
        assert heirs_by_name["C（Bの子）"].is_retransfer is True

    def test_no_retransfer_when_heir_alive(self) -> None:
        """相続人が存命の場合は再転相続が発生しない"""
        decedent = Person(
            name="A",
            is_decedent=True,
            is_alive=False
        )

        # 存命の子
        child = Person(
            name="B",
            is_alive=True,
            died_before_division=False
        )

        calculator = InheritanceCalculator()

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child],
            parents=[],
            siblings=[]
        )

        # 検証: 再転相続は発生しない
        assert result.total_heirs == 1
        assert result.heirs[0].person.name == "B"
        assert result.heirs[0].is_retransfer is False
        assert "再転相続" not in str(result.calculation_basis)
        assert "民法第896条" not in str(result.calculation_basis)

    def test_retransfer_multiple_heirs(self) -> None:
        """複数の相続人が遺産分割前に死亡したケース"""
        decedent = Person(
            name="A",
            is_decedent=True,
            is_alive=False,
            death_date=date(2025, 1, 15)
        )

        # 子B（遺産分割前に死亡）
        child_b = Person(
            name="B",
            is_alive=False,
            death_date=date(2025, 2, 10),
            died_before_division=True
        )

        # 子C（遺産分割前に死亡）
        child_c = Person(
            name="C",
            is_alive=False,
            death_date=date(2025, 2, 20),
            died_before_division=True
        )

        # Bの子D
        grandchild_d = Person(
            name="D（Bの子）",
            is_alive=True
        )

        # Cの子E
        grandchild_e = Person(
            name="E（Cの子）",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # 再転相続先の情報
        retransfer_info = {
            str(child_b.id): [grandchild_d],
            str(child_c.id): [grandchild_e]
        }

        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child_b, child_c],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info
        )

        # 検証: DとEがそれぞれ1/2ずつ相続
        assert result.total_heirs == 2
        heirs_by_name = {heir.person.name: heir for heir in result.heirs}

        assert "D（Bの子）" in heirs_by_name
        assert "E（Cの子）" in heirs_by_name
        assert heirs_by_name["D（Bの子）"].share == Fraction(1, 2)
        assert heirs_by_name["E（Cの子）"].share == Fraction(1, 2)
        assert heirs_by_name["D（Bの子）"].is_retransfer is True
        assert heirs_by_name["E（Cの子）"].is_retransfer is True
