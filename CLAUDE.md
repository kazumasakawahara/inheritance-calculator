<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# 相続人・相続割合確定アプリケーション - 仕様書

## 📋 プロジェクト概要

### プロジェクト名
**Inheritance Calculator (相続計算機)**

### 目的
日本の民法に基づいた相続人の資格確定と相続割合（相続分）の計算を自動化するアプリケーション。代襲相続、再転相続、相続放棄などの複雑なケースにも対応し、実務での判断を支援する。

### 対象ユーザー
- 司法書士
- 弁護士
- 税理士
- 行政書士
- 相続手続きに関わる実務家

---

## 🎯 機能要件

### 1. コア機能

#### 1.1 相続関係の登録・管理
- **被相続人（故人）の基本情報登録**
  - 氏名
  - 死亡日
  - その他識別情報

- **相続人候補の登録**
  - 氏名
  - 続柄（配偶者、子、父母、祖父母、兄弟姉妹など）
  - 生死状態
  - 死亡日（該当する場合）

- **家系図の構築**
  - 親子関係の定義
  - 婚姻関係の定義
  - 養子縁組の記録

#### 1.2 相続資格の判定

##### 第1順位：子（直系卑属）
- 実子・養子の判定
- 胎児の考慮（生きて生まれることが条件）
- 代襲相続の判定
  - 子が被相続人より先に死亡した場合
  - 子が相続欠格・相続廃除された場合
  - その孫（被相続人の直系卑属）が代襲

##### 第2順位：直系尊属
- 父母、祖父母の判定
- 第1順位の相続人がいない場合のみ相続
- 親等の近い者が優先（父母がいれば祖父母は相続できない）

##### 第3順位：兄弟姉妹
- 全血兄弟姉妹と半血兄弟姉妹の区別
- 第1順位、第2順位の相続人がいない場合のみ相続
- 代襲相続は1代のみ（甥・姪まで、その子への再代襲は認められない）

##### 配偶者
- 常に相続人となる
- 内縁関係は含まれない
- 法律上の婚姻関係が必要

#### 1.3 相続割合（法定相続分）の計算

##### 配偶者と子
- 配偶者：1/2
- 子：1/2（子が複数いる場合は均等に分割）

##### 配偶者と直系尊属
- 配偶者：2/3
- 直系尊属：1/3（複数いる場合は均等に分割）

##### 配偶者と兄弟姉妹
- 配偶者：3/4
- 兄弟姉妹：1/4（複数いる場合は均等に分割）
- 半血兄弟姉妹の相続分は全血兄弟姉妹の1/2

##### 配偶者のみ
- 配偶者：全部

##### 子のみ、直系尊属のみ、兄弟姉妹のみ
- 該当する相続人で均等に分割

#### 1.4 特殊ケースの処理

##### 相続放棄
- 相続放棄した者は初めから相続人でなかったものとみなす
- 代襲相続は発生しない
- 次順位の相続人に権利が移行

##### 相続欠格
- 欠格事由の登録
- 代襲相続が発生する

##### 相続廃除
- 廃除の記録
- 代襲相続が発生する

##### 代襲相続
- 直系卑属（子の場合）：制限なく代襲
- 兄弟姉妹の場合：1代限り（甥・姪まで）

##### 再転相続
- 相続人が遺産分割前に死亡した場合
- その相続人の相続人が権利を承継

### 2. 対話型インターフェース機能

#### 2.1 AIエージェントによる質問応答
- **使用モデル**: Ollama経由でgpt-oss:20b
- **エージェントフレームワーク**: Agnos

#### 2.2 質問フロー
1. 被相続人の情報入力
2. 配偶者の有無確認
3. 子の有無と状態確認
4. 直系尊属の有無と状態確認
5. 兄弟姉妹の有無と状態確認
6. 代襲相続の可能性確認
7. 相続放棄・欠格・廃除の確認

