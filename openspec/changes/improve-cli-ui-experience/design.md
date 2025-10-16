# Design Document: CLI User Experience Improvements

## Context

現在の相続計算機CLIは機能的には完全ですが、実務家（司法書士、弁護士）の日常使用において以下の課題が顕在化しています:

1. **長時間処理の不安**: Neo4j保存やPDF生成時に進捗が見えず、フリーズしたように見える
2. **入力エラー時の非効率性**: 1つの入力ミスで全て再入力が必要
3. **視覚的理解の困難性**: 複雑な家系関係をテキストテーブルのみで理解するのは難しい
4. **中断不可能性**: 途中で作業を中断できず、まとまった時間が必要
5. **実務フローとの不一致**: 相続放棄など後日判明する情報を「保留」できず、最初から全情報が必要
6. **連絡先管理の不在**: 確定した相続人の連絡先（住所、電話、メール）を記録・管理できない

特に5, 6は実務において深刻な問題です。相続調査は段階的に情報が明らかになるプロセスであり、また確定後の相続人への連絡は実務の重要な一部です。

これらの改善により、実務効率の向上と利用者満足度の向上を目指します。

**Stakeholders**:
- 司法書士、弁護士（エンドユーザー）
- 開発チーム（保守性）

**Constraints**:
- Rich library依存（既存依存のため追加コストなし）
- 既存CLI APIの互換性維持（破壊的変更なし）
- Python 3.12+のみサポート

## Goals / Non-Goals

### Goals
1. 長時間処理（>2秒）に対する進捗フィードバックの提供
2. インタラクティブモードでの入力ミス修正の簡易化
3. 計算結果の視覚的理解の向上
4. セッションの中断・再開機能の提供
5. エラーメッセージの改善（何が問題で、どう直すか）
6. **保留（ペンディング）機能**: 未確定情報を保留し、後日更新可能
7. **連絡先情報の管理**: 相続人の住所・電話・メールアドレスの入力・保存・出力

### Non-Goals
1. Web UIの実装（Phase 7以降の課題）
2. GUIアプリケーション化
3. 既存コマンドの破壊的変更
4. 英語ローカライゼーション（将来の課題）
5. プラグインシステム（オーバーエンジニアリング）
6. 連絡先情報の高度な管理（住所録機能、一括インポートなど）は対象外

## Decisions

### Decision 1: Rich Libraryの全面活用
**What**: すべての表示機能をRich libraryベースで統一

**Why**:
- 既に依存関係に含まれている（追加コストなし）
- Progress, Panel, Table, Tree, Promptなど必要な機能が全て揃っている
- メンテナンスが活発で安定している
- ドキュメントが充実している

**Alternatives considered**:
- Click library: Rich ほど表示機能が豊富ではない
- curses: 低レベル過ぎて開発コストが高い
- questionary: Richと組み合わせると冗長

### Decision 2: セッションストレージは一時ファイルベース
**What**: `~/.inheritance-calculator/sessions/` にJSON形式で保存

**Why**:
- シンプルで実装が容易
- ファイルシステムベースのため外部依存なし
- デバッグが容易（ファイルを直接確認可能）
- 軽量（通常のセッションデータは10KB未満）

**Alternatives considered**:
- SQLite: オーバーエンジニアリング、クエリ不要
- Redis: 外部依存が増える、ローカルツールには過剰
- メモリ内のみ: プロセス終了で失われるため中断・再開不可

**Implementation**:
```python
# セッションディレクトリ
SESSION_DIR = Path.home() / ".inheritance-calculator" / "sessions"

# セッションID: タイムスタンプベース
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# セッションファイル
session_file = SESSION_DIR / f"{session_id}.json"
```

### Decision 3: プログレス表示の粒度基準
**What**: 処理時間が2秒以上かかる可能性がある操作に対してプログレス表示を追加

**Why**:
- 2秒未満: 体感的に瞬間的な処理と感じられる
- 2秒以上: ユーザーが「遅い」と感じ始める閾値
- Nielsen Norman Groupのユーザビリティ研究に基づく

**Affected operations**:
- Neo4j保存: 5-10秒（多数のノード・リレーションシップ作成）
- PDF生成: 3-8秒（レイアウト計算、レンダリング）
- 大規模CSV読み込み: 2-5秒（100行以上）

### Decision 4: ASCIIアート家系図の制約
**What**: 3世代まで、横幅80文字以内に収める

