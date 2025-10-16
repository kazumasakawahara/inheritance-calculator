# マルチパッケージ移行計画

## 概要

現在の `inheritance-calculator` を3つのパッケージに分割します：

1. **inheritance-calculator-core**: 共有ライブラリ（PyPI公開）
2. **inheritance-calculator-cli**: CLIアプリケーション（PyPI公開）
3. **inheritance-calculator-web**: Webアプリケーション（新規作成、別リポジトリ）

## 移行フェーズ

### Phase 1: 準備（現在）

- [x] 現状分析
- [x] Core抽出計画の策定
- [ ] 移行計画ドキュメントの作成
- [ ] バックアップブランチの作成

### Phase 2: Core パッケージの作成

**ディレクトリ構成**:

```
inheritance-calculator-core/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── inheritance_calculator_core/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── person.py
│       │   ├── inheritance.py
│       │   ├── relationship.py
│       │   └── base.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── inheritance_calculator.py
│       │   ├── heir_validator.py
│       │   ├── share_calculator.py
│       │   ├── neo4j_service.py
│       │   └── base.py
│       ├── database/
│       │   ├── __init__.py
│       │   ├── neo4j_client.py
│       │   ├── queries.py
│       │   ├── repositories.py
│       │   └── base.py
│       ├── agents/ (optional)
│       │   ├── __init__.py
│       │   ├── ollama_client.py
│       │   ├── interview_agent.py
│       │   └── prompts.py
│       └── utils/
│           ├── __init__.py
│           ├── config.py
│           ├── logger.py
│           ├── era_converter.py
│           └── exceptions.py
└── tests/
    ├── test_models/
    ├── test_services/
    ├── test_database/
    └── test_utils/
```

**依存関係**:
- `neo4j~=6.0.2`
- `pydantic[email]~=2.11.9`
- `pydantic-settings~=2.11.0`
- `python-dotenv~=1.1.1`
- `agnos~=1.0.2` (optional)
- `ollama~=0.6.0` (optional)

**バージョン**: `1.0.0`

### Phase 3: CLI パッケージの改修

**ディレクトリ構成**:

```
inheritance-calculator-cli/  (現在のリポジトリを改修)
├── pyproject.toml (改修)
├── README.md (改修)
├── LICENSE
├── .gitignore
├── src/
│   └── inheritance_calculator_cli/
│       ├── __init__.py
│       └── cli/
│           ├── __init__.py
│           ├── main.py
│           ├── commands.py
│           ├── display.py
│           ├── contact_input.py
│           ├── report_generator.py
│           ├── csv_parser.py
│           ├── family_tree_generator.py
│           ├── ascii_tree.py
│           ├── session.py
│           └── prompts.py
├── examples/
│   ├── demo_basic_cases.py
│   ├── demo_complex_cases.py
│   ├── demo_interactive.py
│   ├── demo_contact_collection.py
│   ├── README.md
│   └── data/
└── tests/
    └── test_cli/
```

**依存関係**:
- `inheritance-calculator-core>=1.0.0,<2.0.0`
- `rich~=14.1.0`
- `reportlab>=4.4.4`
- `markdown>=3.9`
- `graphviz>=0.21`

**バージョン**: `1.0.0`

### Phase 4: Web パッケージの作成（将来）

**別リポジトリとして新規作成**:

```
inheritance-calculator-web/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py (FastAPI)
│   │   ├── api/
│   │   ├── models/
│   │   └── services/
│   └── requirements.txt
│       # inheritance-calculator-core>=1.0.0
│       # fastapi
│       # uvicorn
└── frontend/
    ├── package.json
    ├── next.config.js
    └── src/
        ├── app/
        ├── components/
        └── lib/
```

**依存関係**:
- Backend: `inheritance-calculator-core>=1.0.0`, `fastapi`, `uvicorn`
- Frontend: Next.js 14, TypeScript, shadcn/ui

**バージョン**: `0.1.0` (MVP)

## モジュール移行マッピング

### Core に移行

| 現在のパス | Core パス |
|-----------|-----------|
| `src/models/*` | `inheritance_calculator_core/models/*` |
| `src/services/*` | `inheritance_calculator_core/services/*` |
| `src/database/*` | `inheritance_calculator_core/database/*` |
| `src/agents/*` | `inheritance_calculator_core/agents/*` (optional) |
| `src/utils/*` | `inheritance_calculator_core/utils/*` |

