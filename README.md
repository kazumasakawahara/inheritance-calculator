# 相続計算機 (Inheritance Calculator)

日本の民法に基づく相続人の資格確定と相続割合（法定相続分）の計算を自動化するアプリケーション。

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage: 75%](https://img.shields.io/badge/coverage-75%25-brightgreen.svg)](https://github.com/your-org/inheritance-calculator)

## 📋 特徴

- ✅ **日本の民法準拠**: 民法第5編「相続」に完全準拠した計算
- 🔢 **正確な相続割合計算**: 分数演算による精密な相続分計算
- 🌳 **複雑なケース対応**: 代襲相続、相続放棄、半血兄弟姉妹の処理
- 💻 **使いやすいCLI**: Rich libraryによる美しいコマンドラインインターフェース
- 📁 **柔軟な入出力**: JSON/CSV形式での入力・出力、対話型モード
- 🧪 **高品質**: 130件のテスト、75%のカバレッジ

## 🎯 対応ケース

### 基本ケース
- 配偶者のみ
- 配偶者と子
- 配偶者と直系尊属（父母・祖父母）
- 配偶者と兄弟姉妹
- 子のみ、直系尊属のみ、兄弟姉妹のみ

### 複雑ケース
- **代襲相続**: 子の代襲（無制限）、兄弟姉妹の代襲（1代限り）
- **再転相続**: 遺産分割前に相続人が死亡した場合の処理
- **相続放棄**: 次順位への移行処理
- **半血兄弟姉妹**: 全血の1/2の相続分計算
- **混合ケース**: 上記の組み合わせ

## 🚀 クイックスタート

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/inheritance-calculator.git
cd inheritance-calculator

# uvを使った依存関係のインストール
uv sync
```

### 基本的な使い方

#### 1. 対話型モード

```bash
uv run python -m src.cli.main calculate
```

対話形式で相続情報を入力し、計算結果を表示します。

#### 2. ファイルからの計算

```bash
# JSONファイルから計算
uv run python -m src.cli.main calculate -i examples/sample_input.json

# CSVファイルから計算
uv run python -m src.cli.main calculate -i examples/sample_csv_basic.csv

# 結果を出力（形式は拡張子で自動判定）
uv run python -m src.cli.main calculate -i examples/sample_input.json -o result.json  # JSON形式
uv run python -m src.cli.main calculate -i examples/sample_csv_basic.csv -o report.md  # Markdown形式
uv run python -m src.cli.main calculate -i examples/sample_csv_basic.csv -o report.pdf  # PDF形式
```

#### 3. CSVテンプレートの作成

```bash
# CSVテンプレートファイルを生成
uv run python -m src.cli.main template examples/my_case.csv
```

生成されたCSVファイルを編集して相続情報を入力できます。

#### 4. 家系図の生成

```bash
# テキスト形式の家系図
uv run python -m src.cli.main tree -i examples/sample_csv_basic.csv -o family_tree.txt

# Mermaid形式の家系図（GitHub/Mermaid対応エディタで表示）
uv run python -m src.cli.main tree -i examples/sample_csv_basic.csv -o family_tree.mmd

# Graphviz形式（要Graphvizインストール）
uv run python -m src.cli.main tree -i examples/sample_csv_basic.csv -o family_tree.png
```

#### 5. デモ実行

```bash
# 基本ケースのデモ
uv run python -m src.cli.main demo basic

# 複雑ケースのデモ
uv run python -m src.cli.main demo complex

# 対話型デモ
uv run python -m src.cli.main demo interactive
```

## 📖 詳細な使い方

### CLIコマンド

#### calculate (calc)
相続計算を実行します。

```bash
# 対話モード
uv run python -m src.cli.main calculate

# ファイル入力モード
uv run python -m src.cli.main calc -i input.json -o output.json
```

**オプション:**
- `-i, --input`: 入力ファイルのパス（JSON or CSV）
- `-o, --output`: 出力ファイルのパス（JSON, Markdown, PDF）

**対応入力形式:**
- `.json`: JSON形式
- `.csv`: CSV形式

**対応出力形式:**
- `.json`: JSON形式（構造化データ）
- `.md`: Markdown形式（可読性の高いレポート）
- `.pdf`: PDF形式（印刷・配布用レポート）

#### template
CSVテンプレートファイルを作成します。

```bash
uv run python -m src.cli.main template output.csv
```

作成されたテンプレートを編集して相続情報を入力できます。

#### tree
家系図を生成します。

```bash
# テキスト形式
uv run python -m src.cli.main tree -i input.csv -o tree.txt

# Mermaid形式
uv run python -m src.cli.main tree -i input.json -o tree.mmd

# Graphviz形式（要システムにGraphvizインストール）
uv run python -m src.cli.main tree -i input.csv -o tree.png
```

**オプション:**
- `-i, --input`: 入力ファイルのパス（JSON or CSV）
- `-o, --output`: 出力ファイルのパス

**対応出力形式:**
- `.txt`: テキスト形式（コンソールで確認可能）
- `.mmd`: Mermaid形式（GitHubやMermaid対応エディタで表示）
- `.png`, `.pdf`, `.svg`: Graphviz形式（要システムにGraphvizインストール）

#### validate
入力JSONファイルを検証します。

```bash
uv run python -m src.cli.main validate examples/sample_input.json
```

#### demo
デモを実行します。

```bash
uv run python -m src.cli.main demo [basic|complex|interactive]
```

#### version
バージョン情報を表示します。

```bash
uv run python -m src.cli.main version
```

### 入力ファイル形式

#### JSONフォーマット

```json
{
  "decedent": {
    "name": "山田太郎",
    "birth_date": "1950-01-01",
    "death_date": "2025-06-15"
  },
  "spouses": [
    {
      "name": "山田花子",
      "is_alive": true,
      "birth_date": "1955-03-10"
    }
  ],
  "children": [
    {
      "name": "山田一郎",
      "is_alive": true,
      "birth_date": "1980-05-20"
    }
  ],
  "parents": [],
  "siblings": [],
  "renounced": []
}
```

#### CSVフォーマット

CSVファイルは以下の列で構成されます：

| 列名 | 必須 | 説明 | 例 |
|------|------|------|-----|
| role | ✅ | 役割 | decedent, spouse, child, parent, sibling |
| name | ✅ | 氏名 | 山田太郎 |
| is_alive | ✅ | 生存状態 | はい/いいえ, yes/no, 1/0, 存命/死亡 |
| birth_date | - | 生年月日 | 1950-01-01, 1950/01/01, 1950年01月01日 |
| death_date | - | 死亡日 | 2025-06-15 |
| blood_type | - | 血縁タイプ（兄弟姉妹のみ） | full（全血）, half（半血） |
| is_renounced | - | 相続放棄 | はい/いいえ（デフォルト: いいえ） |

**サンプルCSV:**
```csv
role,name,is_alive,birth_date,death_date,blood_type,is_renounced
decedent,山田太郎,いいえ,1950-01-01,2025-06-15,,いいえ
spouse,山田花子,はい,1955-03-10,,,いいえ
child,山田一郎,はい,1980-05-20,,,いいえ
child,山田二郎,はい,1983-11-12,,,いいえ
```

### 出力例

```
╭──────────────╮
│ 相続計算結果 │
╰──────────────╯

                    相続人と相続割合
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ 氏名           ┃ 続柄   ┃ 相続順位┃ 相続割合(分数)┃ 相続割合(%)┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 山田花子(70歳) │ spouse │ 配偶者  │ 1/2          │ 50.00%   │
│ 山田一郎(45歳) │ first  │ 第1順位 │ 1/2          │ 50.00%   │
└────────────────┴────────┴────────┴──────────────┴──────────┘

計算根拠:
  • 民法890条（配偶者の相続権）
  • 民法887条1項（子の相続権）
  • 民法900条1号（配偶者1/2、子1/2）
```

## 🏗️ プロジェクト構造

```
inheritance-calculator/
├── src/
│   ├── models/          # データモデル（Person, Relationship, InheritanceResult）
│   ├── services/        # ビジネスロジック（相続計算、相続人判定）
│   ├── cli/             # CLIインターフェース
│   └── utils/           # ユーティリティ（設定、ログ、例外）
├── tests/               # テストコード（130件）
├── examples/            # サンプル入力ファイル・デモスクリプト
└── docs/                # ドキュメント
```

## 🧪 テスト

```bash
# 全テスト実行
uv run pytest

# カバレッジレポート付き
uv run pytest --cov=src --cov-report=html

# 特定のテストのみ実行
uv run pytest tests/test_services/
```

## 📚 法的根拠

### 対応している民法条文

- **民法887条**: 子の相続権、代襲相続
- **民法889条**: 直系尊属・兄弟姉妹の相続権
- **民法890条**: 配偶者の相続権
- **民法896条**: 相続人の相続（再転相続）
- **民法900条**: 法定相続分
  - 1号: 配偶者と子（配偶者1/2、子1/2）
  - 2号: 配偶者と直系尊属（配偶者2/3、直系尊属1/3）
  - 3号: 配偶者と兄弟姉妹（配偶者3/4、兄弟姉妹1/4）
  - 4号: 半血兄弟姉妹（全血の1/2）
- **民法901条**: 代襲相続人の相続分
- **民法938条-940条**: 相続放棄

## 📄 詳細ドキュメント

- [CLAUDE.md](./CLAUDE.md) - プロジェクト仕様書
- [examples/](./examples/) - サンプル入力ファイルとデモスクリプト

## ⚠️ 免責事項

このアプリケーションは相続実務の補助ツールであり、法的助言を提供するものではありません。実際の相続手続きは専門家（弁護士、司法書士等）に相談してください。

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🤝 コントリビューション

バグ報告や機能提案は [Issues](https://github.com/your-org/inheritance-calculator/issues) へお願いします。

---

**バージョン**: 1.0.0
**開発状況**: Phase 6 (最適化とデプロイ準備) 完了
**最終更新**: 2025年10月3日
**開発**: Claude Code AI Assistant
