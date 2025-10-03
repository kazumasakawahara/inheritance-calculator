# Webダッシュボード UI 仕様書

## 📋 プロジェクト概要

### プロジェクト名
**Inheritance Calculator Web Dashboard**

### 目的
CLIベースの相続計算システムにモダンなWebダッシュボードUIを追加し、ターミナル操作に不慣れなユーザーでも直感的に利用できるようにする。

### 対象ユーザー
- 司法書士、弁護士、税理士、行政書士
- 相続実務の専門家（ITスキルは様々）
- ターミナル操作に抵抗がある利用者

---

## 🎯 機能要件

### 1. 元号・西暦変換機能（重要）

#### 1.1 元号入力対応
**要件:**
- 日本の元号（明治、大正、昭和、平成、令和）での日付入力をサポート
- 西暦入力も並行してサポート
- 自動的に西暦に変換して内部処理

**対応元号:**
```
明治: 1868年1月25日 ～ 1912年7月30日
大正: 1912年7月30日 ～ 1926年12月25日
昭和: 1926年12月25日 ～ 1989年1月7日
平成: 1989年1月8日  ～ 2019年4月30日
令和: 2019年5月1日  ～ 現在
```

**入力形式:**
- `令和5年10月3日`
- `R5.10.3`
- `R5/10/3`
- `昭和60年3月15日`
- `S60.3.15`
- `2025年10月3日`
- `2025/10/3`
- `2025-10-03`

**バリデーション:**
- 元号の有効期間をチェック
- 存在しない日付のチェック（例: 令和元年3月 → エラー）
- 曖昧な入力の場合は確認ダイアログ

#### 1.2 元号変換ロジック
```python
# 元号マッピング
ERA_MAP = {
    "明治": ("M", 1868, 1, 25, 1912, 7, 30),
    "大正": ("T", 1912, 7, 30, 1926, 12, 25),
    "昭和": ("S", 1926, 12, 25, 1989, 1, 7),
    "平成": ("H", 1989, 1, 8, 2019, 4, 30),
    "令和": ("R", 2019, 5, 1, None, None, None)
}

def parse_japanese_date(input_str: str) -> date:
    """
    元号形式の日付を西暦dateオブジェクトに変換

    Args:
        input_str: 元号または西暦の日付文字列

    Returns:
        西暦のdateオブジェクト

    Raises:
        ValueError: 無効な日付形式の場合
    """
    pass
```

### 2. バックエンドAPI（FastAPI）

#### 2.1 プロジェクト構造
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPIアプリケーション
│   ├── config.py               # 設定管理
│   │
│   ├── api/                    # APIエンドポイント
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── cases.py        # ケース管理API
│   │   │   ├── calculation.py  # 計算API
│   │   │   ├── chat.py         # AI対話API
│   │   │   ├── import_export.py # インポート/エクスポート
│   │   │   └── utils.py        # 日付変換などのユーティリティ
│   │
│   ├── models/                 # Pydanticモデル
│   │   ├── __init__.py
│   │   ├── case.py             # ケースモデル
│   │   ├── person.py           # 人物モデル
│   │   ├── calculation.py      # 計算結果モデル
│   │   └── chat.py             # チャットモデル
│   │
│   ├── services/               # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── case_service.py     # ケース管理
│   │   ├── calculation_service.py  # 計算サービス
│   │   ├── chat_service.py     # AI対話サービス
│   │   └── date_converter.py   # 元号変換サービス
│   │
│   ├── schemas/                # レスポンススキーマ
│   │   ├── __init__.py
│   │   └── responses.py
│   │
│   └── core/                   # コア機能
│       ├── __init__.py
│       ├── security.py         # 認証・セキュリティ
│       └── dependencies.py     # 依存性注入
│
├── tests/                      # テスト
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_date_converter.py
│
├── pyproject.toml
└── README.md
```

#### 2.2 APIエンドポイント仕様

##### ケース管理
```python
# POST /api/v1/cases
# 新規ケース作成
Request:
{
    "decedent_name": "山田太郎",
    "death_date": "令和7年6月15日",  # 元号形式
    "description": "相続ケース1"
}

Response:
{
    "id": "uuid",
    "decedent_name": "山田太郎",
    "death_date": "2025-06-15",  # 西暦に変換
    "created_at": "2025-10-03T10:00:00Z"
}

