# デモスクリプト

このディレクトリには、相続計算機の各機能をデモンストレーションするスクリプトが含まれています。

## 📋 デモスクリプト一覧

### 1. `demo_basic_cases.py` - 基本的な相続ケース

基本的な相続パターンをデモンストレーションします。

```bash
uv run python examples/demo_basic_cases.py
```

**デモ内容:**
- 配偶者と子のケース
- 配偶者と直系尊属のケース
- 配偶者と兄弟姉妹のケース
- 配偶者のみのケース

### 2. `demo_complex_cases.py` - 複雑な相続ケース

代襲相続や特殊ケースをデモンストレーションします。

```bash
uv run python examples/demo_complex_cases.py
```

**デモ内容:**
- 代襲相続（子の代襲）
- 代襲相続（兄弟姉妹の代襲）
- 半血兄弟姉妹
- 相続放棄
- 再転相続

### 3. `demo_interactive.py` - 対話型デモ

対話型インターフェースをデモンストレーションします。

```bash
uv run python examples/demo_interactive.py
```

**デモ内容:**
- ステップバイステップの入力
- 対話型プロンプト
- リアルタイム計算

### 4. `demo_contact_collection.py` - 連絡先情報収集 **[NEW]**

連絡先情報収集機能をデモンストレーションします。

```bash
uv run python examples/demo_contact_collection.py
```

**デモ内容:**
- 相続計算後の連絡先情報収集
- 住所、電話番号、メールアドレスの入力
- バリデーション機能
- 連絡先サマリー表示
- 各種レポート生成（Markdown, PDF, CSV）

**実行例:**

```
Step 1: サンプル相続ケースの作成
被相続人: 山田太郎（故人）
相続人: 山田花子（配偶者）、山田一郎（子）、山田二郎（子）

Step 2: 相続計算結果の表示
[相続計算結果テーブル表示]

Step 3: 連絡先情報の収集
相続人の連絡先情報を入力しますか？ [y/n] (y): y

【山田花子】の連絡先情報
住所: 東京都渋谷区渋谷1-1-1
電話番号: 03-1234-5678
メールアドレス: hanako@example.com
✓ 連絡先情報を登録しました

【山田一郎】の連絡先情報
...

Step 4: 連絡先サマリーの表示
[連絡先情報テーブル表示]

Step 5: レポート生成
✓ Markdownレポート: output/contact_demo_report.md
✓ PDFレポート: output/contact_demo_report.pdf
✓ CSV連絡先: output/contact_demo_contacts.csv

✓ デモ完了！
```

## 📂 サンプルデータ

`data/` ディレクトリには、デモで使用するサンプルデータファイルが含まれています。

### JSON形式

```bash
# 基本ケース
examples/data/basic_case.json

# 代襲相続ケース
examples/data/substitution_case.json

# 複雑ケース
examples/data/complex_case.json
```

### CSV形式

```bash
# CSVテンプレート
examples/data/template.csv

# サンプルケース
examples/data/sample_case.csv
```

## 🚀 クイックスタート

### 1. すべてのデモを順番に実行

```bash
# 基本ケース
uv run python examples/demo_basic_cases.py

# 複雑ケース
uv run python examples/demo_complex_cases.py

# 対話型デモ
uv run python examples/demo_interactive.py

# 連絡先収集デモ（NEW）
uv run python examples/demo_contact_collection.py
```

### 2. 特定のケースのみ実行

CLIコマンドを使用して特定のデータファイルから計算できます。

```bash
# JSONファイルから
uv run python -m src.cli.main calc -i examples/data/basic_case.json -o output/result.md

# CSVファイルから
uv run python -m src.cli.main calc -i examples/data/sample_case.csv -o output/result.pdf
```

### 3. 連絡先情報付きレポート生成

```bash
# 計算 → 連絡先収集 → レポート生成（自動）
uv run python -m src.cli.main calc -i examples/data/basic_case.json -o output/report.pdf

# PDFレポート生成時に連絡先CSVもエクスポート
# → プロンプトで "y" を選択
```

## 📝 カスタムデモの作成

独自のデモスクリプトを作成する場合の基本テンプレート:

```python
from datetime import date
from fractions import Fraction

from src.models.person import Person
from src.models.inheritance import InheritanceResult, Heir, HeritageRank, SubstitutionType
from src.services.inheritance_calculator import InheritanceCalculator
from src.cli.contact_input import ContactInfoCollector
from src.cli.report_generator import ReportGenerator
from src.cli.display import display_result

def main():
    # 1. 被相続人と相続人候補の作成
    decedent = Person(
        name="被相続人",
        is_decedent=True,
        is_alive=False,
        death_date=date(2025, 6, 15)
    )

    spouse = Person(name="配偶者", is_alive=True)
    child = Person(name="子", is_alive=True)

    # 2. 相続計算
    calculator = InheritanceCalculator()
    result = calculator.calculate(
        decedent=decedent,
        spouses=[spouse],
        children=[child],
        parents=[],
        siblings=[]
    )

    # 3. 結果表示
    display_result(result)

    # 4. 連絡先情報収集
    collector = ContactInfoCollector()
    updated_persons = collector.collect_contact_info_for_heirs(result)

    # 5. レポート生成
    if updated_persons:
        ReportGenerator.generate_pdf(result, Path("output/my_report.pdf"))
        ReportGenerator.export_contact_csv(result, Path("output/contacts.csv"))

if __name__ == "__main__":
    main()
```

## 🔍 トラブルシューティング

### 問題: デモスクリプトが実行できない

**原因**: 依存関係がインストールされていない

**解決方法**:

```bash
# 依存関係のインストール
uv sync

# 仮想環境の有効化を確認
uv run python --version
```

### 問題: 連絡先入力プロンプトが表示されない

**原因**: 非対話環境（パイプやリダイレクト）で実行している

**解決方法**:

対話シェルから直接実行してください:

```bash
# 正しい実行方法
uv run python examples/demo_contact_collection.py

# 誤った実行方法（プロンプトが表示されない）
echo "y" | uv run python examples/demo_contact_collection.py
```

### 問題: PDF生成でフォントエラー

**原因**: IPAフォントが見つからない

**解決方法**:

ReportGeneratorは自動的にIPAフォントをダウンロードしますが、手動インストールも可能です:

```bash
# macOS
brew install ipa-fonts

# Ubuntu/Debian
sudo apt-get install fonts-ipafont
```

## 📚 関連ドキュメント

- [ユーザーガイド](../docs/user_guide.md) - 詳細な使い方
- [アーキテクチャ設計書](../docs/architecture.md) - システム設計
- [CLAUDE.md](../CLAUDE.md) - プロジェクト仕様書

---

**最終更新日**: 2025年10月17日
