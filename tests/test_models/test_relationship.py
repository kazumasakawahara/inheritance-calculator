"""Relationshipモデルのテスト"""
from datetime import date
from uuid import uuid4
import pytest
from pydantic import ValidationError

from src.models.relationship import (
    ChildOf,
    SpouseOf,
    SiblingOf,
    Renounced,
    Disqualified,
    Disinherited,
    BloodType,
    SharedParent,
)


class TestChildOf:
    """ChildOf関係のテスト"""

    def test_create_biological_child(self):
        """実子関係の作成"""
        parent_id = uuid4()
        child_id = uuid4()

        relationship = ChildOf(
            parent_id=parent_id,
            child_id=child_id,
            is_biological=True
        )

        assert relationship.parent_id == parent_id
        assert relationship.child_id == child_id
        assert relationship.is_biological is True
        assert relationship.is_adoption is False

    def test_create_adopted_child(self):
        """養子関係の作成"""
        parent_id = uuid4()
        child_id = uuid4()

        relationship = ChildOf(
            parent_id=parent_id,
            child_id=child_id,
            is_adoption=True,
            is_biological=False,
            adoption_date=date(2020, 4, 1)
        )

        assert relationship.is_adoption is True
        assert relationship.is_biological is False
        assert relationship.adoption_date == date(2020, 4, 1)

    def test_adopted_cannot_be_biological(self):
        """養子は実子ではないことの検証"""
        parent_id = uuid4()
        child_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            ChildOf(
                parent_id=parent_id,
                child_id=child_id,
                is_adoption=True,
                is_biological=True
            )
        assert "Adopted child cannot be biological" in str(exc_info.value)


class TestSpouseOf:
    """SpouseOf関係のテスト"""

    def test_create_current_spouse(self):
        """現在の配偶者関係の作成"""
        person1_id = uuid4()
        person2_id = uuid4()

        relationship = SpouseOf(
            person1_id=person1_id,
            person2_id=person2_id,
            marriage_date=date(2010, 6, 1),
            is_current=True
        )

        assert relationship.person1_id == person1_id
        assert relationship.person2_id == person2_id
        assert relationship.marriage_date == date(2010, 6, 1)
        assert relationship.is_current is True
        assert relationship.divorce_date is None

    def test_create_divorced_spouse(self):
        """離婚した配偶者関係の作成"""
        person1_id = uuid4()
        person2_id = uuid4()

        relationship = SpouseOf(
            person1_id=person1_id,
            person2_id=person2_id,
            marriage_date=date(2010, 6, 1),
            divorce_date=date(2020, 12, 31),
            is_current=False
        )

        assert relationship.divorce_date == date(2020, 12, 31)
        assert relationship.is_current is False

    def test_divorced_cannot_be_current(self):
        """離婚日がある場合、is_currentはFalseでなければならない"""
        person1_id = uuid4()
        person2_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            SpouseOf(
                person1_id=person1_id,
                person2_id=person2_id,
                divorce_date=date(2020, 12, 31),
                is_current=True
            )
        assert "Divorced spouse cannot be current" in str(exc_info.value)

    def test_divorce_date_before_marriage_invalid(self):
        """離婚日が婚姻日より前は不可"""
        person1_id = uuid4()
        person2_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            SpouseOf(
                person1_id=person1_id,
                person2_id=person2_id,
                marriage_date=date(2010, 6, 1),
                divorce_date=date(2009, 12, 31),
                is_current=False
            )
        assert "Divorce date cannot be before marriage date" in str(exc_info.value)


class TestSiblingOf:
    """SiblingOf関係のテスト"""

    def test_create_full_blood_siblings(self):
        """全血兄弟姉妹関係の作成"""
        person1_id = uuid4()
        person2_id = uuid4()

        relationship = SiblingOf(
            person1_id=person1_id,
            person2_id=person2_id,
            blood_type=BloodType.FULL,
            shared_parent=SharedParent.BOTH
        )

        assert relationship.blood_type == BloodType.FULL
        assert relationship.shared_parent == SharedParent.BOTH

    def test_create_half_blood_siblings_father(self):
        """半血兄弟姉妹関係（父のみ同じ）の作成"""
        person1_id = uuid4()
        person2_id = uuid4()

        relationship = SiblingOf(
            person1_id=person1_id,
            person2_id=person2_id,
            blood_type=BloodType.HALF,
            shared_parent=SharedParent.FATHER
        )

        assert relationship.blood_type == BloodType.HALF
        assert relationship.shared_parent == SharedParent.FATHER

    def test_create_half_blood_siblings_mother(self):
        """半血兄弟姉妹関係（母のみ同じ）の作成"""
        person1_id = uuid4()
        person2_id = uuid4()

        relationship = SiblingOf(
            person1_id=person1_id,
            person2_id=person2_id,
            blood_type=BloodType.HALF,
            shared_parent=SharedParent.MOTHER
        )

        assert relationship.blood_type == BloodType.HALF
        assert relationship.shared_parent == SharedParent.MOTHER

    def test_full_blood_must_share_both_parents(self):
        """全血の場合、両親とも同じでなければならない"""
        person1_id = uuid4()
        person2_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            SiblingOf(
                person1_id=person1_id,
                person2_id=person2_id,
                blood_type=BloodType.FULL,
                shared_parent=SharedParent.FATHER
            )
        assert "Full blood siblings must share both parents" in str(exc_info.value)

    def test_half_blood_cannot_share_both_parents(self):
        """半血の場合、両親とも同じではいけない"""
        person1_id = uuid4()
        person2_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            SiblingOf(
                person1_id=person1_id,
                person2_id=person2_id,
                blood_type=BloodType.HALF,
                shared_parent=SharedParent.BOTH
            )
        assert "Half blood siblings cannot share both parents" in str(exc_info.value)


