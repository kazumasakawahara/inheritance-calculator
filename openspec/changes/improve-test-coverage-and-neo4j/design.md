# Design Document: Test Coverage and Neo4j Integration

## Context

現在のプロジェクトは以下の状態です：

- **テストカバレッジ**: 59%（目標75%未達）
- **Neo4jモック**: 実装済み（外部サーバー不要）
- **Neo4j統合**: リポジトリパターンは定義済みだが実装が不完全（18%カバレッジ）
- **テスト戦略**: ユニットテスト中心、統合テストが不足

### 制約条件

1. **Neo4j依存の最小化**
   - ユニットテストはモックで実行（既存の実装を活用）
   - 統合テストはオプショナル（Neo4jがない環境でもテスト可能）

2. **段階的改善**
   - 一度にすべてを実装するのではなく、優先度に基づいて段階的に改善
   - 各段階で検証可能な成果物を作成

3. **後方互換性**
   - 既存のテストを壊さない
   - 既存のモック実装を活用

## Goals / Non-Goals

### Goals

1. **テストカバレッジを75%以上に向上**
   - Neo4j Repositories: 18% → 85%
   - CLI Commands: 25% → 70%
   - Neo4j Service: 0% → 80%
   - Heir Validator: 64% → 85%

2. **Neo4j統合の完成**
   - Repository層の実装完了
   - 統合テストの追加（オプショナル実行）
   - Cypherクエリの検証

3. **テストインフラの改善**
   - 再利用可能なフィクスチャ
   - テストユーティリティ
   - ドキュメント化

### Non-Goals

- **パフォーマンス最適化**: 現時点ではパフォーマンスよりも正確性を優先
- **CI/CDの完全自動化**: Neo4j統合テストのCI/CD統合は将来の課題
- **Agent層のテスト**: Ollama依存のため、今回のスコープ外（0%で許容）

## Decisions

### Decision 1: Neo4j統合テストのオプショナル実行

**選択**: pytest markersを使用してオプショナル実行

```python
@pytest.mark.integration
@pytest.mark.skipif(
    "not config.getoption('--run-integration', default=False)",
    reason="Integration tests require Neo4j running"
)
def test_neo4j_integration():
    # 統合テスト
    pass
```

**理由**:
- ✅ 開発者がNeo4jなしでユニットテストを実行可能
- ✅ CI/CDでNeo4jを起動して統合テストを実行可能
- ✅ 柔軟性が高い

**代替案**:
- Docker Composeで自動起動: CI/CDが複雑になる
- 常にモックのみ: 実際のクエリの正確性が検証できない

### Decision 2: Repository実装の優先順位

**選択**: PersonRepository → RelationshipRepository → Neo4jService の順

**理由**:
- PersonRepositoryは最も基本的で依存関係が少ない
- RelationshipRepositoryはPersonに依存
- Neo4jServiceは両方のRepositoryに依存

**タスクの依存関係**:
```
PersonRepository (1.1)
    ↓
RelationshipRepository (1.2)
    ↓
Repository Integration Tests (1.3)
    ↓
Neo4jService (2.1)
    ↓
Neo4jService Tests (2.2)
```

### Decision 3: テストフィクスチャの標準化

**選択**: `tests/conftest.py`に共通フィクスチャを集約

```python
# tests/conftest.py
@pytest.fixture
def sample_person():
    """標準的なPersonオブジェクト"""
    return Person(
        name="山田太郎",
        birth_date=date(1950, 1, 1),
        is_alive=False,
        death_date=date(2025, 6, 15),
        is_decedent=True
    )

@pytest.fixture
def sample_family():
    """標準的な家族構成"""
    # ...
```

**理由**:
- ✅ テストデータの一貫性
- ✅ 再利用性の向上
- ✅ メンテナンスの容易さ

**代替案**:
- 各テストファイルに個別定義: 重複が多く、メンテナンスが困難
- ファクトリーパターン: 過度に複雑