**Why**:
- 標準ターミナル幅は80文字
- 4世代以上は視認性が低下
- ほとんどの相続ケースは3世代以内
- 複雑なケースはGraphviz出力を推奨

**Fallback**:
- 4世代以上またはwidth > 80の場合: 警告を表示し、Graphviz出力を推奨

### Decision 5: 入力確認画面のUI設計
**What**: Rich Tableによる一覧表示 + 番号選択による修正

**Why**:
- 一覧性が高い（全入力を一度に確認可能）
- 直感的（修正したい項目の番号を入力するだけ）
- Richのテーブル表示が見やすい

**Alternative considered**:
- TUI形式（カーソル移動で選択）: 実装複雑度高、Rich単体では困難
- 全項目を順番に確認: 時間がかかる、非効率

**UI Flow**:
```
入力完了後:

┌─────────────────────────────────────────┐
│ 入力内容確認                            │
├────┬──────────────┬─────────────────────┤
│ No │ 項目         │ 入力値               │
├────┼──────────────┼─────────────────────┤
│ 1  │ 被相続人氏名 │ 山田太郎            │
│ 2  │ 死亡日       │ 2025-06-15          │
│ 3  │ 配偶者       │ 山田花子 (存命)     │
│ 4  │ 子           │ 山田一郎, 山田二郎  │
└────┴──────────────┴─────────────────────┘

修正する項目の番号を入力してください (Enterで確定): _
```

## Risks / Trade-offs

### Risk 1: プログレス表示によるパフォーマンスオーバーヘッド
**Risk**: プログレス更新処理自体がパフォーマンスに影響

**Mitigation**:
- プログレス更新は適切な間隔で実行（毎イテレーションではなく、100ms毎など）
- バッチ処理での更新頻度を制限
- 必要に応じてプログレス表示をオフにするオプション提供（`--no-progress`）

**Acceptance criteria**:
- プログレス表示によるオーバーヘッドは総処理時間の5%未満

### Risk 2: セッション一時ファイルの肥大化
**Risk**: セッションファイルが蓄積してディスク容量を圧迫

**Mitigation**:
- 古いセッションファイルの自動削除（30日以上経過）
- セッション一覧表示時に合計サイズを表示
- `--clean-sessions` コマンドで手動削除可能

**Monitoring**:
- 起動時に `SESSION_DIR` のサイズをチェック
- 100MB超過時に警告表示

### Risk 3: ASCIIアート表示の複雑なケースでの視認性低下
**Risk**: 複雑な家系構造でASCIIアートが見にくい

**Mitigation**:
- 3世代、横幅80文字を超える場合は警告表示
- 自動的にGraphviz形式へのフォールバック提案
- `--ascii-tree-max-depth` オプションで制限を設定可能

**User communication**:
```
⚠️ 家系図が複雑なため、ASCIIアート表示が見にくい可能性があります
   より詳細な表示には以下をお試しください:
   $ inheritance-calculator tree -i input.json -o tree.png
```

## Migration Plan

**Phase 1: プログレス表示とプロンプト改善**
1. `src/cli/display.py` にプログレス関連関数を追加
2. `src/cli/commands.py` の長時間処理にプログレス追加
3. `examples/demo_interactive.py` のプロンプト改善

**Phase 2: 視覚化機能**
1. ASCIIアート家系図ジェネレーターの実装
2. `display_result()` の拡張（視覚的な割合表示）
3. サマリーパネルの強調表示

**Phase 3: セッション管理**
1. セッションストレージの実装
2. `resume` コマンドの追加
3. 中断時の保存プロンプト

**Phase 4: エラー改善とヘルプ**
1. エラーメッセージの改善
2. インラインヘルプの実装
3. ドキュメント更新

**Rollback strategy**:
- 各機能はフィーチャーフラグで有効化/無効化可能
- 既存機能への影響なし（追加のみ）
- 問題発生時は該当フィーチャーフラグをオフに

### Decision 6: 保留（ペンディング）項目の管理方法
**What**: セッションデータに `pending_items` フィールドを追加し、キー:値形式で保留項目を管理

**Why**:
- シンプルな辞書型で管理が容易
- セッション再開時に保留項目を容易に特定可能
- 柔軟性が高い（任意の項目を保留可能）

**Implementation**:
```python
session_data = {
    "decedent": {...},
    "spouses": [...],
    "pending_items": {
        "renounced": "未確定",  # 相続放棄者が未確定
        "disqualified": "未確定",  # 相続欠格者が未確定
        # その他の保留項目
    },
    ...
}
```

