# Project Context

## Purpose
日本の民法に基づいた相続人の資格確定と相続割合（相続分）の計算を自動化するアプリケーション。代襲相続、再転相続、相続放棄などの複雑なケースにも対応し、実務での判断を支援する。

### 対象ユーザー
- 司法書士
- 弁護士
- 税理士
- 行政書士
- 相続手続きに関わる実務家

## Tech Stack

### Core
- **Python**: 3.12+
- **パッケージ管理**: uv
- **データベース**: Neo4j (Community Edition, グラフデータベース)
- **AI/ML**: Ollama (gpt-oss:20b) + Agnos (エージェントフレームワーク)

### Backend (FastAPI)
- **FastAPI**: RESTful API
- **Uvicorn**: ASGI server
- **Pydantic**: データバリデーション、スキーマ定義

### Frontend (計画中)
- **Next.js**: React framework
- **React**: UIライブラリ
- **TypeScript**: 型安全性

### 主要ライブラリ
- `neo4j` (6.0.2): Neo4jドライバー
- `agnos` (1.0.2): エージェントワークフロー
- `ollama` (0.6.0): Ollama Python SDK
- `pydantic` (2.11.9): データバリデーション
- `python-dotenv` (1.1.1): 環境変数管理
- `rich` (14.1.0): CLIの美しい出力
- `reportlab` (4.4.4+): PDF生成
- `graphviz` (0.21+): 家系図生成
- `markdown` (3.9+): Markdownレポート生成

### 開発ツール
- `pytest` (8.0.0): テストフレームワーク
- `pytest-cov` (4.0.0): カバレッジ測定
- `mypy` (1.8.0): 型チェック
- `ruff` (0.1.0): リンター
- `black` (24.0.0+): フォーマッター

## Project Conventions

### Code Style
- **PEP 8準拠**: Python標準コーディング規約に従う
- **Type Hints必須**: すべての関数・メソッドに型アノテーションを付ける
- **Docstrings**: Google形式で記述（日本語コメント可）
- **命名規則**:
  - 変数名・関数名: 英語（例: `calculate_inheritance_share`）
  - コメント: 日本語可（例: `# 相続人の資格を判定`）
  - クラス名: PascalCase（例: `InheritanceCalculator`）
  - 定数: UPPER_SNAKE_CASE（例: `MAX_RETRY_COUNT`）
- **行長**: 88文字（Black標準）
- **インポート順**: 標準ライブラリ → サードパーティ → ローカル（ruffで自動整理）

### Architecture Patterns

#### レイヤードアーキテクチャ
- **Models層** (`src/models/`): Pydanticデータモデル、バリデーション
- **Services層** (`src/services/`): ビジネスロジック、計算ロジック
- **Database層** (`src/database/`): Neo4jアクセス、Cypherクエリ
- **Agents層** (`src/agents/`): AI対話エージェント、LLM統合
- **CLI層** (`src/cli/`): コマンドラインインターフェース
- **Backend層** (`backend/`): FastAPI REST API

#### 主要デザインパターン
- **Service Layer Pattern**: ビジネスロジックをプレゼンテーション層から分離
- **Repository Pattern**: データベースアクセスの抽象化
- **Strategy Pattern**: 相続順位ごとに異なる計算戦略を適用
- **Factory Pattern**: 入力形式（JSON/CSV）に応じたパーサーの生成

#### 依存関係の方向
```
CLI/Backend → Services → Database
              ↓           ↓
            Models    Neo4j Client
```

### Testing Strategy

#### テスト要件
- **カバレッジ目標**: 75%以上（現在75%達成）
- **テストピラミッド**: Unit > Integration > E2E
- **テストファイル配置**: `tests/` ディレクトリに対応する構造

#### テストカテゴリ
1. **Unit Tests** (`tests/test_models/`, `tests/test_services/`):
   - 各モデル、サービスクラスの単体テスト
   - モックを使用した外部依存の隔離

2. **Integration Tests** (`tests/test_integration/`):
   - サービス層とデータベース層の統合テスト
   - 実際のNeo4j接続（テスト環境）を使用

3. **CLI Tests** (`tests/test_cli/`):
   - コマンド実行のテスト
   - 入出力フォーマットのテスト

#### 実行コマンド
```bash
# 全テスト実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=src --cov-report=html

# 特定モジュール
uv run pytest tests/test_services/

# 型チェック
uv run mypy src/

# リンター
uv run ruff check src/
```

#### テストケースの基準
- **民法に基づく実例**: 実際の民法条文に基づくケースをテスト
- **エッジケース**: 代襲相続、半血兄弟姉妹、相続放棄の組み合わせ
- **エラーケース**: 無効な入力、不整合なデータの処理

### Git Workflow