# GET /api/v1/cases
# ケース一覧取得
Query Parameters:
- page: int (default: 1)
- per_page: int (default: 20)
- sort_by: str (created_at, updated_at, decedent_name)
- order: str (asc, desc)
- search: str (被相続人名で検索)

Response:
{
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
}

# GET /api/v1/cases/{case_id}
# ケース詳細取得

# PUT /api/v1/cases/{case_id}
# ケース更新

# DELETE /api/v1/cases/{case_id}
# ケース削除
```

##### 計算API
```python
# POST /api/v1/cases/{case_id}/calculate
# 相続計算実行
Request:
{
    "spouses": [...],
    "children": [...],
    "parents": [...],
    "siblings": [...],
    "renounced": [...],
    "sibling_blood_types": {...}
}

Response:
{
    "result": {
        "heirs": [
            {
                "name": "山田花子",
                "relationship": "配偶者",
                "share": "1/2",
                "percentage": 50.0,
                "rank": "配偶者"
            },
            ...
        ],
        "legal_basis": "民法第900条1号",
        "calculated_at": "2025-10-03T10:00:00Z"
    }
}
```

##### AI対話API（WebSocket）
```python
# WebSocket /api/v1/chat/{case_id}
# AI対話エンドポイント

Client -> Server:
{
    "type": "message",
    "content": "山田太郎、令和7年6月15日に死亡しました"
}

Server -> Client:
{
    "type": "response",
    "content": "理解しました。被相続人: 山田太郎様（2025年6月15日死亡）\n\n配偶者はいらっしゃいますか？",
    "extracted_data": {
        "decedent_name": "山田太郎",
        "death_date": "2025-06-15"
    },
    "progress": 20
}
```

##### ユーティリティAPI
```python
# POST /api/v1/utils/convert-date
# 元号→西暦変換
Request:
{
    "date_string": "令和5年10月3日"
}

Response:
{
    "original": "令和5年10月3日",
    "converted": "2025-10-03",
    "era": "令和",
    "year": 5,
    "month": 10,
    "day": 3
}
```

### 3. フロントエンド（Next.js + TypeScript）

#### 3.1 プロジェクト構造
```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # ルートレイアウト
│   │   ├── page.tsx            # ダッシュボード
│   │   ├── cases/
│   │   │   ├── page.tsx        # ケース一覧
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx    # ケース詳細
│   │   │   │   └── edit/page.tsx  # ケース編集
│   │   │   └── new/page.tsx    # 新規ケース作成
│   │   ├── settings/
│   │   │   └── page.tsx        # 設定
│   │   └── stats/
│   │       └── page.tsx        # 統計
│   │
│   ├── components/             # コンポーネント
│   │   ├── ui/                 # shadcn/ui コンポーネント
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── cases/
│   │   │   ├── CaseList.tsx
│   │   │   ├── CaseCard.tsx
│   │   │   └── CaseForm.tsx
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── calculation/
│   │   │   ├── ResultTable.tsx
│   │   │   ├── SharePieChart.tsx
│   │   │   └── FamilyTree.tsx
│   │   └── forms/
│   │       ├── DateInput.tsx        # 元号/西暦入力
│   │       ├── PersonForm.tsx
│   │       └── RelationshipForm.tsx
│   │
│   ├── lib/                    # ユーティリティ
│   │   ├── api/                # API クライアント
│   │   │   ├── cases.ts
│   │   │   ├── calculation.ts
│   │   │   └── chat.ts
│   │   ├── utils/
│   │   │   ├── dateConverter.ts     # クライアント側の元号変換
│   │   │   └── validation.ts
│   │   └── hooks/              # カスタムフック
│   │       ├── useCases.ts
│   │       ├── useChat.ts
│   │       └── useDateInput.ts
│   │
│   ├── types/                  # TypeScript型定義
│   │   ├── case.ts
│   │   ├── person.ts
│   │   └── calculation.ts
│   │
│   └── styles/                 # スタイル
│       └── globals.css
│
├── public/                     # 静的ファイル
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

#### 3.2 主要コンポーネント仕様

