# Inheritance Calculator - Backend API

相続人・相続割合確定アプリケーションのWebバックエンドAPI

## 技術スタック

- **FastAPI**: 高性能Webフレームワーク
- **Python 3.12**: 最新のPython
- **Neo4j**: グラフデータベース
- **Ollama**: ローカルLLM
- **Pydantic**: データバリデーション

## セットアップ

```bash
# 依存関係のインストール
uv sync

# 開発用依存関係を含める場合
uv sync --all-extras

# 環境変数設定
cp .env.example .env
# .envファイルを編集して設定を調整
```

## 実行

```bash
# 開発サーバー起動
uv run uvicorn app.main:app --reload --port 8000

# または
uv run fastapi dev app/main.py
```

## API ドキュメント

サーバー起動後、以下のURLでAPIドキュメントにアクセス:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要エンドポイント

### ユーティリティAPI

- `POST /api/v1/utils/convert-era-to-western`: 元号→西暦変換
- `POST /api/v1/utils/convert-western-to-era`: 西暦→元号変換
- `POST /api/v1/utils/detect-and-convert`: 自動判定変換

### ヘルスチェック

- `GET /health`: ヘルスチェック

## テスト

```bash
# テスト実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=app

# 型チェック
uv run mypy app
```

## 開発

```bash
# コード整形
uv run ruff format .

# リンター
uv run ruff check .
```