#### 2.3 対話の特徴
- 自然言語での質問・回答
- 状況に応じた動的な質問生成
- 複雑なケースでの追加質問
- 入力内容の確認と修正機能

### 3. グラフデータベース機能

#### 3.1 Neo4jによるデータモデリング

##### ノードタイプ
- **Person（人物）**
  - プロパティ：
    - `name`: 氏名
    - `is_alive`: 生死状態（boolean）
    - `death_date`: 死亡日（date, nullable）
    - `is_decedent`: 被相続人フラグ（boolean）
    - `birth_date`: 生年月日（date, nullable）
    - `gender`: 性別（string, nullable）

##### リレーションシップタイプ
- **CHILD_OF（子である）**
  - プロパティ：
    - `adoption`: 養子縁組の有無（boolean）
    - `is_biological`: 実子であるか（boolean）

- **SPOUSE_OF（配偶者である）**
  - プロパティ：
    - `marriage_date`: 婚姻日（date, nullable）
    - `divorce_date`: 離婚日（date, nullable）
    - `is_current`: 現在の配偶者か（boolean）

- **SIBLING_OF（兄弟姉妹である）**
  - プロパティ：
    - `blood_type`: 血縁タイプ（"full" or "half"）
    - `shared_parent`: 共通の親（"both", "mother", "father"）

- **RENOUNCED（相続放棄）**
  - プロパティ：
    - `renounce_date`: 放棄日（date）
    - `reason`: 理由（string, nullable）

- **DISQUALIFIED（相続欠格）**
  - プロパティ：
    - `reason`: 欠格事由（string）
    - `date`: 確定日（date）

- **DISINHERITED（相続廃除）**
  - プロパティ：
    - `reason`: 廃除事由（string）
    - `court_decision_date`: 審判確定日（date）

#### 3.2 Cypherクエリパターン

##### 配偶者の取得
```cypher
MATCH (decedent:Person {is_decedent: true})-[r:SPOUSE_OF]-(spouse:Person)
WHERE spouse.is_alive = true 
  AND r.is_current = true
  AND NOT EXISTS((spouse)-[:RENOUNCED]->(decedent))
RETURN spouse
```

##### 第1順位相続人（子）の取得
```cypher
MATCH (decedent:Person {is_decedent: true})<-[:CHILD_OF]-(child:Person)
WHERE child.is_alive = true
  AND NOT EXISTS((child)-[:RENOUNCED]->(decedent))
  AND NOT EXISTS((child)-[:DISQUALIFIED]->(decedent))
  AND NOT EXISTS((child)-[:DISINHERITED]->(decedent))
RETURN child
```

##### 代襲相続人の取得
```cypher
MATCH (decedent:Person {is_decedent: true})<-[:CHILD_OF]-(child:Person)<-[:CHILD_OF*]-(descendant:Person)
WHERE child.is_alive = false 
  AND descendant.is_alive = true
  AND child.death_date < decedent.death_date
  AND NOT EXISTS((descendant)-[:RENOUNCED]->(decedent))
RETURN descendant, length(path) as generation
```

##### 第2順位相続人（直系尊属）の取得
```cypher
MATCH (decedent:Person {is_decedent: true})-[:CHILD_OF*]->(ancestor:Person)
WHERE ancestor.is_alive = true
  AND NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person))  // 子がいない
  AND NOT EXISTS((ancestor)-[:RENOUNCED]->(decedent))
WITH ancestor, length(path) as generation
ORDER BY generation ASC
RETURN ancestor
LIMIT (SELECT MIN(generation))  // 最も近い世代のみ
```

##### 第3順位相続人（兄弟姉妹）の取得
```cypher
MATCH (decedent:Person {is_decedent: true})-[:SIBLING_OF]-(sibling:Person)
WHERE sibling.is_alive = true
  AND NOT EXISTS((decedent)<-[:CHILD_OF]-(:Person))  // 子がいない
  AND NOT EXISTS((decedent)-[:CHILD_OF*]->(:Person {is_alive: true}))  // 直系尊属がいない
  AND NOT EXISTS((sibling)-[:RENOUNCED]->(decedent))
RETURN sibling
```