### CLI に残す

| 現在のパス | CLI パス |
|-----------|----------|
| `src/cli/*` | `inheritance_calculator_cli/cli/*` |
| `examples/*` | `examples/*` |
| `tests/test_cli/*` | `tests/test_cli/*` |

### 削除（Core/CLIに統合）

| 現在のパス | 理由 |
|-----------|------|
| `tests/test_models/` | Core に移行 |
| `tests/test_services/` | Core に移行 |
| `tests/test_database/` | Core に移行 |
| `tests/test_integration/` | Core/CLI で分割 |

## インポートパス変更

### Before (現在)

```python
from src.models.person import Person
from src.services.inheritance_calculator import InheritanceCalculator
from src.database.neo4j_client import Neo4jClient
```

### After (移行後)

**Core パッケージ内**:
```python
from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.services.inheritance_calculator import InheritanceCalculator
from inheritance_calculator_core.database.neo4j_client import Neo4jClient
```

**CLI パッケージ内**:
```python
# Core からインポート
from inheritance_calculator_core.models.person import Person
from inheritance_calculator_core.services.inheritance_calculator import InheritanceCalculator

# CLI 内部からインポート
from inheritance_calculator_cli.cli.display import display_result
```

## テスト戦略

### Core パッケージ

- `tests/test_models/` - モデルのバリデーションテスト
- `tests/test_services/` - 相続計算ロジックのテスト
- `tests/test_database/` - Neo4j統合テスト
- `tests/test_utils/` - ユーティリティのテスト

**カバレッジ目標**: 80%以上

### CLI パッケージ

- `tests/test_cli/` - CLIコマンドのテスト
- `tests/test_report_generator/` - レポート生成のテスト

**カバレッジ目標**: 70%以上

## リリース手順

### Core パッケージ

1. GitHub リポジトリ作成: `inheritance-calculator-core`
2. コード移行とテスト
3. PyPI 公開準備（TestPyPI で検証）
4. PyPI 公開: `uv publish`

### CLI パッケージ

1. 現在のリポジトリを改修
2. Core 依存関係を追加
3. インポートパス変更
4. テスト実行
5. PyPI 公開: `uv publish`

### Web パッケージ（将来）

1. GitHub リポジトリ作成: `inheritance-calculator-web`
2. MVP 開発
3. Docker イメージ公開（Docker Hub）
4. ドキュメント作成

## 互換性マトリクス

| Core バージョン | CLI バージョン | Web バージョン |
|-----------------|----------------|----------------|
| 1.0.x           | 1.0.x          | -              |
| 1.1.x           | 1.0.x, 1.1.x   | -              |
| 2.0.x           | 2.0.x          | 1.0.x          |

**セマンティックバージョニング**:
- **MAJOR**: 破壊的変更（API変更、民法改正対応）
- **MINOR**: 後方互換な機能追加
- **PATCH**: バグ修正

## ドキュメント更新

### Core パッケージ

- `README.md` - Core の使い方
- `API.md` - API リファレンス
- `CHANGELOG.md` - 変更履歴

### CLI パッケージ

- `README.md` - CLI の使い方（改修）
- `docs/user_guide.md` - ユーザーガイド（改修）
- `docs/architecture.md` - アーキテクチャ（改修）

### Web パッケージ（将来）

- `README.md` - Web UI の使い方
- `docs/deployment.md` - デプロイガイド
- `docs/api.md` - API ドキュメント

## リスク管理

| リスク | 影響 | 対策 |
|--------|------|------|
| インポートパス変更の漏れ | 高 | 自動テストでカバー、段階的移行 |
| 既存ユーザーへの影響 | 中 | 移行ガイド作成、バージョン固定推奨 |
| Core API の不安定性 | 中 | 1.0.0 前に十分なテスト |
| PyPI 公開の失敗 | 低 | TestPyPI で事前検証 |

## タイムライン

- **Week 1**: Phase 2 (Core パッケージ作成)
- **Week 2**: Phase 3 (CLI パッケージ改修)
- **Week 3**: テストと検証
- **Week 4**: ドキュメント作成と公開

---

**最終更新日**: 2025年10月17日
**ステータス**: Phase 1 完了
