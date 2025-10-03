"""家系図生成のテスト"""
from pathlib import Path
from datetime import date
from fractions import Fraction

import pytest

from src.cli.family_tree_generator import FamilyTreeGenerator
from src.models.person import Person
from src.models.inheritance import InheritanceResult, Heir, HeritageRank, SubstitutionType


class TestFamilyTreeGenerator:
    """FamilyTreeGeneratorのテストクラス"""

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
            calculation_basis=[]
        )

    @pytest.fixture
    def substitution_result(self) -> InheritanceResult:
        """代襲相続を含む結果"""
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
                person=child,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                substitution_type=SubstitutionType.NONE
            ),
            Heir(
                person=grandchild,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                is_substitution=True,
                substitution_type=SubstitutionType.CHILD
            ),
        ]

        return InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=[]
        )

    def test_generate_text_tree(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """テキスト形式の家系図生成"""
        output_file = tmp_path / "tree.txt"
        FamilyTreeGenerator.generate_text_tree(sample_result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # 被相続人
        assert "山田太郎" in content
        assert "被相続人" in content

        # 配偶者
        assert "山田花子" in content
        assert "配偶者" in content

        # 子
        assert "山田一郎" in content
        assert "山田二郎" in content
        assert "子" in content

        # 相続割合
        assert "1/2" in content
        assert "1/4" in content

    def test_generate_mermaid_diagram(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """Mermaid形式の家系図生成"""
        output_file = tmp_path / "tree.mmd"
        FamilyTreeGenerator.generate_mermaid(sample_result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # Mermaidの基本構文
        assert "```mermaid" in content
        assert "graph TB" in content or "graph LR" in content

        # ノード定義
        assert "山田太郎" in content
        assert "山田花子" in content
        assert "山田一郎" in content
        assert "山田二郎" in content

        # スタイル定義
        assert "classDef decedent" in content
        assert "classDef spouse" in content
        assert "classDef child" in content

    def test_generate_graphviz_diagram(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """Graphviz形式の家系図生成"""
        # PNG形式で生成
        output_file = tmp_path / "tree.png"

        try:
            FamilyTreeGenerator.generate_graphviz(sample_result, output_file)
            assert output_file.exists()

            # PNGファイルのマジックナンバー確認
            with open(output_file, 'rb') as f:
                header = f.read(8)
                assert header == b'\x89PNG\r\n\x1a\n'
        except Exception as e:
            # Graphvizがインストールされていない場合はスキップ
            if "Graphviz" in str(e) or "graphviz" in str(e):
                pytest.skip("Graphvizがインストールされていません")
            raise

    def test_generate_text_tree_with_substitution(
        self, substitution_result: InheritanceResult, tmp_path: Path
    ) -> None:
        """代襲相続を含むテキスト家系図"""
        output_file = tmp_path / "substitution_tree.txt"
        FamilyTreeGenerator.generate_text_tree(substitution_result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # 代襲相続人
        assert "山田三郎" in content
        assert "代襲相続" in content or "孫" in content

    def test_generate_mermaid_with_substitution(
        self, substitution_result: InheritanceResult, tmp_path: Path
    ) -> None:
        """代襲相続を含むMermaid図"""
        output_file = tmp_path / "substitution.mmd"
        FamilyTreeGenerator.generate_mermaid(substitution_result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')

        # 代襲相続人のノード
        assert "山田三郎" in content

        # 代襲相続のスタイル
        assert "classDef substitute" in content

    def test_generate_graphviz_pdf(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """Graphviz PDF形式の生成"""
        output_file = tmp_path / "tree.pdf"

        try:
            FamilyTreeGenerator.generate_graphviz(sample_result, output_file)
            assert output_file.exists()

            # PDFファイルのマジックナンバー確認
            with open(output_file, 'rb') as f:
                header = f.read(4)
                assert header == b'%PDF'
        except Exception as e:
            if "Graphviz" in str(e) or "graphviz" in str(e):
                pytest.skip("Graphvizがインストールされていません")
            raise

    def test_generate_graphviz_svg(self, sample_result: InheritanceResult, tmp_path: Path) -> None:
        """Graphviz SVG形式の生成"""
        output_file = tmp_path / "tree.svg"

        try:
            FamilyTreeGenerator.generate_graphviz(sample_result, output_file)
            assert output_file.exists()

            content = output_file.read_text(encoding='utf-8')
            assert '<svg' in content
            assert '</svg>' in content
        except Exception as e:
            if "Graphviz" in str(e) or "graphviz" in str(e):
                pytest.skip("Graphvizがインストールされていません")
            raise

    def test_empty_heirs(self, tmp_path: Path) -> None:
        """相続人がいない場合"""
        decedent = Person(
            name="山田太郎",
            is_decedent=True,
            is_alive=False
        )

        result = InheritanceResult(
            decedent=decedent,
            heirs=[],
            calculation_basis=[]
        )

        output_file = tmp_path / "empty.txt"
        FamilyTreeGenerator.generate_text_tree(result, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "山田太郎" in content
