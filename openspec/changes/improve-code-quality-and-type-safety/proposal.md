# コード品質と型安全性の改善提案

## Why

現在のコードベースには、将来的なバグの原因となる**技術的負債**が存在しています：

### 1. 型安全性の欠如（mypy: 21エラー）

**影響を受けるファイル**:
- `src/cli/display.py`: 10個の関数で戻り値型アノテーションが欠如
- `src/cli/session.py`: 初期化時の型不一致エラー
- `src/cli/ascii_tree.py`: `any`と`typing.Any`の誤記
- `src/cli/contact_input.py`: 戻り値型の欠如、Any型の不適切な使用
- `src/cli/commands.py`: Optional型の不適切な扱い（Null安全性の問題）

**問題の深刻度**:
- 🔴 **高**: 型エラーは実行時バグの温床となる
- 型チェックが機能せず、IDEの型推論・補完が不正確
- リファクタリング時の安全性が低下

### 2. コードスタイルの不統一（ruff: 多数の警告）

**主な問題**:
- **古い型構文の使用**: Python 3.12では非推奨の`List`, `Dict`, `Optional`を使用
  - 推奨: `list`, `dict`, `X | None`
- **未使用インポート**: `json`, `typing.List`, `typing.Optional`など
- **インポート順序**: ソートされていない、グループ化されていない
- **行長超過**: 88文字制限を超える行が多数存在

**影響**:
- コードの可読性・保守性の低下
- プロジェクト規約（PEP 8、pyproject.toml設定）との不一致
- 将来的な技術的負債の蓄積

### 3. 既存の改善提案との関係

**進行中の変更**:
- `improve-test-coverage-and-neo4j`: テストの信頼性向上には型安全性が前提
- `improve-cli-ui-experience`: 新機能追加の前に基盤を固めるべき

**優先順位の根拠**:
1. 技術的負債は利子がつく（放置するほど修正コストが増大）
2. 型安全なコードベースは開発速度を向上させる
3. 小規模で確実な改善から始めるべき

## What Changes

### 1. 型安全性の完全確保

#### display.py (10個の関数)
- `display_progress_context` → `-> Iterator[Progress]`
- `display_progress_bar` → `-> TaskID`
- `display_multi_step_progress` → `-> None`
- `display_file_progress` → `-> Iterator[TaskID]`
- `display_error`, `display_warning`, `display_info`, `display_success` → `-> None`
- `display_header` → `-> None`
- `display_completion` → `-> None`

#### session.py
- 初期化時の型不一致を修正
  ```python
  # Before
  self.data: dict[str, Any] = None  # ❌ 型エラー

  # After
  self.data: dict[str, Any] = {}  # ✅ 正しい初期化
  ```
- 関数の戻り値型アノテーションを追加

#### ascii_tree.py
- `any` → `Any` の修正
  ```python
  # Before
  def _has_descendant(...) -> any:  # ❌ 誤記

  # After
  def _has_descendant(...) -> Any:  # ✅ 正しい型
  ```

#### contact_input.py
- 戻り値型の追加
- Any型の削減（具体的な型への置き換え）

#### commands.py
- Null安全性の改善
  ```python
  # Before
  save_to_neo4j(
      decedent=decedent,  # ❌ Person | None
      spouses=spouses,    # ❌ list[Person] | None
      ...
  )

  # After
  if decedent and spouses is not None and children is not None:
      save_to_neo4j(
          decedent=decedent,  # ✅ Person
          spouses=spouses,    # ✅ list[Person]
          ...
      )
  ```

### 2. モダンなPython 3.12+型構文への更新

#### 全ファイル対象
- `List[X]` → `list[X]`
- `Dict[K, V]` → `dict[K, V]`
- `Optional[X]` → `X | None`
- `Union[X, Y]` → `X | Y`

**例**:
```python
# Before
from typing import List, Dict, Optional

def process(items: Optional[List[str]]) -> Dict[str, int]:
    ...

# After
def process(items: list[str] | None) -> dict[str, int]:
    ...
```

### 3. コードスタイルの統一

#### 未使用インポートの削除
- `json` (commands.py)
- `typing.List`, `typing.Optional` (ascii_tree.py)
- その他使用されていないインポート

#### インポート順序の修正
```python
# 標準ライブラリ
import sys
from pathlib import Path

# サードパーティ
from rich.console import Console

# ローカル
from src.cli.display import display_result
```

#### 行長制限の遵守
- 88文字を超える行を適切に分割
- 読みやすさを維持しながらフォーマット

### 4. ツール設定の強化

#### pyproject.toml
- mypy strict モードの段階的導入検討
- ruff の自動修正設定の活用

#### CI/CD統合
- GitHub Actions（または使用中のCI）での型チェック・リンター実行
- プルリクエスト時の自動検証

## Impact

### 影響を受けるスペック

**新規作成**:
- `code-quality`: コード品質基準、ツール設定、ベストプラクティス

**既存スペックへの影響**:
- `inheritance-calculation`: 影響なし（実装の品質改善のみ）

### 影響を受けるコード

**修正対象ファイル**:
- `src/cli/display.py` - 型アノテーション追加
- `src/cli/session.py` - 型エラー修正、アノテーション追加
- `src/cli/ascii_tree.py` - 型定義修正、古い型構文更新
- `src/cli/contact_input.py` - 型アノテーション追加、Any型削減
- `src/cli/commands.py` - Null安全性改善、古い型構文更新
- `src/cli/main.py` - インポート整理、型構文更新
- `src/cli/prompts.py` - 型構文更新
- `src/cli/report_generator.py` - 型構文更新
- `src/cli/family_tree_generator.py` - 型構文更新
- `src/cli/csv_parser.py` - 型構文更新

**テストファイル**:
- 型アノテーションの追加（必要に応じて）

### Breaking Changes

**なし** - 非破壊的変更のみ

この変更は以下の理由で既存機能に影響を与えません：
- 型アノテーションの追加は実行時動作に影響しない
- コードスタイルの修正は意味論的に等価
- 公開APIの変更なし

### Migration Path

**不要** - 既存コードへの影響なし

### Risks

**低リスク**:
- ✅ 非破壊的変更（実行時動作の変更なし）
- ✅ 段階的な修正が可能
- ✅ 既存テストで検証可能

**潜在的な注意点**:
- 型エラー修正時に、隠れていたバグが発見される可能性（これは良いこと）
- CI/CD設定の更新が必要な場合がある

### Benefits

**即時の効果**:
- ✅ **mypy 21エラー → 0エラー**: 型安全性の完全確保
- ✅ **ruff警告の大幅削減**: コードスタイルの統一
- ✅ **IDEサポートの向上**: 正確な型推論・補完

**中長期的な効果**:
- ✅ **バグの早期発見**: 実行前に型エラーを検出
- ✅ **開発効率向上**: リファクタリングが安全かつ迅速に
- ✅ **保守性向上**: コードの意図が明確で理解しやすい
- ✅ **技術的負債の解消**: 将来的な修正コストの削減

**測定可能な指標**:
- mypy成功率: 0% → 100%
- ruff警告数: 多数 → 0または最小限
- コード品質スコアの向上

## Timeline

**推定作業時間**: 4-6時間

**フェーズ1**: 型安全性の確保（2-3時間）
- display.py, session.py, ascii_tree.py, contact_input.py, commands.py

**フェーズ2**: コードスタイルの統一（1-2時間）
- 全ファイルの型構文更新、インポート整理

**フェーズ3**: 検証と最終調整（1時間）
- mypy, ruff, pytest実行
- CI/CD設定の更新
