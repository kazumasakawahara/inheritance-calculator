# 相続計算機 - ユーザーガイド

## 📋 目次

1. [概要](#概要)
2. [インストール](#インストール)
3. [基本的な使い方](#基本的な使い方)
4. [コマンドリファレンス](#コマンドリファレンス)
5. [連絡先情報の管理](#連絡先情報の管理)
6. [レポート生成](#レポート生成)
7. [Neo4jデータベース連携](#neo4jデータベース連携)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

相続計算機は、日本の民法に基づいた相続人の資格確定と相続割合の計算を自動化するアプリケーションです。

### 主な機能

- **相続人の資格判定**: 配偶者、子、直系尊属、兄弟姉妹の相続権を民法に基づいて判定
- **相続割合の計算**: 法定相続分を自動計算
- **代襲相続の処理**: 子の代襲相続（制限なし）、兄弟姉妹の代襲相続（1代限り）
- **特殊ケースの対応**: 相続放棄、相続欠格、相続廃除、再転相続
- **連絡先情報の管理**: 相続人の住所、電話番号、メールアドレスの管理
- **レポート生成**: Markdown、PDF、CSV形式でのレポート出力
- **Neo4jデータベース連携**: グラフデータベースによる相続関係の永続化

---

## インストール

### 前提条件

- Python 3.12以上
- uv（パッケージマネージャー）

### インストール手順

```bash
# リポジトリのクローン
git clone https://github.com/your-org/inheritance-calculator.git
cd inheritance-calculator

# 依存関係のインストール
uv sync

# 環境変数の設定（オプション）
cp .env.example .env
# .envファイルを編集してNeo4j接続情報などを設定
```

---

## 基本的な使い方

### 1. ファイルからの計算

#### JSON形式

```bash
uv run python -m src.cli.main calc -i examples/data/basic_case.json
```

#### CSV形式

```bash
uv run python -m src.cli.main calc -i examples/data/basic_case.csv
```

### 2. 対話モード

```bash
uv run python -m src.cli.main calc
```

対話モードでは、順次質問に答えることで相続計算を実行できます。

---

## コマンドリファレンス

### `calc` - 相続計算

相続人の資格確定と相続割合を計算します。

```bash
uv run python -m src.cli.main calc [OPTIONS]
```

**オプション:**

- `-i, --input FILE`: 入力ファイル（JSON/CSV）
- `-o, --output FILE`: 出力ファイル（JSON/Markdown/PDF/CSV）
- `--save-to-neo4j`: Neo4jに保存

**使用例:**

```bash
# JSONファイルから計算してMarkdownレポート生成
uv run python -m src.cli.main calc -i case.json -o report.md

# CSVファイルから計算してPDFレポート生成
uv run python -m src.cli.main calc -i case.csv -o report.pdf

# 対話モードで計算してNeo4jに保存
uv run python -m src.cli.main calc --save-to-neo4j
```

### `validate` - 入力ファイル検証

入力JSONファイルの形式を検証します。

```bash
uv run python -m src.cli.main validate -i FILE
```

### `template` - テンプレート生成

CSVテンプレートファイルを生成します。

```bash
uv run python -m src.cli.main template -o template.csv
```

### `tree` - 家系図生成

相続関係の家系図を生成します。

```bash
uv run python -m src.cli.main tree -i case.json -o family_tree.png
```

**サポート形式:**

- `.txt`: テキスト形式
- `.mmd` / `.md`: Mermaid形式
- `.png` / `.pdf` / `.svg`: Graphviz画像形式

### `interview` - AI対話型インタビュー

Ollamaを使用したAI対話型で相続情報を収集します（要Ollama）。

```bash
uv run python -m src.cli.main interview -o result.json
```

### `demo` - デモ実行

デモケースを実行します。

```bash
# 基本ケース
uv run python -m src.cli.main demo --type basic

# 複雑ケース
uv run python -m src.cli.main demo --type complex

# 対話デモ
uv run python -m src.cli.main demo --type interactive
```

---

## 連絡先情報の管理

### 連絡先情報の収集

相続計算実行後、自動的に連絡先情報の入力プロンプトが表示されます。

```
╭────────────────────────╮
│ 相続人の連絡先情報入力 │
╰────────────────────────╯

相続人の連絡先情報を入力しますか？ [y/n] (y): y

【山田花子】の連絡先情報

住所: 東京都渋谷区渋谷1-1-1
電話番号: 03-1234-5678
メールアドレス: hanako@example.com
✓ 連絡先情報を登録しました

【山田一郎】の連絡先情報

住所: [Enter キーでスキップ]
電話番号: 090-1234-5678
メールアドレス: [Enter キーでスキップ]
✓ 連絡先情報を登録しました

✓ 2名の連絡先情報を登録しました
```

### 連絡先情報のバリデーション

- **メールアドレス**: `@`と`.`を含む基本的な形式チェック
- **電話番号**: 数字、ハイフン、`+`、括弧、スペースのみ許可
- **住所**: 任意の文字列（バリデーションなし）

### 連絡先情報の表示

収集後、自動的にサマリーテーブルが表示されます：

```
╭──────────────────╮
│ 登録された連絡先情報 │
╰──────────────────╯

┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 氏名         ┃ 住所                     ┃ 電話番号    ┃ メールアドレス          ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 山田花子     │ 東京都渋谷区渋谷1-1-1    │ 03-1234-5678│ hanako@example.com      │
│ 山田一郎     │ -                        │ 090-1234-5678│ -                       │
└──────────────┴──────────────────────────┴─────────────┴─────────────────────────┘
```

---

## レポート生成

### Markdownレポート

相続計算結果と連絡先情報を含むMarkdownレポートを生成します。

```bash
uv run python -m src.cli.main calc -i case.json -o report.md
```

**出力内容:**

- 相続計算レポート（被相続人、相続人、相続割合）
- 計算根拠（民法条文）
- 相続人連絡先情報（データがある場合のみ）

### PDFレポート

専門的な体裁のPDFレポートを生成します。

```bash
uv run python -m src.cli.main calc -i case.json -o report.pdf
```

**特徴:**

- 日本語フォント対応（IPAフォント使用）
- テーブルスタイリング（グレーヘッダー、ベージュ行）
- 連絡先情報テーブル（データがある場合のみ）

### CSV連絡先エクスポート

連絡先情報をCSV形式でエクスポートします。

```bash
uv run python -m src.cli.main calc -i case.json -o contacts.csv
```

**CSV形式:**

```csv
氏名,続柄,相続順位,相続割合（分数）,相続割合（%）,住所,電話番号,メールアドレス
山田花子,配偶者,常に相続,1/2,50.00,東京都渋谷区渋谷1-1-1,03-1234-5678,hanako@example.com
山田一郎,子,第1順位,1/2,50.00,,-,ichiro@example.com
```

**エンコーディング**: UTF-8-sig（BOM付き、Excel互換）

### レポート生成時の連絡先CSVエクスポート

Markdown/PDFレポート生成時に、連絡先情報のCSVもエクスポートできます。

```bash
uv run python -m src.cli.main calc -i case.json -o report.pdf
```

プロンプトが表示されます：

```
結果を report.pdf に出力しました。
連絡先情報のCSVもエクスポートしますか？ [y/n] (n): y
連絡先情報を report_contacts.csv に出力しました。
```

---

## Neo4jデータベース連携

### Neo4jのセットアップ

```bash
# Neo4jのダウンロードとインストール
# https://neo4j.com/download/

# Neo4jの起動
neo4j start

# 初回ログイン（デフォルト: neo4j/neo4j）
# http://localhost:7474
```

### 環境変数の設定

`.env`ファイルに接続情報を設定：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### データの保存

```bash
uv run python -m src.cli.main calc -i case.json --save-to-neo4j
```

保存される情報：

- 人物ノード（Person）
  - 基本情報: 氏名、生死、生年月日、死亡日
  - 連絡先情報: 住所、電話番号、メールアドレス
- リレーションシップ
  - CHILD_OF: 親子関係
  - SPOUSE_OF: 配偶者関係
  - SIBLING_OF: 兄弟姉妹関係
  - RENOUNCED: 相続放棄
  - DISQUALIFIED: 相続欠格
  - DISINHERITED: 相続廃除

### Neo4jブラウザでの確認

```cypher
// すべての人物を表示
MATCH (p:Person) RETURN p

// 被相続人を中心とした家系図
MATCH (decedent:Person {is_decedent: true})-[r]-(related:Person)
RETURN decedent, r, related

// 連絡先情報がある相続人
MATCH (p:Person)
WHERE p.address IS NOT NULL OR p.phone IS NOT NULL OR p.email IS NOT NULL
RETURN p.name, p.address, p.phone, p.email
```

---

## トラブルシューティング

### 問題: Neo4jに接続できない

**原因**: Neo4jサービスが起動していない、または接続情報が正しくない

**解決方法**:

```bash
# Neo4jの状態確認
neo4j status

# 起動
neo4j start

# .envファイルの接続情報を確認
cat .env
```

### 問題: PDFレポートで日本語が表示されない

**原因**: IPAフォントがインストールされていない

**解決方法**:

IPAフォントは`ReportGenerator`で自動的にダウンロードされますが、手動でインストールすることもできます：

```bash
# macOS
brew install ipa-fonts

# Ubuntu/Debian
sudo apt-get install fonts-ipafont
```

### 問題: CSV連絡先エクスポートで文字化けする

**原因**: Excelが文字エンコーディングを正しく認識していない

**解決方法**:

CSV出力は自動的にUTF-8-sig（BOM付き）で保存されます。それでも文字化けする場合：

1. CSVファイルをテキストエディタで開く
2. エンコーディングをUTF-8で保存し直す
3. Excelの「データ」→「テキストファイルから」でインポート

### 問題: 連絡先情報の入力プロンプトが表示されない

**原因**: 非対話環境（テスト、バッチ処理など）で実行している

**動作**:

`sys.stdin.isatty()`がFalseの場合、連絡先収集は自動的にスキップされます。これは正常な動作です。

対話環境で実行してください：

```bash
# 対話シェルから実行
uv run python -m src.cli.main calc -i case.json
```

### 問題: メールアドレスのバリデーションエラー

**原因**: メールアドレスの形式が正しくない

**解決方法**:

基本的な形式要件：
- `@`が含まれている
- `@`の後に`.`が含まれている

有効な例:
- `user@example.com`
- `user.name@example.co.jp`

無効な例:
- `user@example`（ドメインに`.`がない）
- `user.example.com`（`@`がない）

### 問題: 電話番号のバリデーションエラー

**原因**: 許可されていない文字が含まれている

**解決方法**:

許可されている文字:
- 数字: `0-9`
- ハイフン: `-`
- プラス: `+`
- 括弧: `(`, `)`
- スペース

有効な例:
- `03-1234-5678`
- `090-1234-5678`
- `+81-3-1234-5678`
- `03 (1234) 5678`

無効な例:
- `03-1234-5678 (自宅)`（許可されていない文字）

---

## 付録

### 入力JSONフォーマット

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

### CSVテンプレート

```csv
区分,氏名,生存状態,生年月日,死亡日,血縁タイプ,相続放棄
被相続人,山田太郎,故人,1950-01-01,2025-06-15,,
配偶者,山田花子,存命,1955-03-10,,,
子,山田一郎,存命,1980-05-20,,,
```

---

## サポート

問題が解決しない場合は、以下のリソースを参照してください：

- [GitHubリポジトリ](https://github.com/your-org/inheritance-calculator)
- [Issue Tracker](https://github.com/your-org/inheritance-calculator/issues)
- [CLAUDE.md](../CLAUDE.md) - プロジェクト仕様書

---

**最終更新日**: 2025年10月17日
**バージョン**: 1.1.0
