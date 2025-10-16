"""ASCIIアート家系図生成のテスト"""
from datetime import date
from fractions import Fraction

import pytest

from src.cli.ascii_tree import AsciiTreeGenerator
from inheritance_calculator_core.models.person import Person, Gender
from inheritance_calculator_core.models.inheritance import InheritanceResult, Heir, HeritageRank


class TestAsciiTreeGenerator:
    """AsciiTreeGeneratorクラスのテスト"""

    @pytest.fixture
    def generator(self):
        """テスト用AsciiTreeGenerator"""
        return AsciiTreeGenerator()

    @pytest.fixture
    def simple_result(self):
        """シンプルな相続ケース"""
        decedent = Person(
            name="山田太郎",
            is_alive=False,
            is_decedent=True,
            death_date=date(2025, 6, 15)
        )
        spouse = Person(name="山田花子", is_alive=True, gender=Gender.FEMALE)
        child = Person(name="山田一郎", is_alive=True, gender=Gender.MALE)

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 2),
                share_percentage=50.0
            ),
            Heir(
                person=child,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 2),
                share_percentage=50.0
            )
        ]

        return InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            has_spouse=True,
            has_children=True,
            calculation_basis=["配偶者と子の相続"]
        )

    @pytest.fixture
    def complex_result(self):
        """複雑な相続ケース（代襲相続含む）"""
        decedent = Person(name="山田太郎", is_alive=False, is_decedent=True)
        spouse = Person(name="山田花子", is_alive=True, gender=Gender.FEMALE)
        child1 = Person(name="山田一郎", is_alive=True, gender=Gender.MALE)
        grandchild = Person(name="山田次郎", is_alive=True, gender=Gender.MALE)

        heirs = [
            Heir(
                person=spouse,
                rank=HeritageRank.SPOUSE,
                share=Fraction(1, 2),
                share_percentage=50.0
            ),
            Heir(
                person=child1,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0
            ),
            Heir(
                person=grandchild,
                rank=HeritageRank.FIRST,
                share=Fraction(1, 4),
                share_percentage=25.0,
                is_substitution=True
            )
        ]

        return InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            has_spouse=True,
            has_children=True,
            calculation_basis=["配偶者と子の相続", "代襲相続が発生"]
        )

    def test_initialization(self, generator):
        """初期化テスト"""
        assert generator.max_width == 80

    def test_initialization_custom_width(self):
        """カスタム幅での初期化テスト"""
        generator = AsciiTreeGenerator(max_width=100)
        assert generator.max_width == 100

    def test_generate_simple_tree(self, generator, simple_result):
        """シンプルな家系図生成テスト"""
        tree = generator.generate_simple_tree(simple_result)

        # 基本的な内容チェック
        assert tree is not None
        assert len(tree) > 0
        assert "家系図" in tree
        assert "山田太郎" in tree
        assert "山田花子" in tree
        assert "山田一郎" in tree
        assert "被相続人" in tree
        assert "配偶者" in tree

    def test_generate_simple_tree_with_substitution(self, generator, complex_result):
        """代襲相続を含む家系図生成テスト"""
        tree = generator.generate_simple_tree(complex_result)

        assert tree is not None
        assert "代襲" in tree
        assert "山田次郎" in tree

    def test_generate_detailed_tree(self, generator, simple_result):
        """詳細な家系図生成テスト"""
        tree = generator.generate_detailed_tree(simple_result)

        # 詳細版の特徴をチェック
        assert tree is not None
        assert "相続関係図（詳細版）" in tree
        assert "╔" in tree  # ボックス文字
        assert "═" in tree
        assert "相続人総数" in tree

    def test_generate_detailed_tree_structure(self, generator, simple_result):
        """詳細な家系図の構造テスト"""
        tree = generator.generate_detailed_tree(simple_result)

        # 構造要素のチェック
        assert "├─" in tree or "└─" in tree  # ツリー構造
        assert "💑" in tree  # 配偶者アイコン
        assert "👶" in tree  # 子アイコン

    def test_check_complexity_simple(self, generator, simple_result):
        """シンプルケースの複雑さチェック"""
        complexity = generator.check_complexity(simple_result)

        assert complexity["complexity"] == "simple"
        assert complexity["total_heirs"] == 2
        assert complexity["has_substitution"] is False
        assert "シンプル版" in complexity["recommendation"]

    def test_check_complexity_with_substitution(self, generator, complex_result):
        """代襲相続ありケースの複雑さチェック"""
        complexity = generator.check_complexity(complex_result)

        assert complexity["complexity"] == "moderate"
        assert complexity["total_heirs"] == 3
        assert complexity["has_substitution"] is True

    def test_check_complexity_many_heirs(self, generator):
        """多数の相続人がいるケースの複雑さチェック"""
        decedent = Person(name="被相続人", is_alive=False, is_decedent=True)

        # 10人の相続人を作成
        heirs = []
        for i in range(10):
            person = Person(name=f"相続人{i+1}", is_alive=True)
            heir = Heir(
                person=person,
                rank=HeritageRank.THIRD,
                share=Fraction(1, 10),
                share_percentage=10.0
            )
            heirs.append(heir)

        result = InheritanceResult(
            decedent=decedent,
            heirs=heirs,
            calculation_basis=["多数の相続人"]
        )

        complexity = generator.check_complexity(result)

        assert complexity["complexity"] == "complex"
        assert complexity["total_heirs"] == 10
        assert "Graphviz" in complexity["recommendation"]

    def test_tree_contains_shares(self, generator, simple_result):
        """家系図に相続割合が含まれるかテスト"""
        tree = generator.generate_simple_tree(simple_result)

        # 相続割合の表示をチェック
        assert "1/2" in tree or "50" in tree  # 分数またはパーセンテージ
        assert "%" in tree

    def test_tree_formatting(self, generator, simple_result):
        """家系図のフォーマットテスト"""
        tree = generator.generate_simple_tree(simple_result)

        # 各行が空ではないことを確認
        lines = tree.split("\n")
        assert len(lines) > 0

        # タイトル行の存在確認
        assert any("家系図" in line for line in lines)

    def test_detailed_tree_with_death_date(self, generator, simple_result):
        """死亡日付を含む詳細家系図テスト"""
        tree = generator.generate_detailed_tree(simple_result)

        # 死亡日が含まれることを確認
        assert "2025-06-15" in tree or "死亡日" in tree

    def test_tree_emoji_icons(self, generator, simple_result):
        """絵文字アイコンの使用テスト"""
        tree = generator.generate_simple_tree(simple_result)

        # 各種絵文字の存在確認
        assert "⚰️" in tree  # 被相続人
        assert "💑" in tree  # 配偶者
        assert "👶" in tree  # 子