##### DateInput コンポーネント
```typescript
// src/components/forms/DateInput.tsx

interface DateInputProps {
  value: string;
  onChange: (value: string) => void;
  label: string;
  placeholder?: string;
  format?: 'era' | 'western' | 'auto';  // 元号/西暦/自動判定
  error?: string;
}

/**
 * 元号・西暦対応の日付入力コンポーネント
 *
 * 機能:
 * - 元号入力（令和5年10月3日、R5.10.3）
 * - 西暦入力（2025/10/3、2025-10-03）
 * - 自動判定と変換
 * - カレンダーピッカー
 * - リアルタイムバリデーション
 * - 変換結果のプレビュー表示
 */
export const DateInput: React.FC<DateInputProps> = ({...}) => {
  // 実装
}
```

##### ChatInterface コンポーネント
```typescript
// src/components/chat/ChatInterface.tsx

/**
 * AI対話インターフェース
 *
 * 機能:
 * - WebSocket接続
 * - メッセージ送受信
 * - 抽出データのリアルタイム表示
 * - 進捗表示
 * - 音声入力（オプション）
 */
```

##### FamilyTree コンポーネント
```typescript
// src/components/calculation/FamilyTree.tsx

/**
 * 家系図可視化コンポーネント
 *
 * 使用ライブラリ: React Flow または D3.js
 *
 * 機能:
 * - 対話的な家系図表示
 * - ドラッグ＆ドロップで編集
 * - ズーム・パン
 * - 人物ノードのクリックで詳細表示
 * - 相続割合の視覚化
 */
```

### 4. データベース拡張

#### 4.1 ケース管理テーブル（新規）
```cypher
# Caseノード
CREATE (c:Case {
    id: $id,                    # UUID
    decedent_name: $name,       # 被相続人名
    death_date: date($date),    # 西暦形式
    created_at: datetime(),
    updated_at: datetime(),
    status: $status,            # draft, calculated, completed
    description: $description
})

# ケースと人物の関係
CREATE (c)-[:HAS_PERSON]->(p:Person)

# 計算結果の保存
CREATE (c)-[:HAS_RESULT]->(r:CalculationResult {
    calculated_at: datetime(),
    result_json: $json_data
})
```

---

## 🏗️ 実装フェーズ計画

### Phase 5: 基盤構築（Week 1-2）

#### Task 5.1: プロジェクトセットアップ
- [ ] 5.1.1: FastAPI プロジェクト初期化
- [ ] 5.1.2: Next.js プロジェクト初期化
- [ ] 5.1.3: 依存関係の追加
- [ ] 5.1.4: ディレクトリ構造の作成
- [ ] 5.1.5: 開発環境設定（ESLint, Prettier, pre-commit）

#### Task 5.2: 元号変換ロジック実装
- [ ] 5.2.1: 元号マスターデータ定義
- [ ] 5.2.2: 元号→西暦変換関数実装
- [ ] 5.2.3: 西暦→元号変換関数実装
- [ ] 5.2.4: 日付文字列パース関数実装
- [ ] 5.2.5: バリデーション関数実装
- [ ] 5.2.6: ユニットテスト（100%カバレッジ目標）

#### Task 5.3: FastAPI基本セットアップ
- [ ] 5.3.1: FastAPIアプリケーション初期化
- [ ] 5.3.2: CORS設定
- [ ] 5.3.3: ミドルウェア設定
- [ ] 5.3.4: ロギング設定
- [ ] 5.3.5: 既存Pythonコードとの統合準備

### Phase 6: バックエンドAPI開発（Week 3-4）

#### Task 6.1: ケース管理API
- [ ] 6.1.1: Pydanticモデル定義（Case, Person）
- [ ] 6.1.2: Neo4j拡張（Caseノード対応）
- [ ] 6.1.3: ケースCRUD API実装
- [ ] 6.1.4: ページネーション実装
- [ ] 6.1.5: 検索・フィルター実装
- [ ] 6.1.6: APIテスト

#### Task 6.2: 計算API
- [ ] 6.2.1: 既存計算ロジックのAPI化
- [ ] 6.2.2: 計算結果スキーマ定義
- [ ] 6.2.3: POST /calculate エンドポイント実装
- [ ] 6.2.4: 計算結果の保存機能
- [ ] 6.2.5: APIテスト

