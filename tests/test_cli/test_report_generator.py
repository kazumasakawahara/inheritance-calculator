"""レポート生成のテスト"""
from pathlib import Path
from datetime import date
from fractions import Fraction

import pytest

from src.cli.report_generator import ReportGenerator
from src.models.person import Person
from src.models.inheritance import InheritanceResult, Heir, HeritageRank, SubstitutionType


class TestReportGenerator:
    """ReportGeneratorのテストクラス"""

    @pytest.fixture
    def sample_result(self) -> InheritanceResult:
        """サンプルの相続計算結果"""
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

        child1 = Person(
            name="山田一郎",
            is_alive=True,
            birth_date=date(1980, 5, 20)
        )

        child2 = Person(
            name="山田二郎",
            is_alive=True,
            birth_date=date(1983, 11, 12)
        )

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 2),
                share_percentage=50.0,
                substitution_type=SubstitutionType.NONE
            ),
            Heir(
                person=child1,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                substitution_type=SubstitutionType.NONE
            ),
            Heir(
                person=child2,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        return InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=[
                "民法890条（配偶者の相続権）",
                "民法887条1項（子の相続権）",
                "民法900条1号（配偶者1/2、子1/2）",
            ]
        )

    def test_generate_markdown(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """Markdownレポートの生成"""
        output_file = tmp_path / "report.md"
        ReportGenerator.generate_markdown(sample_result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # タイトル
        assert "# 相続計算レポート" in content

        # 被相続人情報
        assert "山田太郎" in content
        assert "1950" in content and "01" in content  # 日付フォーマットは年月日

        # 相続人情報
        assert "山田花子" in content
        assert "山田一郎" in content
        assert "山田二郎" in content

        # 相続割合
        assert "1/2" in content
        assert "1/4" in content

        # 計算根拠
        assert "民法890条" in content
        assert "民法887条1項" in content
        assert "民法900条1号" in content

    def test_generate_pdf(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """PDFレポートの生成"""
        output_file = tmp_path / "report.pdf"
        ReportGenerator.generate_pdf(sample_result, output_file)

        assert output_file.exists()

        # PDFファイルのマジックナンバー確認
        with open(output_file, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_generate_markdown_with_substitution(self, tmp_path: Path) -> None:
        """代襲相続を含むMarkdownレポート"""
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

        grandchild = Person(
            name="山田三郎",
            is_alive=True,
            birth_date=date(2005, 8, 15)
        )

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 2),
                share_percentage=50.0,
                substitution_type=SubstitutionType.NONE
            ),
            Heir(
                person=grandchild,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0,
                is_substitution=True,
                substitution_type=SubstitutionType.CHILD
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["民法887条2項（代襲相続）"]
        )

        output_file = tmp_path / "substitution.md"
        ReportGenerator.generate_markdown(result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # 代襲相続の表示確認
        assert "代襲相続" in content or "（孫）" in content

    def test_generate_pdf_with_long_names(self, tmp_path: Path) -> None:
        """長い名前を含むPDFレポート"""
        decedent = Person(
            name="非常に長い名前の被相続人さんです",
            is_decedent=True,
            is_alive=False
        )

        heir = Person(
            name="これも非常に長い名前の相続人さんです",
            is_alive=True
        )

        heirs = [
            Heir(
                person=heir,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 1),
                share_percentage=100.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["テスト"]
        )

        output_file = tmp_path / "long_names.pdf"

        # エラーなくPDFが生成されることを確認
        ReportGenerator.generate_pdf(result, output_file)
        assert output_file.exists()