class TestRenounced:
    """Renounced（相続放棄）関係のテスト"""

    def test_create_renounced(self):
        """相続放棄関係の作成"""
        heir_id = uuid4()
        decedent_id = uuid4()

        relationship = Renounced(
            heir_id=heir_id,
            decedent_id=decedent_id,
            renounce_date=date(2025, 7, 1),
            reason="経済的理由"
        )

        assert relationship.heir_id == heir_id
        assert relationship.decedent_id == decedent_id
        assert relationship.renounce_date == date(2025, 7, 1)
        assert relationship.reason == "経済的理由"

    def test_renounce_date_future_invalid(self):
        """未来の放棄日は不可"""
        heir_id = uuid4()
        decedent_id = uuid4()
        from datetime import date as date_class, timedelta
        future_date = date_class.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            Renounced(
                heir_id=heir_id,
                decedent_id=decedent_id,
                renounce_date=future_date
            )
        assert "Renounce date cannot be in the future" in str(exc_info.value)


class TestDisqualified:
    """Disqualified（相続欠格）関係のテスト"""

    def test_create_disqualified(self):
        """相続欠格関係の作成"""
        heir_id = uuid4()
        decedent_id = uuid4()

        relationship = Disqualified(
            heir_id=heir_id,
            decedent_id=decedent_id,
            reason="被相続人を殺害した",
            determination_date=date(2025, 6, 1)
        )

        assert relationship.heir_id == heir_id
        assert relationship.decedent_id == decedent_id
        assert relationship.reason == "被相続人を殺害した"
        assert relationship.determination_date == date(2025, 6, 1)

    def test_reason_required(self):
        """欠格事由は必須"""
        heir_id = uuid4()
        decedent_id = uuid4()

        with pytest.raises(ValidationError):
            Disqualified(
                heir_id=heir_id,
                decedent_id=decedent_id,
                reason="",
                determination_date=date(2025, 6, 1)
            )

    def test_determination_date_future_invalid(self):
        """未来の確定日は不可"""
        heir_id = uuid4()
        decedent_id = uuid4()
        from datetime import date as date_class, timedelta
        future_date = date_class.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            Disqualified(
                heir_id=heir_id,
                decedent_id=decedent_id,
                reason="被相続人を殺害した",
                determination_date=future_date
            )
        assert "Determination date cannot be in the future" in str(exc_info.value)


class TestDisinherited:
    """Disinherited（相続廃除）関係のテスト"""

    def test_create_disinherited(self):
        """相続廃除関係の作成"""
        heir_id = uuid4()
        decedent_id = uuid4()

        relationship = Disinherited(
            heir_id=heir_id,
            decedent_id=decedent_id,
            reason="被相続人に対する虐待",
            court_decision_date=date(2025, 5, 1)
        )

        assert relationship.heir_id == heir_id
        assert relationship.decedent_id == decedent_id
        assert relationship.reason == "被相続人に対する虐待"
        assert relationship.court_decision_date == date(2025, 5, 1)

    def test_reason_required(self):
        """廃除事由は必須"""
        heir_id = uuid4()
        decedent_id = uuid4()

        with pytest.raises(ValidationError):
            Disinherited(
                heir_id=heir_id,
                decedent_id=decedent_id,
                reason="",
                court_decision_date=date(2025, 5, 1)
            )

    def test_court_decision_date_future_invalid(self):
        """未来の審判確定日は不可"""
        heir_id = uuid4()
        decedent_id = uuid4()
        from datetime import date as date_class, timedelta
        future_date = date_class.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            Disinherited(
                heir_id=heir_id,
                decedent_id=decedent_id,
                reason="被相続人に対する虐待",
                court_decision_date=future_date
            )
        assert "Court decision date cannot be in the future" in str(exc_info.value)
