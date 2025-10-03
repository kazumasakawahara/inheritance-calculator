"""CSVパーサー

CSV形式から相続情報を読み込む機能を提供します。
"""
import csv
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.models.person import Person
from src.models.relationship import BloodType
from src.utils.exceptions import ValidationError


@dataclass
class CSVRow:
    """CSV行データ"""
    role: str  # 役割: decedent, spouse, child, parent, sibling
    name: str
    is_alive: bool
    birth_date: Optional[date]
    death_date: Optional[date]
    blood_type: Optional[str]  # full or half (兄弟姉妹のみ)
    is_renounced: bool  # 相続放棄


class CSVParser:
    """CSVパーサー"""

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """日付文字列をdateオブジェクトに変換

        Args:
            date_str: 日付文字列（YYYY-MM-DD、YYYY/MM/DD、空文字列）

        Returns:
            dateオブジェクト、または None
        """
        if not date_str or date_str.strip() == "":
            return None

        # 複数の日付フォーマットに対応
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        raise ValueError(f"無効な日付形式です: {date_str}")

    @staticmethod
    def parse_bool(bool_str: str) -> bool:
        """文字列をbooleanに変換

        Args:
            bool_str: 真偽値文字列（はい/いいえ、yes/no、1/0、true/false）

        Returns:
            boolean値
        """
        true_values = ["はい", "yes", "y", "1", "true", "t", "存命", "○", "◯"]
        false_values = ["いいえ", "no", "n", "0", "false", "f", "死亡", "×"]

        normalized = bool_str.strip().lower()

        if normalized in true_values:
            return True
        elif normalized in false_values:
            return False
        else:
            raise ValueError(f"無効なboolean値です: {bool_str}")

    @classmethod
    def parse_csv_file(cls, file_path: Path) -> Tuple[
        Person,
        List[Person],
        List[Person],
        List[Person],
        List[Person],
        List[Person],
        Dict[str, BloodType]
    ]:
        """CSVファイルから相続情報を読み込み

        Args:
            file_path: CSVファイルのパス

        Returns:
            (decedent, spouses, children, parents, siblings, renounced, sibling_blood_types)

        Raises:
            ValidationError: バリデーションエラー
            ValueError: データ形式エラー
        """
        rows: List[CSVRow] = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # 必須カラムの確認
            required_columns = ['role', 'name', 'is_alive']
            fieldnames = reader.fieldnames if reader.fieldnames is not None else []
            if not all(col in fieldnames for col in required_columns):
                raise ValidationError(
                    f"必須カラムが不足しています。必要: {required_columns}"
                )

            for i, csv_dict in enumerate(reader, start=2):  # ヘッダー行の次から
                try:
                    csv_row = CSVRow(
                        role=csv_dict['role'].strip().lower(),
                        name=csv_dict['name'].strip(),
                        is_alive=cls.parse_bool(csv_dict['is_alive']),
                        birth_date=cls.parse_date(csv_dict.get('birth_date', '')),
                        death_date=cls.parse_date(csv_dict.get('death_date', '')),
                        blood_type=csv_dict.get('blood_type', '').strip().lower() if csv_dict.get('blood_type') else None,
                        is_renounced=cls.parse_bool(csv_dict.get('is_renounced', 'いいえ'))
                    )
                    rows.append(csv_row)
                except Exception as e:
                    raise ValidationError(f"行{i}のパースエラー: {str(e)}") from e

        # 被相続人の検索
        decedent_rows = [r for r in rows if r.role == 'decedent']
        if len(decedent_rows) == 0:
            raise ValidationError("被相続人（decedent）が見つかりません")
        if len(decedent_rows) > 1:
            raise ValidationError("被相続人（decedent）は1人のみ指定してください")

        decedent_row = decedent_rows[0]
        decedent = Person(
            name=decedent_row.name,
            is_decedent=True,
            is_alive=False,  # 被相続人は必ず死亡
            birth_date=decedent_row.birth_date,
            death_date=decedent_row.death_date
        )

        # 各役割ごとに人物を作成
        spouses: List[Person] = []
        children: List[Person] = []
        parents: List[Person] = []
        siblings: List[Person] = []
        renounced: List[Person] = []
        sibling_blood_types: Dict[str, BloodType] = {}

        for row in rows:
            if row.role == 'decedent':
                continue

            person = Person(
                name=row.name,
                is_alive=row.is_alive,
                birth_date=row.birth_date,
                death_date=row.death_date
            )

            # 役割ごとに分類
            if row.role == 'spouse':
                spouses.append(person)
            elif row.role == 'child':
                children.append(person)
            elif row.role == 'parent':
                parents.append(person)
            elif row.role == 'sibling':
                siblings.append(person)
                # 血縁タイプの設定
                if row.blood_type:
                    if row.blood_type == 'full':
                        sibling_blood_types[str(person.id)] = BloodType.FULL
                    elif row.blood_type == 'half':
                        sibling_blood_types[str(person.id)] = BloodType.HALF
                    else:
                        raise ValidationError(
                            f"無効な血縁タイプです（{row.name}）: {row.blood_type}"
                        )
                else:
                    # デフォルトは全血
                    sibling_blood_types[str(person.id)] = BloodType.FULL
            else:
                raise ValidationError(f"無効な役割です: {row.role}")

            # 相続放棄の記録
            if row.is_renounced:
                renounced.append(person)

        return decedent, spouses, children, parents, siblings, renounced, sibling_blood_types

    @staticmethod
    def create_template_csv(file_path: Path) -> None:
        """テンプレートCSVファイルを作成

        Args:
            file_path: 出力先ファイルパス
        """
        headers = [
            'role',
            'name',
            'is_alive',
            'birth_date',
            'death_date',
            'blood_type',
            'is_renounced'
        ]

        sample_rows = [
            {
                'role': 'decedent',
                'name': '山田太郎',
                'is_alive': 'いいえ',
                'birth_date': '1950-01-01',
                'death_date': '2025-06-15',
                'blood_type': '',
                'is_renounced': 'いいえ'
            },
            {
                'role': 'spouse',
                'name': '山田花子',
                'is_alive': 'はい',
                'birth_date': '1955-03-10',
                'death_date': '',
                'blood_type': '',
                'is_renounced': 'いいえ'
            },
            {
                'role': 'child',
                'name': '山田一郎',
                'is_alive': 'はい',
                'birth_date': '1980-05-20',
                'death_date': '',
                'blood_type': '',
                'is_renounced': 'いいえ'
            },
        ]

        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(sample_rows)