### Decision 4: Cypherクエリのテスト戦略

**選択**: ユニットテスト（モック） + 統合テスト（実Neo4j）の両方

**ユニットテスト**:
```python
def test_find_children_query(mocker):
    """Cypherクエリの構築をテスト（モック使用）"""
    mock_session = mocker.patch('neo4j.Session')
    repo = PersonRepository(mock_client)
    repo.find_children("parent")

    # クエリが正しく構築されたか検証
    mock_session.run.assert_called_with(
        "MATCH (p:Person {name: $name})<-[:CHILD_OF]-(c:Person) RETURN c",
        {"name": "parent"}
    )
```

**統合テスト**:
```python
@pytest.mark.integration
def test_find_children_actual(neo4j_test_db):
    """実際のNeo4jでクエリ実行をテスト"""
    # 実際のNeo4jに対してクエリを実行
    # データの正確性を検証
```

**理由**:
- ユニットテスト: 高速、Neo4j不要、クエリ構築の検証
- 統合テスト: 実環境での動作保証、クエリ結果の検証

## Risks / Trade-offs

### Risk 1: Neo4j統合テストの実行コスト

**リスク**: 統合テストの実行に時間がかかる（Neo4j起動が必要）

**緩和策**:
- デフォルトではスキップ（`--run-integration`フラグで実行）
- CI/CDでは並列実行
- ローカルでは開発者が必要に応じて実行

**影響**: 低（オプショナル実行のため）

### Risk 2: テストデータの管理

**リスク**: 統合テストでのテストデータのクリーンアップが不完全

**緩和策**:
- 各テストで独立したNeo4jデータベースを使用
- テスト後のクリーンアップを確実に実行（fixtureのfinalizerを使用）
- テストデータに一意のプレフィックスを付ける

**影響**: 中（データが残るとテストが失敗する）

### Risk 3: カバレッジ目標の達成困難

**リスク**: 一部のコード（エラーハンドリングなど）のカバレッジが困難

**緩和策**:
- 優先順位をつけて重要なコードから対応
- モックを活用してエラーケースをシミュレート
- 段階的に改善（完璧を求めない）

**影響**: 低（75%は達成可能な目標）

## Migration Plan

### Phase 1: Repository実装とユニットテスト（Week 1）

1. PersonRepositoryの実装完成
2. RelationshipRepositoryの実装完成
3. ユニットテスト（モック使用）の作成
4. **検証**: Repository層のカバレッジ80%以上

### Phase 2: 統合テストとNeo4jService（Week 2）

1. 統合テスト環境の構築
2. Repository統合テストの作成
3. Neo4jServiceの実装
4. Neo4jServiceのテスト
5. **検証**: Neo4j関連コードのカバレッジ80%以上

### Phase 3: CLI・Display・Validatorテスト（Week 3）

1. CLIコマンドテストの拡充
2. Displayテストの作成
3. HeirValidatorテストの拡充
4. **検証**: これらのモジュールのカバレッジ目標達成

### Phase 4: テストインフラとドキュメント（Week 4）

1. フィクスチャの整理
2. テストユーティリティの作成
3. ドキュメントの作成
4. **検証**: 全体カバレッジ75%以上

### Rollback Strategy

各Phaseは独立しているため、問題が発生した場合：

1. 該当Phaseのコミットをrevert
2. 既存のテストは影響を受けない（追加のみ）
3. カバレッジは前のPhaseの状態に戻る

**リスク**: 低（破壊的変更なし）

## Open Questions

1. **CI/CDでのNeo4j起動方法**
   - Docker Composeを使用？
   - GitHub ActionsのServicesを使用？
   - → 今回のスコープ外、Phase 2完了後に検討

2. **パフォーマンステストの必要性**
   - 大規模家系図（100人以上）でのパフォーマンス
   - → 現時点では不要、将来的に追加

3. **Agent層のテスト**
   - Ollama依存のため困難
   - → 今回のスコープ外、将来的にモック化を検討