### 4. 出力機能

#### 4.1 相続人一覧の表示
- 相続人の氏名
- 続柄
- 相続順位
- 相続割合（分数および百分率）
- 代襲相続の場合はその旨を表示

#### 4.2 相続関係図の出力
- テキストベースの家系図
- Graphviz形式のエクスポート（オプション）

#### 4.3 計算根拠の説明
- どの条文に基づいて判定したか
- 計算過程の表示
- 特殊ケースが適用された理由

---

## 🏗️ 技術スタック

### 言語・フレームワーク
- **Python**: 3.12以上
- **パッケージ管理**: uv

### データベース
- **Neo4j**: グラフデータベース
  - Community Edition推奨
  - ローカル実行（Dockerは使用しない）

### AI/ML
- **Ollama**: ローカルLLM実行環境
  - モデル: `gpt-oss:20b`
- **Agnos**: Pythonエージェントワークフローフレームワーク

### 主要ライブラリ
- `neo4j`: Neo4jドライバー
- `agnos`: エージェントワークフロー
- `ollama`: Ollama Python SDK
- `pydantic`: データバリデーション
- `python-dotenv`: 環境変数管理
- `rich`: CLIの美しい出力

---

## 📁 プロジェクト構造

```
inheritance-calculator/
├── pyproject.toml          # uvプロジェクト設定
├── uv.lock                 # 依存関係ロック
├── .env.example            # 環境変数テンプレート
├── .env                    # 環境変数（gitignore）
├── CLAUDE.md               # 本仕様書
├── README.md               # プロジェクト説明
│
├── src/
│   ├── __init__.py
│   │
│   ├── models/             # データモデル
│   │   ├── __init__.py
│   │   ├── person.py       # 人物モデル
│   │   ├── relationship.py # 関係性モデル
│   │   └── inheritance.py  # 相続計算結果モデル
│   │
│   ├── database/           # データベース層
│   │   ├── __init__.py
│   │   ├── neo4j_client.py # Neo4j接続クライアント
│   │   ├── queries.py      # Cypherクエリ集
│   │   └── schema.py       # データベーススキーマ定義
│   │
│   ├── services/           # ビジネスロジック層
│   │   ├── __init__.py
│   │   ├── inheritance_calculator.py  # 相続計算サービス
│   │   ├── heir_validator.py          # 相続人資格検証
│   │   └── share_calculator.py        # 相続割合計算
│   │
│   ├── agents/             # AIエージェント層
│   │   ├── __init__.py
│   │   ├── interview_agent.py     # 対話エージェント
│   │   ├── ollama_client.py       # Ollamaクライアント
│   │   └── prompts.py             # プロンプトテンプレート
│   │
│   ├── cli/                # CLIインターフェース
│   │   ├── __init__.py
│   │   ├── main.py         # メインCLI
│   │   ├── commands.py     # コマンド定義
│   │   └── display.py      # 表示ユーティリティ
│   │
│   └── utils/              # ユーティリティ
│       ├── __init__.py
│       ├── config.py       # 設定管理
│       ├── logger.py       # ロギング
│       └── validators.py   # バリデーション関数
│
├── tests/                  # テストコード
│   ├── __init__.py
│   ├── test_models/
│   ├── test_services/
│   └── test_integration/
│
├── scripts/                # ユーティリティスクリプト
│   ├── setup_neo4j.sh     # Neo4jセットアップ
│   └── seed_data.py       # サンプルデータ投入
│
└── docs/                   # ドキュメント
    ├── architecture.md     # アーキテクチャ設計
    ├── database_schema.md  # データベース設計
    └── user_guide.md       # ユーザーガイド
```

---

## 🔧 環境設定

### 必要な環境
- Python 3.12以上
- Neo4j Community Edition
- Ollama
  - gpt-oss:20bモデルをpull済み

