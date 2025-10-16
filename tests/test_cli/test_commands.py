"""CLIコマンドのテスト"""
import json
from pathlib import Path
from datetime import date
import pytest
from unittest.mock import Mock, patch

from src.cli.commands import (
    calculate_from_file,
    export_result,
    validate_command,
)
from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.models.inheritance import InheritanceResult, Heir, HeritageRank
from fractions import Fraction


@pytest.fixture
def sample_input_file(tmp_path):
    """サンプル入力ファイルを作成"""
    input_data = {
        "decedent": {
            "name": "山田太郎",
            "birth_date": "1950-01-01",
            "death_date": "2025-06-15"
        },
        "spouses": [
            {
                "name": "山田花子",
                "is_alive": True,
                "birth_date": "1955-03-10"
            }
        ],
        "children": [
            {
                "name": "山田一郎",
                "is_alive": True,
                "birth_date": "1980-05-20"
            }
        ],
        "parents": [],
        "siblings": [],
        "renounced": []
    }

    file_path = tmp_path / "test_input.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(input_data, f, ensure_ascii=False)

    return file_path


@pytest.fixture
def sample_result():
    """サンプル相続計算結果を作成"""
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

    heirs = [
        Heir(person=spouse, rank=HeritageRank.SPOUSE, share=Fraction(1, 2), share_percentage=50.0),
        Heir(person=child, rank=HeritageRank.FIRST, share=Fraction(1, 2), share_percentage=50.0),
    ]

    return InheritanceResult(
        decedent=decedent,
        heirs=heirs,
        calculation_basis=["民法890条", "民法887条1項", "民法900条1号"]
    )


class TestCalculateFromFile:
    """calculate_from_file関数のテスト"""

    def test_calculate_from_file_success(self, sample_input_file, capsys):
        """正常な入力ファイルからの計算"""
        result = calculate_from_file(sample_input_file)

        assert result == 0  # 成功

        # 出力を確認
        captured = capsys.readouterr()
        assert "山田太郎" in captured.out
        assert "山田花子" in captured.out
        assert "山田一郎" in captured.out
        assert "相続計算結果" in captured.out

    def test_calculate_from_file_with_output(self, sample_input_file, tmp_path, capsys):
        """出力ファイル指定ありの計算"""
        output_file = tmp_path / "output.json"

        result = calculate_from_file(sample_input_file, output_file)

        assert result == 0
        assert output_file.exists()

        # 出力ファイルの内容を確認
        with open(output_file, 'r', encoding='utf-8') as f:
            output_data = json.load(f)

        assert "decedent" in output_data
        assert "heirs" in output_data
        assert output_data["total_heirs"] == 2

        # メッセージ確認
        captured = capsys.readouterr()
        assert "出力しました" in captured.out

    def test_calculate_from_file_not_found(self, tmp_path, capsys):
        """存在しないファイル"""
        non_existent = tmp_path / "non_existent.json"

        result = calculate_from_file(non_existent)

        assert result == 1  # エラー

        captured = capsys.readouterr()
        assert "ファイルが見つかりません" in captured.out

    def test_calculate_from_file_invalid_json(self, tmp_path, capsys):
        """無効なJSON"""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json")

        result = calculate_from_file(invalid_file)

        assert result == 1

        captured = capsys.readouterr()
        assert "JSON" in captured.out
        assert "解析エラー" in captured.out

    def test_calculate_from_file_missing_field(self, tmp_path, capsys):
        """必須フィールド不足"""
        incomplete_file = tmp_path / "incomplete.json"
        with open(incomplete_file, 'w', encoding='utf-8') as f:
            json.dump({"spouses": []}, f)  # decedentフィールドなし

        result = calculate_from_file(incomplete_file)

        assert result == 1

        captured = capsys.readouterr()
        assert "必須フィールド" in captured.out


class TestExportResult:
    """export_result関数のテスト"""

    def test_export_result_json(self, sample_result, tmp_path):
        """JSON形式での結果エクスポート"""
        output_file = tmp_path / "result.json"

        export_result(sample_result, output_file)

        assert output_file.exists()

        # ファイル内容を確認
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["total_heirs"] == 2
        # has_spouseとhas_childrenは実際のheirs内容から計算される
        assert len(data["heirs"]) == 2
        assert len(data["calculation_basis"]) == 3

        # 相続人情報を確認
        heir_names = [h["name"] for h in data["heirs"]]
        assert any("山田花子" in name for name in heir_names)
        assert any("山田一郎" in name for name in heir_names)

    def test_export_result_share_format(self, sample_result, tmp_path):
        """相続割合の形式確認"""
        output_file = tmp_path / "result.json"

        export_result(sample_result, output_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 分数と百分率の確認
        for heir in data["heirs"]:
            assert "share" in heir
            assert "share_percentage" in heir
            assert "/" in heir["share"]  # 分数形式
            assert isinstance(heir["share_percentage"], (int, float))


class TestValidateCommand:
    """validate_command関数のテスト"""

    def test_validate_valid_file(self, sample_input_file, capsys):
        """有効なファイルの検証"""
        args = Mock(input_file=sample_input_file)

        result = validate_command(args)

        assert result == 0

        captured = capsys.readouterr()
        assert "有効な入力ファイル" in captured.out

    def test_validate_missing_decedent(self, tmp_path, capsys):
        """被相続人情報なし"""
        invalid_file = tmp_path / "no_decedent.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump({"spouses": []}, f)

        args = Mock(input_file=invalid_file)
        result = validate_command(args)

        assert result == 1

        captured = capsys.readouterr()
        assert "必須フィールド" in captured.out

    def test_validate_missing_name(self, tmp_path, capsys):
        """被相続人の氏名なし"""
        invalid_file = tmp_path / "no_name.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump({"decedent": {"death_date": "2025-06-15"}}, f)

        args = Mock(input_file=invalid_file)
        result = validate_command(args)

        assert result == 1

        captured = capsys.readouterr()
        assert "氏名が不足" in captured.out

    def test_validate_missing_death_date(self, tmp_path, capsys):
        """被相続人の死亡日なし"""
        invalid_file = tmp_path / "no_death_date.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump({"decedent": {"name": "山田太郎"}}, f)

        args = Mock(input_file=invalid_file)
        result = validate_command(args)

        assert result == 1

        captured = capsys.readouterr()
        assert "死亡日が不足" in captured.out

    def test_validate_not_found(self, tmp_path, capsys):
        """ファイルが存在しない"""
        non_existent = tmp_path / "non_existent.json"

        args = Mock(input_file=non_existent)
        result = validate_command(args)

        assert result == 1

        captured = capsys.readouterr()
        assert "ファイルが見つかりません" in captured.out
