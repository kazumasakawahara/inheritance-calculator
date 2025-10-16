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

    def test_generate_markdown_with_contact_info(self, tmp_path: Path) -> None:
        """連絡先情報を含むMarkdownレポート"""
        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False,
            death_date=date(2025, 6, 15)
        )

        spouse = Person(
            name="山田花子",
            is_alive=True,
            address="東京都渋谷区渋谷1-1-1",
            phone="03-1234-5678",
            email="hanako@example.com"
        )

        child = Person(
            name="山田一郎",
            is_alive=True,
            address="大阪府大阪市北区梅田1-1-1",
            phone="06-9876-5432",
            email="ichiro@example.com"
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
                person=child,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["民法900条1号"]
        )

        output_file = tmp_path / "contact.md"
        ReportGenerator.generate_markdown(result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # 連絡先情報セクションの確認
        assert "相続人連絡先情報" in content
        assert "東京都渋谷区渋谷1-1-1" in content
        assert "03-1234-5678" in content
        assert "hanako@example.com" in content
        assert "大阪府大阪市北区梅田1-1-1" in content
        assert "06-9876-5432" in content
        assert "ichiro@example.com" in content

    def test_generate_pdf_with_contact_info(self, tmp_path: Path) -> None:
        """連絡先情報を含むPDFレポート"""
        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False
        )

        spouse = Person(
            name="山田花子",
            is_alive=True,
            address="愛知県名古屋市中区栄1-1-1",
            phone="052-123-4567",
            email="hanako@example.com"
        )

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 1),
                share_percentage=100.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["配偶者のみ"]
        )

        output_file = tmp_path / "contact.pdf"
        ReportGenerator.generate_pdf(result, output_file)

        assert output_file.exists()

        # PDFファイルのマジックナンバー確認
        with open(output_file, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_export_contact_csv(self, tmp_path: Path) -> None:
        """連絡先情報CSVエクスポート"""
        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False
        )

        spouse = Person(
            name="山田花子",
            is_alive=True,
            address="福岡県福岡市博多区博多駅前1-1-1",
            phone="092-111-2222",
            email="hanako@example.com"
        )

        child = Person(
            name="山田一郎",
            is_alive=True,
            address="北海道札幌市中央区北1条西1丁目",
            phone="011-333-4444",
            email="ichiro@example.com"
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
                person=child,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["民法900条1号"]
        )

        output_file = tmp_path / "contacts.csv"
        ReportGenerator.export_contact_csv(result, output_file)

        assert output_file.exists()

        # CSVの内容確認
        import csv
        with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

            # ヘッダー行
            assert rows[0] == ["氏名", "続柄", "相続順位", "相続割合（分数）", "相続割合（%）", "住所", "電話番号", "メールアドレス"]

            # データ行（2名の相続人）
            assert len(rows) == 3  # ヘッダー + 2データ行

            # 配偶者のデータ
            assert rows[1][0] == "山田花子"
            assert "福岡県福岡市博多区博多駅前1-1-1" in rows[1][5]
            assert "092-111-2222" in rows[1][6]
            assert "hanako@example.com" in rows[1][7]

            # 子のデータ
            assert rows[2][0] == "山田一郎"
            assert "北海道札幌市中央区北1条西1丁目" in rows[2][5]
            assert "011-333-4444" in rows[2][6]
            assert "ichiro@example.com" in rows[2][7]

    def test_export_contact_csv_no_contacts(self, tmp_path: Path) -> None:
        """連絡先情報がない場合のCSVエクスポート"""
        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False
        )

        spouse = Person(
            name="山田花子",
            is_alive=True
            # 連絡先情報なし
        )

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 1),
                share_percentage=100.0,
                substitution_type=SubstitutionType.NONE
            ),
        ]

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["配偶者のみ"]
        )

        output_file = tmp_path / "no_contacts.csv"
        ReportGenerator.export_contact_csv(result, output_file)

        assert output_file.exists()

        # CSVの内容確認
        import csv
        with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

            # 連絡先なしメッセージの確認
            assert "連絡先情報が登録されている相続人はありません" in rows[1][-1]
