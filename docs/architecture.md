# 相続計算機 - アーキテクチャ設計書

## 📋 目次

1. [概要](#概要)
2. [アーキテクチャ原則](#アーキテクチャ原則)
3. [システムアーキテクチャ](#システムアーキテクチャ)
4. [レイヤー構成](#レイヤー構成)
5. [データモデル](#データモデル)
6. [主要コンポーネント](#主要コンポーネント)
7. [データフロー](#データフロー)
8. [拡張性と保守性](#拡張性と保守性)

---

## 概要

相続計算機は、日本の民法に基づいた相続計算を自動化するPythonアプリケーションです。クリーンアーキテクチャの原則に従い、ビジネスロジックと外部依存を分離した設計となっています。

### アーキテクチャスタイル

- **レイヤードアーキテクチャ**: 責務の明確な分離
- **ドメイン駆動設計（DDD）**: ドメインモデル中心の設計
- **リポジトリパターン**: データアクセスの抽象化
- **依存性注入**: テスタビリティの向上

---

## アーキテクチャ原則

### 1. 関心の分離（Separation of Concerns）

各レイヤーは明確な責務を持ち、他のレイヤーに依存しないようにします。

### 2. 依存性の逆転（Dependency Inversion）

高レベルモジュールは低レベルモジュールに依存せず、抽象に依存します。

### 3. 単一責任の原則（Single Responsibility Principle）

各クラス・モジュールは1つの責務のみを持ちます。

### 4. オープン・クローズドの原則（Open-Closed Principle）

拡張に対して開いており、修正に対して閉じている設計を目指します。

### 5. テスタビリティ

すべてのコンポーネントは独立してテスト可能な設計とします。

---

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    プレゼンテーション層                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   CLI        │  │ Interactive  │  │ AI Interview │     │
│  │  Commands    │  │    Prompts   │  │    Agent     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    アプリケーション層                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Inheritance  │  │ Report       │  │ Contact      │     │
│  │ Calculator   │  │ Generator    │  │ Collector    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      ドメイン層                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Heir         │  │ Share        │  │ Domain       │     │
│  │ Validator    │  │ Calculator   │  │ Models       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    インフラストラクチャ層                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Neo4j        │  │ File I/O     │  │ Ollama       │     │
│  │ Repository   │  │ (CSV/JSON)   │  │ Client       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## レイヤー構成

### 1. プレゼンテーション層 (`src/cli/`)

ユーザーインターフェースとコマンドライン処理を担当します。

**主要コンポーネント:**

- `main.py`: CLIエントリーポイント
- `commands.py`: コマンド実装（calc, validate, tree, etc.）
- `prompts.py`: 対話型プロンプト
- `contact_input.py`: 連絡先情報収集
- `display.py`: 結果表示
- `report_generator.py`: レポート生成（Markdown, PDF, CSV）
- `family_tree_generator.py`: 家系図生成

**責務:**

- ユーザー入力の受付と検証
- 結果の表示とフォーマット
- ファイル入出力の制御
- エラーハンドリングとユーザーフィードバック

### 2. アプリケーション層 (`src/services/`)

ビジネスロジックのオーケストレーションを担当します。

**主要コンポーネント:**

- `inheritance_calculator.py`: 相続計算のオーケストレーター
- `heir_validator.py`: 相続人資格の検証
- `share_calculator.py`: 相続割合の計算
- `neo4j_service.py`: Neo4jデータベースサービス

**責務:**

- ビジネスロジックの調整
- トランザクション管理
- ドメインサービスの呼び出し
- データ変換とバリデーション

### 3. ドメイン層 (`src/models/`)

ビジネスドメインの概念とルールを表現します。

**主要コンポーネント:**

- `person.py`: 人物モデル
  - 基本情報（氏名、生死、生年月日、死亡日）
  - 連絡先情報（住所、電話番号、メールアドレス）
- `relationship.py`: 関係性モデル
  - 親子関係、配偶者関係、兄弟姉妹関係
  - 相続放棄、相続欠格、相続廃除
- `inheritance.py`: 相続計算結果モデル
  - 相続人情報（Heir）
  - 相続順位（HeritageRank）
  - 代襲相続タイプ（SubstitutionType）

**責務:**

- ビジネスルールの表現
- ドメインロジックのカプセル化
- 不変条件の維持
- ドメインイベントの発行

### 4. インフラストラクチャ層 (`src/database/`, `src/agents/`, `src/utils/`)

外部システムとの統合を担当します。

**主要コンポーネント:**

- **データベース** (`src/database/`)
  - `neo4j_client.py`: Neo4j接続クライアント
  - `repositories.py`: リポジトリ実装
  - `queries.py`: Cypherクエリ集

- **AIエージェント** (`src/agents/`)
  - `interview_agent.py`: 対話型インタビューエージェント
  - `ollama_client.py`: Ollamaクライアント

- **ユーティリティ** (`src/utils/`)
  - `config.py`: 設定管理
  - `logger.py`: ロギング
  - `validators.py`: バリデーション
  - `era_converter.py`: 元号変換

**責務:**

- 外部システムとの通信
- データの永続化と取得
- 外部APIの呼び出し
- ユーティリティ機能の提供

---

## データモデル

### ドメインモデル

#### Person（人物）

```python
class Person(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str                              # 氏名
    is_alive: bool = True                  # 生存状態
    is_decedent: bool = False              # 被相続人フラグ
    birth_date: Optional[date] = None      # 生年月日
    death_date: Optional[date] = None      # 死亡日
    gender: Optional[Gender] = None        # 性別

    # 連絡先情報（Phase 5で追加）
    address: Optional[str] = None          # 住所
    phone: Optional[str] = None            # 電話番号
    email: Optional[str] = None            # メールアドレス
```

#### Heir（相続人）

```python
class Heir(BaseModel):
    person: Person                         # 相続人
    rank: HeritageRank                     # 相続順位
    share: Fraction                        # 相続割合（分数）
    share_percentage: float                # 相続割合（百分率）
    is_substitution: bool = False          # 代襲相続フラグ
    substitution_type: SubstitutionType    # 代襲相続タイプ
    original_heir: Optional[Person] = None # 元の相続人（代襲の場合）
```

#### InheritanceResult（相続計算結果）

```python
class InheritanceResult(BaseModel):
    decedent: Person                       # 被相続人
    heirs: List[Heir]                      # 相続人リスト
    calculation_basis: List[str]           # 計算根拠（民法条文）
    total_heirs: int                       # 相続人総数
    has_spouse: bool                       # 配偶者の有無
    has_children: bool                     # 子の有無
    has_parents: bool                      # 直系尊属の有無
    has_siblings: bool                     # 兄弟姉妹の有無
```

### Neo4jデータモデル

#### ノードタイプ

**Person（人物）**

```cypher
(:Person {
  name: string,
  is_alive: boolean,
  is_decedent: boolean,
  birth_date: date,
  death_date: date,
  gender: string,
  address: string,    // Phase 5で追加
  phone: string,      // Phase 5で追加
  email: string       // Phase 5で追加
})
```

#### リレーションシップタイプ

```cypher
// 親子関係
(:Person)-[:CHILD_OF {
  adoption: boolean,
  is_biological: boolean
}]->(:Person)

// 配偶者関係
(:Person)-[:SPOUSE_OF {
  marriage_date: date,
  divorce_date: date,
  is_current: boolean
}]-(:Person)

// 兄弟姉妹関係
(:Person)-[:SIBLING_OF {
  blood_type: string,  // "full" or "half"
  shared_parent: string // "both", "mother", "father"
}]-(:Person)

// 相続放棄
(:Person)-[:RENOUNCED {
  renounce_date: date,
  reason: string
}]->(:Person)

// 相続欠格
(:Person)-[:DISQUALIFIED {
  reason: string,
  date: date
}]->(:Person)

// 相続廃除
(:Person)-[:DISINHERITED {
  reason: string,
  court_decision_date: date
}]->(:Person)
```

---

## 主要コンポーネント

### InheritanceCalculator（相続計算オーケストレーター）

**責務**: 相続計算全体の流れを制御

```python
class InheritanceCalculator(BaseService):
    def calculate(
        self,
        decedent: Person,
        spouses: List[Person],
        children: List[Person],
        parents: List[Person],
        siblings: List[Person],
        renounced: Optional[List[Person]] = None,
        disqualified: Optional[List[Person]] = None,
        disinherited: Optional[List[Person]] = None,
        sibling_blood_types: Optional[Dict[str, BloodType]] = None,
        retransfer_heirs_info: Optional[List[Dict[str, Any]]] = None
    ) -> InheritanceResult:
        # 1. 入力検証
        # 2. 相続人資格の判定（HeirValidator）
        # 3. 相続割合の計算（ShareCalculator）
        # 4. 結果の構築と返却
```

### HeirValidator（相続人資格検証）

**責務**: 民法に基づく相続人資格の判定

```python
class HeirValidator(BaseService):
    def determine_heirs(
        self,
        decedent: Person,
        spouses: List[Person],
        children: List[Person],
        parents: List[Person],
        siblings: List[Person],
        renounced: List[Person],
        disqualified: List[Person],
        disinherited: List[Person],
        sibling_blood_types: Dict[str, BloodType]
    ) -> Tuple[List[Heir], List[str]]:
        # 1. 配偶者の判定
        # 2. 第1順位（子）の判定
        # 3. 代襲相続の判定
        # 4. 第2順位（直系尊属）の判定
        # 5. 第3順位（兄弟姉妹）の判定
```

### ShareCalculator（相続割合計算）

**責務**: 法定相続分の計算

```python
class ShareCalculator(BaseService):
    def calculate_shares(
        self,
        heirs: List[Heir],
        has_spouse: bool,
        has_children: bool,
        has_parents: bool,
        has_siblings: bool
    ) -> List[str]:
        # 1. 相続パターンの判定
        # 2. 配偶者の割合計算
        # 3. 他の相続人の割合計算
        # 4. 半血兄弟姉妹の調整
```

### ContactInfoCollector（連絡先情報収集）

**責務**: 相続人の連絡先情報の対話的収集

```python
class ContactInfoCollector:
    def collect_contact_info_for_heirs(
        self,
        result: InheritanceResult
    ) -> List[Person]:
        # 1. 連絡先入力の確認
        # 2. 各相続人の連絡先情報収集
        #    - 住所
        #    - 電話番号（バリデーション付き）
        #    - メールアドレス（バリデーション付き）
        # 3. 更新された人物リストの返却
```

### ReportGenerator（レポート生成）

**責務**: 各種形式でのレポート生成

```python
class ReportGenerator:
    @staticmethod
    def generate_markdown(
        result: InheritanceResult,
        output_path: Path
    ) -> None:
        # 1. Markdownフォーマットでレポート生成
        # 2. 連絡先情報セクション（条件付き）

    @staticmethod
    def generate_pdf(
        result: InheritanceResult,
        output_path: Path
    ) -> None:
        # 1. PDFフォーマットでレポート生成
        # 2. ReportLabによるスタイリング
        # 3. 連絡先情報テーブル（条件付き）

    @staticmethod
    def export_contact_csv(
        result: InheritanceResult,
        output_path: Path
    ) -> None:
        # 1. 連絡先情報をCSV形式でエクスポート
        # 2. UTF-8-sig エンコーディング（Excel互換）
```

### PersonRepository（人物リポジトリ）

**責務**: Neo4j Personノードのデータアクセス

```python
class PersonRepository:
    def create(self, person: Person) -> Person:
        # 連絡先情報を含むPersonノードを作成

    def update(self, person: Person) -> Person:
        # 連絡先情報を含むPersonノードを更新

    def find_by_name(self, name: str) -> Optional[Person]:
        # 名前で検索

    def find_decedent(self) -> Optional[Person]:
        # 被相続人を検索
```

---

## データフロー

### 1. 相続計算フロー（ファイル入力）

```
[JSONファイル]
    ↓
[calculate_from_file] (commands.py)
    ↓
[InheritanceCalculator.calculate]
    ↓
[HeirValidator.determine_heirs] → 相続人資格判定
    ↓
[ShareCalculator.calculate_shares] → 相続割合計算
    ↓
[InheritanceResult] 構築
    ↓
[display_result] 結果表示
    ↓
[ContactInfoCollector.collect_contact_info_for_heirs] 連絡先収集
    ↓
[ReportGenerator.generate_*] レポート生成（オプション）
    ↓
[Neo4jService.save_inheritance_case] DB保存（オプション）
```

### 2. 連絡先情報収集フロー

```
[InheritanceResult] 相続計算完了
    ↓
[ContactInfoCollector] 初期化
    ↓
[ユーザーに確認] 連絡先情報を入力しますか？
    ↓ (Yes)
[各相続人について繰り返し]
    ├─ 住所入力
    ├─ 電話番号入力（バリデーション）
    └─ メールアドレス入力（バリデーション）
    ↓
[Person.set_contact_info] 連絡先情報設定
    ↓
[display_contact_summary] サマリー表示
    ↓
[更新されたPersonリスト] 返却
```

### 3. レポート生成フロー

```
[InheritanceResult] 相続計算完了
    ↓
[ReportGenerator.generate_*] 形式に応じた生成
    ├─ [Markdown] → テーブル形式 + 連絡先セクション
    ├─ [PDF] → ReportLab + スタイリング + 連絡先テーブル
    └─ [CSV] → UTF-8-sig + 連絡先情報
    ↓
[ファイル出力]
    ↓
[オプション] 連絡先CSVの追加エクスポート確認
```

### 4. Neo4j保存フロー

```
[InheritanceResult] 相続計算完了
    ↓
[Neo4jClient] 接続確立
    ↓
[Neo4jService.save_inheritance_case]
    ├─ [PersonRepository.create] Personノード作成（連絡先含む）
    ├─ [RelationshipRepository.create_*] リレーションシップ作成
    │   ├─ CHILD_OF
    │   ├─ SPOUSE_OF
    │   ├─ SIBLING_OF
    │   ├─ RENOUNCED
    │   ├─ DISQUALIFIED
    │   └─ DISINHERITED
    └─ トランザクション完了
```

---

## 拡張性と保守性

### 1. レイヤーの独立性

各レイヤーは抽象インターフェースを通じて通信するため、実装を変更しても他のレイヤーに影響を与えません。

**例**: データベースをNeo4jからPostgreSQLに変更する場合

- `PersonRepository`インターフェースは変更不要
- 新しい`PostgreSQLPersonRepository`を実装
- 依存性注入でリポジトリを切り替え

### 2. ドメインロジックの保護

ビジネスルールはドメイン層に集中しており、UIやデータベースの変更から隔離されています。

**例**: 相続割合の計算ロジック変更

- `ShareCalculator`のみを修正
- CLI、レポート生成、データベース層は影響なし

### 3. テストの容易性

各コンポーネントは独立してテスト可能です。

```python
# ユニットテスト例
def test_heir_validator():
    validator = HeirValidator()
    # モックデータで相続人判定をテスト

# 統合テスト例
def test_full_calculation_flow():
    # エンドツーエンドのフロー検証
```

### 4. 新機能の追加

新しい機能は既存コードを変更せずに追加できます。

**例**: 連絡先情報機能の追加（Phase 5）

- `Person`モデルに連絡先フィールド追加
- `ContactInfoCollector`クラス追加
- `ReportGenerator`に連絡先セクション追加
- 既存の相続計算ロジックは無変更

### 5. 設定の外部化

環境変数や設定ファイルによる設定の外部化により、環境ごとの動作変更が容易です。

```python
# src/utils/config.py
class Config:
    @staticmethod
    def get_neo4j_uri() -> str:
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")
```

---

## パフォーマンスとスケーラビリティ

### 1. データベースクエリの最適化

- インデックスとConstraintの適切な設定
- Cypherクエリのパフォーマンスチューニング
- バッチ処理による複数ノード作成

### 2. メモリ管理

- Pydanticモデルの効率的な利用
- 大量データ処理時のストリーミング処理
- ガベージコレクションの考慮

### 3. 並列処理

- 独立した計算の並列化
- 非同期I/O処理（将来的な拡張）

---

## セキュリティ

### 1. データ保護

- 個人情報（連絡先情報）の適切な管理
- Neo4jアクセス制御
- ログにおける個人情報のマスキング

### 2. 入力検証

- すべてのユーザー入力の検証
- Pydanticによる型安全性
- SQLインジェクション対策（Cypherクエリのパラメータ化）

### 3. エラーハンドリング

- 適切なエラーメッセージ
- スタックトレースの制御
- ログレベルの管理

---

## モニタリングとロギング

### 1. 構造化ロギング

```python
# src/utils/logger.py
logger.info(
    "Calculated inheritance shares",
    extra={
        "decedent": decedent.name,
        "heirs_count": len(heirs),
        "basis": calculation_basis
    }
)
```

### 2. メトリクス

- 計算時間の計測
- データベースアクセス回数
- エラー発生率

---

## 今後の拡張

### 1. Web UI

- FastAPIによるRESTful API
- Vue.js/ReactによるSPA
- リアルタイム家系図編集

### 2. 遺留分計算

- 遺留分侵害額の自動計算
- 遺言書の考慮

### 3. 税額計算

- 相続税の概算計算
- 基礎控除、配偶者控除の適用

### 4. マルチテナント対応

- 複数事務所の管理
- ユーザー認証・認可
- データの論理的分離

---

## 参考資料

- [クリーンアーキテクチャ](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [ドメイン駆動設計](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**最終更新日**: 2025年10月17日
**バージョン**: 1.1.0