#### ブランチ戦略
- **main**: 本番環境相当、常に安定版
- **develop**: 開発ブランチ（現在は未使用、mainで直接開発）
- **feature/***: 機能追加ブランチ（例: `feature/web-ui`）
- **fix/***: バグ修正ブランチ

#### コミットメッセージ規約
**Conventional Commits形式**:
```
<type>: <subject>

[optional body]
[optional footer]
```

**Types**:
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `test`: テスト追加・修正
- `refactor`: リファクタリング
- `chore`: ビルド、依存関係など

**例**:
```
feat: Neo4j統合機能を追加

- Neo4jクライアントの実装
- Cypherクエリのリポジトリパターン
- CLIの--save-to-neo4jオプション追加

Closes #12
```

## Domain Context

### 日本の民法（相続法）
このプロジェクトは**民法第5編「相続」（第882条～第1050条）**に準拠しています。

#### 相続順位
1. **配偶者**: 常に相続人（民法890条）
2. **第1順位**: 子（直系卑属）（民法887条1項）
3. **第2順位**: 直系尊属（父母、祖父母）（民法889条1項1号）
4. **第3順位**: 兄弟姉妹（民法889条1項2号）

#### 法定相続分（民法900条）
- 配偶者 + 子: 配偶者1/2、子1/2
- 配偶者 + 直系尊属: 配偶者2/3、直系尊属1/3
- 配偶者 + 兄弟姉妹: 配偶者3/4、兄弟姉妹1/4
- 半血兄弟姉妹: 全血の1/2

#### 特殊ケース
- **代襲相続**（民法887条2項、3項）:
  - 子の場合: 無制限に代襲
  - 兄弟姉妹の場合: 1代限り（甥・姪まで）

- **再転相続**（民法896条）:
  - 相続人が遺産分割前に死亡した場合、その相続人の相続人が権利を承継

- **相続放棄**（民法938条～940条）:
  - 初めから相続人でなかったものとみなす
  - 代襲相続は発生しない

### 用語集
- **被相続人**: 故人（decedent）
- **相続人**: 遺産を受け継ぐ資格のある人（heir）
- **法定相続分**: 民法で定められた相続割合（statutory share）
- **代襲相続**: 相続人の地位を子・孫が引き継ぐこと（substitution）
- **直系卑属**: 子、孫、ひ孫など（lineal descendants）
- **直系尊属**: 父母、祖父母など（lineal ascendants）
- **全血**: 父母を同じくする兄弟姉妹（full-blood siblings）
- **半血**: 父母の一方のみを同じくする兄弟姉妹（half-blood siblings）

## Important Constraints

### 法的制約
- **民法準拠必須**: すべての計算ロジックは民法に厳密に従う
- **法改正対応**: 民法改正時には計算ロジックの更新が必要
- **免責事項**: 本システムは法的助言を提供するものではない

### データ整合性制約
- **日付検証**: `death_date > birth_date`、`death_date < 現在日時`
- **被相続人**: 必ず1名、死亡済みであること
- **配偶者**: `is_current=True`の配偶者のみ相続資格あり
- **分数演算**: 浮動小数点ではなく分数（Fraction）を使用して正確な割合計算

### 技術的制約
- **Python 3.12+必須**: 新しい型システム機能を使用
- **Neo4j必須**: グラフデータベースでの永続化機能使用時
- **Ollama必須**: AI対話型インタビュー機能使用時（gpt-oss:20bモデル）
- **メモリ制約**: 大規模家系図（100人以上）の場合、パフォーマンス考慮が必要

### セキュリティ制約
- **個人情報保護**: 相続人の個人情報を含むため、適切なアクセス制御
- **ローカル実行推奨**: データプライバシーの観点からローカル環境での実行を推奨
- **データベースセキュリティ**: Neo4jの認証・アクセス制御を適切に設定

## External Dependencies

### Neo4j (グラフデータベース)
- **用途**: 相続関係のグラフ構造での永続化
- **接続**: bolt://localhost:7687
- **認証**: USERNAME/PASSWORD認証
- **必須設定**: `.env`ファイルで`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`を設定

### Ollama (ローカルLLM実行環境)
- **用途**: AI対話型インタビュー機能
- **モデル**: gpt-oss:20b（20Bパラメータの日本語対応モデル）
- **接続**: http://localhost:11434
- **必須設定**:
  - Ollamaサーバーが起動していること
  - `ollama pull gpt-oss:20b`でモデルをダウンロード済み

### Graphviz (グラフ描画ツール)
- **用途**: 家系図のPNG/PDF/SVG生成（オプション）
- **インストール**: システムレベルでのインストールが必要
  ```bash
  # macOS
  brew install graphviz

  # Ubuntu/Debian
  sudo apt-get install graphviz
  ```
- **依存**: `src/cli/family_tree_generator.py`の一部機能

### 環境変数 (.env)
```bash
# Neo4j接続設定
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j

# Ollama設定
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_TIMEOUT=120
OLLAMA_TEMPERATURE=0.7

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=logs/inheritance.log

# アプリケーション設定
APP_ENV=development
```
