"""再転相続における相続放棄制約のテスト"""
from datetime import date
import pytest

from src.models.person import Person
from src.services.inheritance_calculator import InheritanceCalculator
from src.utils.exceptions import RenunciationConflictError


class TestRetransferRenunciationConstraint:
    """再転相続における相続放棄制約のテストクラス（最高裁昭和63年6月21日判決）"""

    def test_second_inheritance_renounced_cannot_accept_first_only(self) -> None:
        """第2次相続を放棄した者は第1次相続のみを承認できない（判例違反ケース）

        ケース: 再転相続放棄制約
        - 被相続人A（2025年1月死亡）
        - 子B（2025年2月死亡、遺産分割前）
        - Bの子C（存命）
        - CがBの相続を放棄したが、Aの相続のみを承認しようとする
        - 期待結果: RenunciationConflictError が発生
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
            died_before_division=True
        )

        # Bの子C
        grandchild_c = Person(
            name="C",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # 再転相続先の情報: CはAの相続を承認しようとしている
        retransfer_info = {
            str(child_b.id): [grandchild_c]
        }

        # 再転相続先の関係情報
        retransfer_relationships = {
            str(child_b.id): {
                str(grandchild_c.id): 'child'
            }
        }

        # 第2次相続（Bの相続）をCが放棄
        second_inheritance_renounced = {
            str(child_b.id): [grandchild_c]
        }

        # 検証: 判例制約違反のためRenunciationConflictErrorが発生すべき
        with pytest.raises(RenunciationConflictError) as exc_info:
            calculator.calculate(
                decedent=decedent,
                spouses=[],
                children=[child_b],
                parents=[],
                siblings=[],
                retransfer_heirs_info=retransfer_info,
                retransfer_relationships=retransfer_relationships,
                second_inheritance_renounced=second_inheritance_renounced
            )

        # エラーメッセージの検証
        error_message = str(exc_info.value)
        assert "Cは" in error_message
        assert "Bの相続を放棄している" in error_message
        assert "Aの相続のみを承認することはできません" in error_message
        assert "最高裁昭和63年6月21日判決" in error_message

    def test_both_inheritances_renounced_is_allowed(self) -> None:
        """両方の相続を放棄することは許可される"""
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
            died_before_division=True
        )

        # Bの子C（両方放棄）
        grandchild_c = Person(
            name="C",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # CはAの相続もBの相続も放棄する場合、再転相続先には含まれない
        retransfer_info = {
            str(child_b.id): []  # Cは含まれていない
        }

        # 第2次相続（Bの相続）をCが放棄
        second_inheritance_renounced = {
            str(child_b.id): [grandchild_c]
        }

        # 検証: エラーが発生しない（両方放棄は許可される）
        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child_b],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info,
            second_inheritance_renounced=second_inheritance_renounced
        )

        # 再転相続先がいない場合、Bが相続人として残る（died_before_divisionだが再転相続先なし）
        assert result.total_heirs == 1
        assert result.heirs[0].person.name == "B"

    def test_both_inheritances_accepted_is_allowed(self) -> None:
        """両方の相続を承認することは許可される"""
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
            died_before_division=True
        )

        # Bの子C（両方承認）
        grandchild_c = Person(
            name="C",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # CはAの相続もBの相続も承認
        retransfer_info = {
            str(child_b.id): [grandchild_c]
        }

        retransfer_relationships = {
            str(child_b.id): {
                str(grandchild_c.id): 'child'
            }
        }

        # 第2次相続（Bの相続）の放棄者なし
        second_inheritance_renounced = {
            str(child_b.id): []
        }

        # 検証: エラーが発生しない（両方承認は許可される）
        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child_b],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info,
            retransfer_relationships=retransfer_relationships,
            second_inheritance_renounced=second_inheritance_renounced
        )

        # Cが全部相続
        assert result.total_heirs == 1
        assert result.heirs[0].person.name == "C"

    def test_first_inheritance_renounced_is_allowed(self) -> None:
        """第1次相続を放棄し、第2次相続を承認することは許可される"""
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
            died_before_division=True
        )

        # Bの子C
        grandchild_c = Person(
            name="C",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # CがAの相続を放棄した場合、再転相続先には含まれない
        # （Aの相続権がないので、Bから承継する権利もない）
        retransfer_info = {
            str(child_b.id): []  # Cは含まれていない（Aの相続を放棄）
        }

        # Bの相続は承認（放棄者なし）
        second_inheritance_renounced = {
            str(child_b.id): []
        }

        # 検証: エラーが発生しない
        result = calculator.calculate(
            decedent=decedent,
            spouses=[],
            children=[child_b],
            parents=[],
            siblings=[],
            retransfer_heirs_info=retransfer_info,
            second_inheritance_renounced=second_inheritance_renounced
        )

        # 再転相続先がいない場合、Bが相続人として残る
        assert result.total_heirs == 1
        assert result.heirs[0].person.name == "B"

    def test_multiple_retransfer_heirs_partial_renunciation(self) -> None:
        """複数の再転相続先のうち一部が第2次相続を放棄したケース"""
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
            died_before_division=True
        )

        # Bの子C（Bの相続を放棄）
        grandchild_c = Person(
            name="C",
            is_alive=True
        )

        # Bの子D（Bの相続を承認）
        grandchild_d = Person(
            name="D",
            is_alive=True
        )

        calculator = InheritanceCalculator()

        # CとDの両方がAの相続を承認しようとする（ただしCはBの相続を放棄）
        retransfer_info = {
            str(child_b.id): [grandchild_c, grandchild_d]
        }

        retransfer_relationships = {
            str(child_b.id): {
                str(grandchild_c.id): 'child',
                str(grandchild_d.id): 'child'
            }
        }

        # CがBの相続を放棄
        second_inheritance_renounced = {
            str(child_b.id): [grandchild_c]
        }

        # 検証: Cが含まれているためRenunciationConflictErrorが発生すべき
        with pytest.raises(RenunciationConflictError) as exc_info:
            calculator.calculate(
                decedent=decedent,
                spouses=[],
                children=[child_b],
                parents=[],
                siblings=[],
                retransfer_heirs_info=retransfer_info,
                retransfer_relationships=retransfer_relationships,
                second_inheritance_renounced=second_inheritance_renounced
            )

        error_message = str(exc_info.value)
        assert "C" in error_message
