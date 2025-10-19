"""CSVパーサーのテスト"""
import tempfile
from pathlib import Path
from datetime import date

import pytest

from src.cli.csv_parser import CSVParser
from inheritance_calculator_core.models.relationship import BloodType
from inheritance_calculator_core.utils.exceptions import ValidationError


class TestCSVParser:
    """CSVParserのテストクラス"""

    def test_parse_date_valid_formats(self) -> None:
        """有効な日付フォーマットのパース"""
        # YYYY-MM-DD
        assert CSVParser.parse_date("2025-01-15") == date(2025, 1, 15)

        # YYYY/MM/DD
        assert CSVParser.parse_date("2025/01/15") == date(2025, 1, 15)

        # YYYY年MM月DD日
        assert CSVParser.parse_date("2025年01月15日") == date(2025, 1, 15)

        # 空文字列
        assert CSVParser.parse_date("") is None
        assert CSVParser.parse_date("  ") is None

    def test_parse_date_invalid_format(self) -> None:
        """無効な日付フォーマット"""
        with pytest.raises(ValueError, match="無効な日付形式です"):
            CSVParser.parse_date("2025-13-01")  # 無効な月

    def test_parse_bool_japanese(self) -> None:
        """日本語のboolean値"""
        assert CSVParser.parse_bool("はい") is True
        assert CSVParser.parse_bool("いいえ") is False
        assert CSVParser.parse_bool("存命") is True
        assert CSVParser.parse_bool("死亡") is False
        assert CSVParser.parse_bool("○") is True
        assert CSVParser.parse_bool("×") is False

    def test_parse_bool_english(self) -> None:
        """英語のboolean値"""
        assert CSVParser.parse_bool("yes") is True
        assert CSVParser.parse_bool("no") is False
        assert CSVParser.parse_bool("y") is True
        assert CSVParser.parse_bool("n") is False
        assert CSVParser.parse_bool("true") is True
        assert CSVParser.parse_bool("false") is False
        assert CSVParser.parse_bool("1") is True
        assert CSVParser.parse_bool("0") is False

    def test_parse_bool_invalid(self) -> None:
        """無効なboolean値"""
        with pytest.raises(ValueError, match="無効なboolean値です"):
            CSVParser.parse_bool("maybe")

    def test_parse_csv_file_basic(self, tmp_path: Path) -> None:
        """基本的なCSVファイルのパース"""
        csv_file = tmp_path / "test.csv"
        csv_content = """role,name,is_alive,birth_date,death_date,blood_type,is_renounced
decedent,山田太郎,いいえ,1950-01-01,2025-06-15,,いいえ
spouse,山田花子,はい,1955-03-10,,,いいえ
child,山田一郎,はい,1980-05-20,,,いいえ
child,山田二郎,はい,1983-11-12,,,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        decedent, spouses, children, parents, siblings, renounced, blood_types = \
            CSVParser.parse_csv_file(csv_file)

        # 被相続人
        assert decedent.name == "山田太郎"
        assert not decedent.is_alive
        assert decedent.birth_date == date(1950, 1, 1)
        assert decedent.death_date == date(2025, 6, 15)

        # 配偶者
        assert len(spouses) == 1
        assert spouses[0].name == "山田花子"
        assert spouses[0].is_alive

        # 子
        assert len(children) == 2
        assert children[0].name == "山田一郎"
        assert children[1].name == "山田二郎"

        # その他
        assert len(parents) == 0
        assert len(siblings) == 0
        assert len(renounced) == 0

    def test_parse_csv_file_with_siblings(self, tmp_path: Path) -> None:
        """兄弟姉妹を含むCSV"""
        csv_file = tmp_path / "test.csv"
        csv_content = """role,name,is_alive,birth_date,death_date,blood_type,is_renounced
decedent,山田太郎,いいえ,1950-01-01,2025-06-15,,いいえ
sibling,山田次郎,はい,1952-03-10,,full,いいえ
sibling,田中三郎,はい,1955-05-20,,half,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        decedent, spouses, children, parents, siblings, renounced, blood_types = \
            CSVParser.parse_csv_file(csv_file)

        assert len(siblings) == 2

        # 血縁タイプの確認
        assert blood_types[siblings[0].id] == BloodType.FULL
        assert blood_types[siblings[1].id] == BloodType.HALF

    def test_parse_csv_file_with_renounced(self, tmp_path: Path) -> None:
        """相続放棄を含むCSV"""
        csv_file = tmp_path / "test.csv"
        csv_content = """role,name,is_alive,birth_date,death_date,blood_type,is_renounced
decedent,山田太郎,いいえ,1950-01-01,2025-06-15,,いいえ
child,山田一郎,はい,1980-05-20,,いいえ,はい
child,山田二郎,はい,1983-11-12,,いいえ,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        decedent, spouses, children, parents, siblings, renounced, blood_types = \
            CSVParser.parse_csv_file(csv_file)

        assert len(children) == 2
        assert len(renounced) == 1
        assert renounced[0].name == "山田一郎"

    def test_parse_csv_file_missing_required_columns(self, tmp_path: Path) -> None:
        """必須カラムが不足しているCSV"""
        csv_file = tmp_path / "test.csv"
        csv_content = """name,is_alive
山田太郎,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        with pytest.raises(ValidationError, match="必須カラムが不足しています"):
            CSVParser.parse_csv_file(csv_file)

    def test_parse_csv_file_no_decedent(self, tmp_path: Path) -> None:
        """被相続人がいない場合"""
        csv_file = tmp_path / "test.csv"
        csv_content = """role,name,is_alive,birth_date,death_date,blood_type,is_renounced
spouse,山田花子,はい,1955-03-10,,,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        with pytest.raises(ValidationError, match="被相続人（decedent）が見つかりません"):
            CSVParser.parse_csv_file(csv_file)

    def test_parse_csv_file_multiple_decedents(self, tmp_path: Path) -> None:
        """複数の被相続人がいる場合"""
        csv_file = tmp_path / "test.csv"
        csv_content = """role,name,is_alive,birth_date,death_date,blood_type,is_renounced
decedent,山田太郎,いいえ,1950-01-01,2025-06-15,,いいえ
decedent,田中次郎,いいえ,1952-03-10,2025-07-20,,いいえ
"""
        csv_file.write_text(csv_content, encoding='utf-8')

        with pytest.raises(ValidationError, match="被相続人（decedent）は1人のみ指定してください"):
            CSVParser.parse_csv_file(csv_file)

    def test_create_template_csv(self, tmp_path: Path) -> None:
        """テンプレートCSVの作成"""
        output_file = tmp_path / "template.csv"
        CSVParser.create_template_csv(output_file)

        assert output_file.exists()

        # ヘッダー行の確認
        content = output_file.read_text(encoding='utf-8-sig')
        assert 'role,name,is_alive,birth_date,death_date,blood_type,is_renounced' in content

        # サンプルデータの確認
        assert '山田太郎' in content
        assert '山田花子' in content
        assert '山田一郎' in content
