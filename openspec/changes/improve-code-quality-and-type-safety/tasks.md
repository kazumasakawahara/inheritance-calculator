# Tasks for improve-code-quality-and-type-safety

## Phase 1: 型安全性の確保

### Task 1: display.py の型アノテーション追加
- [ ] `display_progress_context` に戻り値型 `-> Iterator[Progress]` を追加
- [ ] `display_progress_bar` に戻り値型 `-> TaskID` を追加
- [ ] `display_multi_step_progress` に戻り値型 `-> None` を追加
- [ ] `display_file_progress` に戻り値型 `-> Iterator[TaskID]` を追加
- [ ] `display_error`, `display_warning`, `display_info`, `display_success` に戻り値型 `-> None` を追加
- [ ] `display_header` に戻り値型 `-> None` を追加
- [ ] `display_completion` に戻り値型 `-> None` を追加
- [ ] mypyで検証（display.pyのエラーが0になることを確認）

**検証コマンド**: `uv run mypy src/cli/display.py`

---

### Task 2: session.py の型エラー修正
- [ ] 初期化時の型不一致を修正（`None` → `{}`）
  - `self.data: dict[str, Any] = {}`
  - `self.contacts: dict[str, str] = {}`
- [ ] 関数の戻り値型アノテーションを追加
- [ ] mypyで検証（session.pyのエラーが0になることを確認）

**検証コマンド**: `uv run mypy src/cli/session.py`

---

### Task 3: ascii_tree.py の型定義修正
- [ ] `any` → `Any` の誤記を修正
  - `from typing import Any` をインポート
  - 該当箇所の型を修正
- [ ] mypyで検証（ascii_tree.pyのエラーが0になることを確認）

**検証コマンド**: `uv run mypy src/cli/ascii_tree.py`

---

### Task 4: contact_input.py の型アノテーション追加
- [ ] 関数の戻り値型アノテーションを追加
- [ ] Any型を具体的な型に置き換え
  - 戻り値が `Any` の箇所を `str | None` などに修正
- [ ] mypyで検証（contact_input.pyのエラーが0になることを確認）

**検証コマンド**: `uv run mypy src/cli/contact_input.py`

---

### Task 5: commands.py のNull安全性改善
- [ ] `save_to_neo4j` 呼び出し前のNullチェックを追加
  - 既存の `if` 条件を強化
  - Optional型の変数を適切に扱う
- [ ] mypyで検証（commands.pyのエラーが0になることを確認）

**検証コマンド**: `uv run mypy src/cli/commands.py`

---

### Task 6: 全体の型チェック検証
- [ ] 全ファイルでmypyを実行
- [ ] 21エラー → 0エラーを確認
- [ ] 既存テストが通ることを確認

**検証コマンド**:
```bash
uv run mypy src/
uv run pytest
```

---

## Phase 2: モダンなPython 3.12+型構文への更新

### Task 7: 古い型構文の一括更新（全ファイル）
- [ ] `List[X]` → `list[X]` の置換
- [ ] `Dict[K, V]` → `dict[K, V]` の置換
- [ ] `Optional[X]` → `X | None` の置換
- [ ] `Union[X, Y]` → `X | Y` の置換
- [ ] 不要になった `from typing import List, Dict, Optional, Union` を削除

**対象ファイル**:
- [ ] src/cli/ascii_tree.py
- [ ] src/cli/commands.py
- [ ] src/cli/main.py
- [ ] src/cli/prompts.py
- [ ] src/cli/report_generator.py
- [ ] src/cli/family_tree_generator.py
- [ ] src/cli/csv_parser.py
- [ ] src/cli/contact_input.py
- [ ] src/cli/session.py

**検証コマンド**: `rg "List\[|Dict\[|Optional\[|Union\[" src/cli/`（結果が0件であることを確認）

---

## Phase 3: コードスタイルの統一

### Task 8: 未使用インポートの削除
- [ ] commands.py から `json` を削除
- [ ] ascii_tree.py から `List`, `Optional` を削除
- [ ] その他の未使用インポートを削除
- [ ] ruffで検証（F401エラーが0になることを確認）

**検証コマンド**: `uv run ruff check src/ --select F401`

---

### Task 9: インポート順序の修正（全ファイル）
- [ ] 標準ライブラリ → サードパーティ → ローカル の順序に整理
- [ ] ruffの自動修正機能を活用: `uv run ruff check --fix src/ --select I001`
- [ ] 手動で調整が必要な箇所を修正

**対象ファイル**:
- [ ] src/cli/__init__.py
- [ ] src/cli/ascii_tree.py
- [ ] src/cli/commands.py
- [ ] その他I001エラーがあるファイル

**検証コマンド**: `uv run ruff check src/ --select I001`

---

### Task 10: 行長制限の遵守
- [ ] 88文字を超える行を適切に分割
- [ ] 可読性を維持しながらフォーマット
- [ ] blackまたは手動で調整

**検証コマンド**: `uv run ruff check src/ --select E501`

---

## Phase 4: 検証と最終調整

### Task 11: 全体の品質チェック
- [ ] mypy実行: `uv run mypy src/`（エラー0を確認）
- [ ] ruff実行: `uv run ruff check src/`（重要な警告がないことを確認）
- [ ] pytest実行: `uv run pytest`（全テスト通過を確認）
- [ ] カバレッジ確認: `uv run pytest --cov=src`（68%以上を維持）

**成功基準**:
- ✅ mypy: 0 errors
- ✅ ruff: 重大な警告なし（E501など軽微なものは許容）
- ✅ pytest: 全テスト通過
- ✅ カバレッジ: 68%以上

---

### Task 12: CI/CD設定の更新（オプション）
- [ ] GitHub Actionsワークフローを確認
- [ ] mypyとruffのチェックがCI/CDに含まれているか確認
- [ ] 必要に応じて追加・更新

**該当ファイル**: `.github/workflows/*.yml`

---

### Task 13: ドキュメント更新
- [ ] README.md に型チェック・リンターの実行方法を追加
- [ ] 開発者ガイドに品質基準を明記
- [ ] コントリビューションガイドを更新（必要に応じて）

**検証**: ドキュメントが正確で分かりやすいことを確認

---

## 完了基準

すべてのタスクが完了し、以下の条件を満たすこと：

✅ **型安全性**: mypy実行時にエラー0
✅ **コードスタイル**: ruff実行時に重大な警告なし
✅ **テスト**: 全テスト通過、カバレッジ68%以上維持
✅ **ドキュメント**: 開発者向けドキュメントが更新されている

## 推定作業時間

- **Phase 1**: 2-3時間（型安全性の確保）
- **Phase 2**: 1-2時間（型構文の更新）
- **Phase 3**: 1時間（コードスタイルの統一）
- **Phase 4**: 1時間（検証と最終調整）

**合計**: 4-6時間