#### Task 6.3: AI対話API（WebSocket）
- [ ] 6.3.1: WebSocket接続セットアップ
- [ ] 6.3.2: 既存interview_agentの統合
- [ ] 6.3.3: メッセージ送受信ロジック
- [ ] 6.3.4: 状態管理（セッション）
- [ ] 6.3.5: エラーハンドリング
- [ ] 6.3.6: WebSocketテスト

#### Task 6.4: ユーティリティAPI
- [ ] 6.4.1: 日付変換API実装
- [ ] 6.4.2: インポート/エクスポートAPI実装
- [ ] 6.4.3: APIドキュメント生成（Swagger UI）

### Phase 7: フロントエンド基礎（Week 5-6）

#### Task 7.1: Next.jsセットアップ
- [ ] 7.1.1: Next.js 14 + TypeScript プロジェクト作成
- [ ] 7.1.2: Tailwind CSS セットアップ
- [ ] 7.1.3: shadcn/ui インストール・設定
- [ ] 7.1.4: ルーティング設計
- [ ] 7.1.5: レイアウトコンポーネント作成

#### Task 7.2: UI基礎コンポーネント
- [ ] 7.2.1: shadcn/uiコンポーネント追加
- [ ] 7.2.2: Header, Sidebar, Footer実装
- [ ] 7.2.3: ダークモード対応
- [ ] 7.2.4: レスポンシブデザイン実装

#### Task 7.3: APIクライアント
- [ ] 7.3.1: Axios または fetch ラッパー作成
- [ ] 7.3.2: React Query セットアップ
- [ ] 7.3.3: API型定義（TypeScript）
- [ ] 7.3.4: エラーハンドリング

#### Task 7.4: 元号入力コンポーネント
- [ ] 7.4.1: DateInputコンポーネント実装
- [ ] 7.4.2: クライアント側の元号変換ロジック
- [ ] 7.4.3: カレンダーピッカー統合
- [ ] 7.4.4: バリデーション表示
- [ ] 7.4.5: Storybookでコンポーネント確認

### Phase 8: 主要機能実装（Week 7-8）

#### Task 8.1: ダッシュボード
- [ ] 8.1.1: ダッシュボードページ実装
- [ ] 8.1.2: 統計カード実装
- [ ] 8.1.3: 最近のケース表示
- [ ] 8.1.4: グラフ表示（Chart.js or Recharts）

#### Task 8.2: ケース一覧・詳細
- [ ] 8.2.1: ケース一覧ページ実装
- [ ] 8.2.2: ケースカード実装
- [ ] 8.2.3: 検索・フィルター UI
- [ ] 8.2.4: ページネーション UI
- [ ] 8.2.5: ケース詳細ページ実装

#### Task 8.3: AI対話インターフェース
- [ ] 8.3.1: ChatInterfaceコンポーネント実装
- [ ] 8.3.2: WebSocket接続管理
- [ ] 8.3.3: メッセージ表示UI
- [ ] 8.3.4: 入力フォーム（元号対応）
- [ ] 8.3.5: 進捗表示
- [ ] 8.3.6: 抽出データのプレビュー

#### Task 8.4: 計算結果表示
- [ ] 8.4.1: 結果テーブルコンポーネント
- [ ] 8.4.2: 円グラフコンポーネント
- [ ] 8.4.3: 法的根拠表示
- [ ] 8.4.4: PDF出力機能

### Phase 9: 家系図エディター（Week 9-10）

#### Task 9.1: 家系図可視化
- [ ] 9.1.1: React Flow または D3.js 選定
- [ ] 9.1.2: 基本的な家系図レイアウト
- [ ] 9.1.3: ノード（人物）コンポーネント
- [ ] 9.1.4: エッジ（関係）コンポーネント
- [ ] 9.1.5: ズーム・パン機能

#### Task 9.2: 対話的編集
- [ ] 9.2.1: ドラッグ＆ドロップ
- [ ] 9.2.2: 人物追加UI
- [ ] 9.2.3: 関係追加UI
- [ ] 9.2.4: 編集モーダル
- [ ] 9.2.5: 自動レイアウト調整

### Phase 10: テストと最適化（Week 11-12）

#### Task 10.1: テスト実装
- [ ] 10.1.1: バックエンドユニットテスト
- [ ] 10.1.2: バックエンド統合テスト
- [ ] 10.1.3: フロントエンドユニットテスト（Jest）
- [ ] 10.1.4: E2Eテスト（Playwright）
- [ ] 10.1.5: テストカバレッジ80%以上達成