### 環境変数（.env）
```bash
# Neo4j接続設定
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Ollama設定
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=logs/inheritance.log

# アプリケーション設定
APP_ENV=development
```

---

## 📝 実装タスク細分化

### Phase 1: 基盤構築（Week 1）

#### Task 1.1: プロジェクトセットアップ ✅
- [x] uvによるプロジェクト初期化
- [x] 依存関係の追加
- [x] ディレクトリ構造の作成
- [ ] .env.exampleの作成
- [ ] README.mdの作成

#### Task 1.2: データモデルの定義
- [ ] `Person`モデルの実装（Pydantic）
- [ ] `Relationship`モデルの実装
- [ ] `InheritanceResult`モデルの実装
- [ ] バリデーションルールの実装

#### Task 1.3: Neo4jデータベース層の実装
- [ ] Neo4j接続クライアントの実装
- [ ] 基本的なCRUD操作の実装
- [ ] スキーマ初期化スクリプトの作成
- [ ] 制約とインデックスの設定

### Phase 2: コアロジックの実装（Week 2）

#### Task 2.1: 相続人資格判定ロジック
- [ ] 配偶者判定の実装
- [ ] 第1順位（子）判定の実装
- [ ] 第2順位（直系尊属）判定の実装
- [ ] 第3順位（兄弟姉妹）判定の実装
- [ ] 代襲相続判定の実装

#### Task 2.2: 相続割合計算ロジック
- [ ] 配偶者+子の場合の計算
- [ ] 配偶者+直系尊属の場合の計算
- [ ] 配偶者+兄弟姉妹の場合の計算
- [ ] 単独相続の場合の計算
- [ ] 半血兄弟姉妹の調整計算

#### Task 2.3: Cypherクエリの実装
- [ ] 相続人取得クエリ群の実装
- [ ] 代襲相続判定クエリの実装
- [ ] 相続放棄・欠格処理クエリの実装
- [ ] パフォーマンス最適化

### Phase 3: AIエージェント統合（Week 3）

#### Task 3.1: Ollamaクライアントの実装
- [ ] Ollama接続クライアントの実装
- [ ] モデル初期化と設定
- [ ] エラーハンドリング
- [ ] レスポンスパース処理

#### Task 3.2: Agnosエージェントの実装
- [ ] 対話エージェントの基本構造
- [ ] 質問生成ロジックの実装
- [ ] 回答解析ロジックの実装
- [ ] 状態管理の実装

#### Task 3.3: プロンプトエンジニアリング
- [ ] システムプロンプトの作成
- [ ] 質問テンプレートの作成
- [ ] Few-shot例の準備
- [ ] プロンプト最適化

### Phase 4: CLIインターフェース（Week 4）

#### Task 4.1: メインCLIの実装
- [ ] コマンドライン引数パーサー
- [ ] サブコマンドの定義
- [ ] インタラクティブモードの実装
- [ ] バッチモードの実装

#### Task 4.2: 表示機能の実装
- [ ] Rich libraryを使った表示
- [ ] 相続人一覧の表示
- [ ] 家系図の表示
- [ ] 計算過程の表示

#### Task 4.3: データ入出力
- [ ] JSONファイルからの読み込み
- [ ] CSVファイルからの読み込み
- [ ] 結果のエクスポート機能
- [ ] レポート生成機能

### Phase 5: テストとドキュメント（Week 5）

#### Task 5.1: ユニットテストの実装
- [ ] モデルのテスト
- [ ] サービス層のテスト
- [ ] データベース層のテスト
- [ ] エージェント層のテスト

#### Task 5.2: 統合テストの実装
- [ ] エンドツーエンドテストシナリオ
- [ ] 複雑なケースのテスト
- [ ] エラーケースのテスト
- [ ] パフォーマンステスト

#### Task 5.3: ドキュメント作成
- [ ] アーキテクチャドキュメント
- [ ] データベース設計ドキュメント
- [ ] ユーザーガイド
- [ ] API仕様書

