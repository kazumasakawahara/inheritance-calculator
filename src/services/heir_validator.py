"""相続人資格検証サービス

日本の民法に基づいて相続人の資格を判定するサービス。
"""
from typing import List, Optional
from datetime import date

from ..models.person import Person
from ..models.relationship import (
    ChildOf,
    SpouseOf,
    SiblingOf,
    Renounced,
    Disqualified,
    Disinherited,
    BloodType,
)
from ..models.inheritance import HeritageRank, SubstitutionType
from .base import BaseService


class HeirValidator(BaseService[Person]):
    """
    相続人資格検証サービス

    相続人の資格を判定し、相続順位を確定する。
    """

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.decedent: Optional[Person] = None
        self.spouses: List[Person] = []
        self.children: List[Person] = []
        self.parents: List[Person] = []
        self.siblings: List[Person] = []
        self.renounced_persons: List[Person] = []
        self.disqualified_persons: List[Person] = []
        self.disinherited_persons: List[Person] = []

    def set_decedent(self, decedent: Person) -> None:
        """
        被相続人を設定

        Args:
            decedent: 被相続人
        """
        if not decedent.is_decedent:
            self.log_warning("Person is not marked as decedent", person=decedent.name)

        self.decedent = decedent
        self.log_operation("Set decedent", name=decedent.name)

    def is_valid_heir(self, person: Person) -> bool:
        """
        相続人として有効かチェック

        Args:
            person: チェック対象の人物

        Returns:
            相続人として有効な場合True
        """
        if self.decedent is None:
            raise ValueError("Decedent must be set before validating heirs")

        # 被相続人本人は相続人になれない
        if person.id == self.decedent.id:
            return False

        # 死亡している場合は相続人になれない（代襲相続を除く）
        if not person.is_alive:
            return False

        # 相続放棄している場合は相続人になれない
        if person in self.renounced_persons:
            self.log_info("Person has renounced inheritance", person=person.name)
            return False

        # 相続欠格の場合は相続人になれない（ただし代襲相続は可能）
        if person in self.disqualified_persons:
            self.log_info("Person is disqualified", person=person.name)
            return False

        # 相続廃除の場合は相続人になれない（ただし代襲相続は可能）
        if person in self.disinherited_persons:
            self.log_info("Person is disinherited", person=person.name)
            return False

        return True

    def validate_spouse(self, spouse: Person) -> bool:
        """
        配偶者の相続資格を検証

        民法890条：配偶者は常に相続人となる

        Args:
            spouse: 配偶者

        Returns:
            相続人として有効な場合True
        """
        if not self.is_valid_heir(spouse):
            return False

        # 配偶者は常に相続人（民法890条）
        self.log_operation(
            "Validated spouse",
            spouse=spouse.name,
            basis="民法890条"
        )
        return True

    def validate_child(self, child: Person) -> bool:
        """
        子の相続資格を検証

        民法887条1項：子は第1順位の相続人

        Args:
            child: 子

        Returns:
            相続人として有効な場合True
        """
        if not self.is_valid_heir(child):
            return False

        # 子は第1順位の相続人（民法887条1項）
        self.log_operation(
            "Validated child",
            child=child.name,
            basis="民法887条1項"
        )
        return True

    def validate_parent(self, parent: Person, has_first_rank: bool) -> bool:
        """
        直系尊属の相続資格を検証

        民法889条1項1号：第1順位の相続人がいない場合のみ相続

        Args:
            parent: 直系尊属（父母、祖父母等）
            has_first_rank: 第1順位の相続人が存在するか

        Returns:
            相続人として有効な場合True
        """
        if not self.is_valid_heir(parent):
            return False

        # 第1順位の相続人がいる場合は相続できない
        if has_first_rank:
            self.log_info(
                "Parent cannot inherit (first rank heirs exist)",
                parent=parent.name
            )
            return False

        # 直系尊属は第2順位の相続人（民法889条1項1号）
        self.log_operation(
            "Validated parent",
            parent=parent.name,
            basis="民法889条1項1号"
        )
        return True

    def validate_sibling(
        self,
        sibling: Person,
        has_first_rank: bool,
        has_second_rank: bool
    ) -> bool:
        """
        兄弟姉妹の相続資格を検証

        民法889条1項2号：第1順位、第2順位の相続人がいない場合のみ相続

        Args:
            sibling: 兄弟姉妹
            has_first_rank: 第1順位の相続人が存在するか
            has_second_rank: 第2順位の相続人が存在するか

        Returns:
            相続人として有効な場合True
        """
        if not self.is_valid_heir(sibling):
            return False

        # 第1順位または第2順位の相続人がいる場合は相続できない
        if has_first_rank or has_second_rank:
            self.log_info(
                "Sibling cannot inherit (higher rank heirs exist)",
                sibling=sibling.name
            )
            return False

        # 兄弟姉妹は第3順位の相続人（民法889条1項2号）
        self.log_operation(
            "Validated sibling",
            sibling=sibling.name,
            basis="民法889条1項2号"
        )
        return True

    def can_substitute(
        self,
        deceased_heir: Person,
        substitute: Person,
        rank: HeritageRank
    ) -> bool:
        """
        代襲相続が可能かチェック

        民法887条2項・3項：子の代襲相続（制限なし）
        民法889条2項：兄弟姉妹の代襲相続（1代限り）

        Args:
            deceased_heir: 死亡した相続人（被代襲者）
            substitute: 代襲相続人候補
            rank: 相続順位

        Returns:
            代襲相続が可能な場合True
        """
        if self.decedent is None:
            raise ValueError("Decedent must be set")

        # 代襲相続人候補が生存していなければならない
        if not substitute.is_alive:
            return False

        # 被代襲者が被相続人より先に死亡しているか、
        # 相続欠格・相続廃除されている必要がある
        valid_substitution_reason = (
            (deceased_heir.death_date is not None and
             self.decedent.death_date is not None and
             deceased_heir.death_date < self.decedent.death_date) or
            deceased_heir in self.disqualified_persons or
            deceased_heir in self.disinherited_persons
        )

        if not valid_substitution_reason:
            return False

        # 相続放棄は代襲原因にならない
        if deceased_heir in self.renounced_persons:
            self.log_info(
                "No substitution for renounced heir",
                deceased=deceased_heir.name
            )
            return False

        # 第1順位（子）の代襲：制限なし（民法887条2項・3項）
        if rank == HeritageRank.FIRST:
            self.log_operation(
                "Substitution allowed for child",
                substitute=substitute.name,
                deceased=deceased_heir.name,
                basis="民法887条2項・3項"
            )
            return True

        # 第3順位（兄弟姉妹）の代襲：1代限り（民法889条2項）
        if rank == HeritageRank.THIRD:
            # 兄弟姉妹の子（甥・姪）までのみ代襲可能
            self.log_operation(
                "Substitution allowed for sibling (1 generation only)",
                substitute=substitute.name,
                deceased=deceased_heir.name,
                basis="民法889条2項"
            )
            return True

        return False

    def get_substitution_type(self, rank: HeritageRank) -> SubstitutionType:
        """
        代襲相続のタイプを取得

        Args:
            rank: 相続順位

        Returns:
            代襲相続タイプ
        """
        if rank == HeritageRank.FIRST:
            return SubstitutionType.CHILD
        elif rank == HeritageRank.THIRD:
            return SubstitutionType.SIBLING
        else:
            return SubstitutionType.NONE