**User Experience**:
- 入力時に `pending`, `保留`, `未確定` と入力すると保留マーク
- 確認画面で黄色ハイライト表示
- セッション再開時に保留項目の更新を促す

### Decision 7: Person モデルへの連絡先フィールド追加方式
**What**: Optional フィールドとして `address`, `phone`, `email` を追加（Pydantic）

**Why**:
- 後方互換性維持（既存データは None で動作）
- Pydantic の Optional により、フィールドなしでも動作
- Neo4j のプロパティも同様に Optional（null 許可）

**Alternatives considered**:
- 別モデル（ContactInfo）を作成: オーバーエンジニアリング、シンプルさを損なう
- 埋め込み辞書（extra_data）: 型安全性が低下、バリデーション困難

**Migration**:
```python
class Person(BaseModel):
    name: str
    is_alive: bool = True
    # ... 既存フィールド ...

    # 新規フィールド（Optional）
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None  # Pydanticのメールバリデーション
```

**Neo4j Schema**:
```cypher
// 既存のPersonノードにプロパティを追加（既存データに影響なし）
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS NOT NULL;

// 新規プロパティはOptional（制約なし）
// address, phone, email プロパティは自動的にnull許可
```

## Open Questions

1. **Q**: セッション暗号化は必要か？
   - **A**: 連絡先情報追加により、よりセンシティブなデータを扱うため、将来的には暗号化を検討。Phase 1ではファイルパーミッション（0600）で対応。

2. **Q**: プログレス表示のスタイル統一基準は？
   - **A**: Rich の `Progress` を使用。すべて同じスタイル（緑色バー、パーセンテージ、経過時間）に統一。

3. **Q**: 家系図の最大表示人数制限は？
   - **A**: 実装後にユーザビリティテストで決定。暫定的に15人まで。

4. **Q**: カラースキームのカスタマイズ機能は必要か？
   - **A**: Phase 1ではデフォルトのみ。需要があればPhase 2以降で環境変数による設定を検討。

5. **Q**: 連絡先情報の個人情報保護は？
   - **A**: ローカル実行のため外部送信なし。セッションファイルのパーミッション制御（0600）で保護。GDPR対応は将来の課題。

6. **Q**: 電話番号のバリデーションレベルは？
   - **A**: 柔軟性を重視し、厳密なバリデーションは行わない。国際番号や様々な形式に対応。

## Performance Targets

| Operation | Current | Target | Measurement |
|-----------|---------|--------|-------------|
| プログレス表示オーバーヘッド | N/A | <5% | 処理時間の増加率 |
| セッション保存時間 | N/A | <500ms | save_session() 実行時間 |
| ASCIIアート生成時間 | N/A | <100ms | generate_ascii_tree() 実行時間 |
| 確認画面表示時間 | N/A | <50ms | display_confirmation() 実行時間 |

## Security Considerations

1. **セッションファイルのパーミッション**: 0600 (owner read/write only)
2. **一時ファイルの安全な削除**: `os.remove()` 使用、`shutil.rmtree()` は使わない
3. **パス traversal 対策**: セッションIDは `[a-zA-Z0-9_-]` のみ許可、`../` などを拒否
4. **入力値のサニタイズ**: ユーザー入力を表示前にエスケープ（Rich markup injection 対策）

## Testing Strategy

### Unit Tests
- プログレス表示関数（モック使用）
- ASCIIアート生成ロジック
- セッション保存・読み込み
- 入力バリデーション

### Integration Tests
- 各コマンドでのプログレス表示
- 対話型モードでの確認・修正フロー
- セッション中断・再開

### Manual Tests
- 実際のターミナルでの視覚確認
- 異なるターミナルサイズでの表示テスト
- カラーモード（標準、colorblind、no-color）テスト

### Performance Tests
- 100行CSVファイルの処理時間
- 100ノードのNeo4j保存時間
- プログレス表示のオーバーヘッド測定

## Success Metrics

**User Experience**:
- 入力ミス修正時間: 50%削減（再入力不要）
- 処理待ち時間の不安: ユーザーフィードバックで測定
- 結果理解時間: 30%短縮（視覚化による）

**Code Quality**:
- テストカバレッジ: 85%以上維持
- 既存機能の後方互換性: 100%維持
- 新規バグ: 実装後1ヶ月で5件以下

**Documentation**:
- ユーザーガイド更新: 新機能すべてカバー
- スクリーンショット/GIF: 各主要機能に対して1つ以上