### Phase 6: 最適化とデプロイ準備（Week 6）

#### Task 6.1: パフォーマンス最適化
- [ ] Cypherクエリの最適化
- [ ] キャッシング戦略の実装
- [ ] バッチ処理の最適化
- [ ] メモリ使用量の最適化

#### Task 6.2: エラーハンドリングとロギング
- [ ] 包括的なエラーハンドリング
- [ ] ロギング戦略の実装
- [ ] エラーメッセージの日本語化
- [ ] デバッグモードの実装

#### Task 6.3: 配布準備
- [ ] セットアップスクリプトの作成
- [ ] 依存関係の最終確認
- [ ] ドキュメントの最終レビュー
- [ ] リリースノートの作成

---

## 🧪 テストケース

### 基本ケース

#### ケース1: 配偶者と子
- 被相続人: A
- 相続人: 配偶者B、子C、子D
- 期待結果:
  - B: 1/2
  - C: 1/4
  - D: 1/4

#### ケース2: 配偶者と直系尊属
- 被相続人: A（子なし）
- 相続人: 配偶者B、父C、母D
- 期待結果:
  - B: 2/3
  - C: 1/6
  - D: 1/6

#### ケース3: 配偶者と兄弟姉妹
- 被相続人: A（子なし、直系尊属なし）
- 相続人: 配偶者B、兄C、妹D
- 期待結果:
  - B: 3/4
  - C: 1/8
  - D: 1/8

### 複雑ケース

#### ケース4: 代襲相続（子の代襲）
- 被相続人: A
- 配偶者: B（存命）
- 子C（死亡、子D・Eあり）、子F（存命）
- 期待結果:
  - B: 1/2
  - D: 1/8（Cの代襲）
  - E: 1/8（Cの代襲）
  - F: 1/4

#### ケース5: 代襲相続（兄弟姉妹の代襲）
- 被相続人: A（子なし、直系尊属なし）
- 配偶者: B（存命）
- 兄C（死亡、子D・Eあり）、妹F（存命）
- 期待結果:
  - B: 3/4
  - D: 1/16（Cの代襲）
  - E: 1/16（Cの代襲）
  - F: 1/8

#### ケース6: 半血兄弟姉妹
- 被相続人: A（子なし、直系尊属なし）
- 配偶者: B（存命）
- 全血兄C（父母同じ）、半血兄D（父のみ同じ）
- 期待結果:
  - B: 3/4
  - C: 1/6（1/4 × 2/3）
  - D: 1/12（1/4 × 1/3）

#### ケース7: 相続放棄
- 被相続人: A
- 子B（相続放棄）、子C（存命）、父D（存命）
- 期待結果:
  - C: 全部（Bは放棄、他の子がいるので直系尊属には移行しない）

#### ケース8: 再転相続
- 被相続人: A（2025年1月死亡）
- 子B（2025年2月死亡、遺産分割前）、Bの配偶者C、Bの子D
- 期待結果:
  - Bの相続分（全部）がCとDに再転相続される

---

## 🎨 ユーザーインターフェース設計

### 対話フローの例