#### Task 10.2: パフォーマンス最適化
- [ ] 10.2.1: バックエンドAPI最適化
- [ ] 10.2.2: フロントエンドバンドルサイズ最適化
- [ ] 10.2.3: 画像最適化
- [ ] 10.2.4: キャッシング戦略
- [ ] 10.2.5: Lighthouseスコア90以上達成

#### Task 10.3: セキュリティ強化
- [ ] 10.3.1: 認証・認可実装（JWT）
- [ ] 10.3.2: CSRF対策
- [ ] 10.3.3: XSS対策
- [ ] 10.3.4: セキュリティヘッダー設定
- [ ] 10.3.5: セキュリティ監査

### Phase 11: デプロイ準備（Week 13-14）

#### Task 11.1: Docker化
- [ ] 11.1.1: FastAPI Dockerfile作成
- [ ] 11.1.2: Next.js Dockerfile作成
- [ ] 11.1.3: docker-compose.yml作成
- [ ] 11.1.4: 環境変数管理
- [ ] 11.1.5: ローカル環境でのDocker動作確認

#### Task 11.2: CI/CD
- [ ] 11.2.1: GitHub Actions ワークフロー作成
- [ ] 11.2.2: 自動テスト実行
- [ ] 11.2.3: 自動デプロイ設定
- [ ] 11.2.4: 環境別デプロイ（dev, staging, prod）

#### Task 11.3: ドキュメント
- [ ] 11.3.1: API仕様書（OpenAPI）
- [ ] 11.3.2: セットアップガイド
- [ ] 11.3.3: ユーザーマニュアル
- [ ] 11.3.4: 開発者ガイド

---

## 🧪 テストケース（元号変換）

### ユニットテスト
```python
# tests/test_date_converter.py

def test_parse_reiwa_format():
    """令和形式のパース"""
    assert parse_japanese_date("令和5年10月3日") == date(2023, 10, 3)
    assert parse_japanese_date("R5.10.3") == date(2023, 10, 3)
    assert parse_japanese_date("R5/10/3") == date(2023, 10, 3)

def test_parse_showa_format():
    """昭和形式のパース"""
    assert parse_japanese_date("昭和60年3月15日") == date(1985, 3, 15)
    assert parse_japanese_date("S60.3.15") == date(1985, 3, 15)

def test_parse_heisei_format():
    """平成形式のパース"""
    assert parse_japanese_date("平成31年4月30日") == date(2019, 4, 30)
    assert parse_japanese_date("H31.4.30") == date(2019, 4, 30)

def test_parse_western_format():
    """西暦形式のパース"""
    assert parse_japanese_date("2025/10/3") == date(2025, 10, 3)
    assert parse_japanese_date("2025-10-03") == date(2025, 10, 3)

def test_invalid_era_date():
    """無効な元号日付"""
    with pytest.raises(ValueError):
        parse_japanese_date("令和元年3月1日")  # 令和は5月1日開始

def test_gannen_format():
    """元年形式"""
    assert parse_japanese_date("令和元年5月1日") == date(2019, 5, 1)
    assert parse_japanese_date("平成元年1月8日") == date(1989, 1, 8)
```

---

## 📊 期待される成果物

### バックエンド
- FastAPIアプリケーション
- RESTful API + WebSocket API
- 元号変換ライブラリ
- OpenAPI仕様書

### フロントエンド
- Next.js Webアプリケーション
- レスポンシブUI
- 元号対応日付入力コンポーネント
- 対話的家系図エディター

### インフラ
- Dockerコンテナ
- CI/CDパイプライン

### ドキュメント
- API仕様書
- ユーザーマニュアル
- 開発者ガイド

---

## 🎯 品質目標

| 指標 | 目標 |
|------|------|
| テストカバレッジ | 80%以上 |
| Lighthouse Performance | 90以上 |
| Lighthouse Accessibility | 100 |
| mypy型チェック | 0 errors |
| ESLint | 0 errors |
| レスポンス時間 | API < 500ms |
| ページ読み込み | < 3秒 |

---

**最終更新日**: 2025年10月3日
**バージョン**: 1.0.0
**ステータス**: 仕様策定完了