```
=================================
相続人・相続割合確定システム
=================================

被相続人の情報を入力してください。

被相続人の氏名: 山田太郎
死亡日 (YYYY-MM-DD): 2025-06-15

配偶者はいますか？ (はい/いいえ): はい
配偶者の氏名: 山田花子

子はいますか？ (はい/いいえ): はい
子の人数: 2

1人目の子の情報を入力してください。
氏名: 山田一郎
存命ですか？ (はい/いいえ): はい

2人目の子の情報を入力してください。
氏名: 山田二郎
存命ですか？ (はい/いいえ): いいえ
死亡日 (YYYY-MM-DD): 2020-03-10

山田二郎さんに子（被相続人の孫）はいますか？ (はい/いいえ): はい
人数: 1

1人目の孫の情報を入力してください。
氏名: 山田三郎
存命ですか？ (はい/いいえ): はい

相続放棄、相続欠格、相続廃除はありますか？ (はい/いいえ): いいえ

--- 計算結果 ---

✓ 相続人の確定
┌──────────────┬──────────┬──────────┬──────────┐
│ 氏名         │ 続柄     │ 相続順位 │ 相続割合 │
├──────────────┼──────────┼──────────┼──────────┤
│ 山田花子     │ 配偶者   │ 常に相続 │ 1/2      │
│ 山田一郎     │ 子       │ 第1順位  │ 1/4      │
│ 山田三郎     │ 孫(代襲) │ 第1順位  │ 1/4      │
└──────────────┴──────────┴──────────┴──────────┘

✓ 計算根拠
• 配偶者は常に相続人となります（民法890条）
• 子は第1順位の相続人です（民法887条1項）
• 山田二郎さんが被相続人より先に死亡しているため、
  その子である山田三郎さんが代襲相続します（民法887条2項）

• 配偶者と子が相続人の場合、
  配偶者は1/2、子は残りの1/2を均等に分けます（民法900条1号）

次のアクション:
1. 結果をJSONで保存
2. 結果をPDFレポートで出力
3. 新しい相続案件を入力
4. 終了

選択してください (1-4): 
```

---

## 🚀 今後の拡張予定

### Phase 7以降の機能（オプショナル）

1. **遺留分計算機能**
   - 遺留分侵害額の計算
   - 遺留分侵害額請求のシミュレーション

2. **遺言書対応**
   - 遺言書の内容入力
   - 遺言書と法定相続分の比較
   - 遺留分侵害の検証

3. **税額計算**
   - 相続税の概算計算
   - 基礎控除、配偶者控除の適用
   - 税務署への提出書類生成

4. **Web UI版**
   - FastAPIによるRESTful API
   - Vue.js/Reactによるフロントエンド
   - ビジュアルな家系図編集

5. **データ永続化**
   - 案件のセッション保存
   - 履歴管理
   - エクスポート/インポート機能

---

## 📚 参考資料

### 法律条文
- 民法第5編「相続」（第882条～第1050条）
  - 第887条：子の相続権、代襲相続
  - 第889条：直系尊属・兄弟姉妹の相続権
  - 第890条：配偶者の相続権
  - 第900条：法定相続分
  - 第901条：代襲相続人の相続分
  - 第938条～第940条：相続放棄
  - 第891条：相続欠格
  - 第892条～第894条：相続廃除

### 技術ドキュメント
- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)
- [Agnos Documentation](https://github.com/AGNOSTech/agnos)
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Rich Documentation](https://rich.readthedocs.io/)

---

## 🤝 開発ガイドライン

### コーディング規約
- PEP 8に準拠
- Type hintsを必ず使用
- Docstringsはスタイル（Google形式）で記述
- 変数名・関数名は英語、コメントは日本語

### Gitワークフロー
- ブランチ戦略: Git Flow
- コミットメッセージ: Conventional Commits形式
- プルリクエスト必須

### コードレビュー基準
- テストカバレッジ80%以上
- 型チェック（mypy）合格
- リンター（ruff）合格
- セキュリティチェック合格

---

## ⚠️ 注意事項

1. **法的免責事項**
   - このアプリケーションは相続実務の補助ツールであり、法的助言を提供するものではありません
   - 実際の相続手続きは専門家（弁護士、司法書士等）に相談してください

2. **データプライバシー**
   - 個人情報を含むデータの取り扱いに注意
   - ローカル環境での実行を推奨
   - データベースのアクセス制御を適切に設定

3. **法改正対応**
   - 民法は改正される可能性があります
   - 定期的な法律の確認と更新が必要

---

## 📞 サポート・コンタクト

- Issue Tracker: （GitHubリポジトリのIssuesセクション）
- ドキュメント: `docs/`ディレクトリ
- 開発者: Claude Code AI Assistant

---

**最終更新日**: 2025年10月2日
**バージョン**: 1.0.0
**ステータス**: 開発中（Phase 1完了）