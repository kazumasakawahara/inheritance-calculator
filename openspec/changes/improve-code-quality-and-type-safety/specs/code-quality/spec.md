# code-quality Specification

## Purpose

プロジェクト全体のコード品質基準を定義し、型安全性、コードスタイル、保守性の標準を確立する。

## ADDED Requirements

### Requirement: 型安全性の保証

すべてのPythonコードSHALL pass mypy type checking. 関数の引数と戻り値にはtype annotationを必須とし、型の安全性を保証しなければならない。

#### Scenario: 関数定義時の型アノテーション

- **GIVEN** 新しい関数を定義する
- **WHEN** 関数が引数または戻り値を持つ
- **THEN** すべての引数と戻り値に型アノテーションを付与しなければならない
- **AND** `mypy --strict` モードで型チェックに合格しなければならない

**例**:
```python
# ❌ 不合格
def process_data(items):
    return len(items)

# ✅ 合格
def process_data(items: list[str]) -> int:
    return len(items)
```

#### Scenario: Optional型の適切な処理

- **GIVEN** 関数がNoneを返す可能性がある、またはNone引数を受け入れる
- **WHEN** その変数を使用する
- **THEN** Noneチェックを実施してから使用しなければならない
- **AND** 型ガードまたは`assert`文で型を保証しなければならない

**例**:
```python
# ❌ 不合格
def save(data: Person | None):
    repository.save(data)  # 型エラー

# ✅ 合格
def save(data: Person | None):
    if data is not None:
        repository.save(data)  # 型安全
```

#### Scenario: Any型の最小化

- **GIVEN** 型を定義する必要がある
- **WHEN** 具体的な型が判明している
- **THEN** `Any` 型の使用を避け、具体的な型を指定しなければならない
- **AND** `Any` 型の使用は、真に型が不明な場合のみに限定する

**例**:
```python
# ❌ 不合格
def get_config() -> Any:
    return {"key": "value"}

# ✅ 合格
def get_config() -> dict[str, str]:
    return {"key": "value"}
```

---

### Requirement: Python 3.12+モダン型構文の使用

プロジェクトSHALL use Python 3.12+ modern type syntax. `typing`モジュールからの古い型構文（`List`, `Dict`, `Optional`など）は使用してはならない。

#### Scenario: リスト・辞書型の定義

- **GIVEN** リストまたは辞書の型を定義する
- **WHEN** 型アノテーションを記述する
- **THEN** `list[X]` または `dict[K, V]` を使用しなければならない
- **AND** `typing.List` や `typing.Dict` を使用してはならない

**例**:
```python
# ❌ 不合格
from typing import List, Dict

def process(items: List[str]) -> Dict[str, int]:
    ...

# ✅ 合格
def process(items: list[str]) -> dict[str, int]:
    ...
```

#### Scenario: Optional型の定義

- **GIVEN** Noneを含む可能性のある型を定義する
- **WHEN** 型アノテーションを記述する
- **THEN** `X | None` 構文を使用しなければならない
- **AND** `typing.Optional[X]` を使用してはならない

**例**:
```python
# ❌ 不合格
from typing import Optional

def find_user(id: int) -> Optional[User]:
    ...

# ✅ 合格
def find_user(id: int) -> User | None:
    ...
```

#### Scenario: Union型の定義

- **GIVEN** 複数の型のいずれかを取る変数を定義する
- **WHEN** 型アノテーションを記述する
- **THEN** `X | Y` 構文を使用しなければならない
- **AND** `typing.Union[X, Y]` を使用してはならない

**例**:
```python
# ❌ 不合格
from typing import Union

def handle(value: Union[str, int]) -> None:
    ...

# ✅ 合格
def handle(value: str | int) -> None:
    ...
```

---

### Requirement: コードスタイルの統一

すべてのコードSHALL pass ruff linting and format checks. プロジェクト全体で一貫したコードスタイルを維持しなければならない。

#### Scenario: インポート順序の標準化

- **GIVEN** Pythonファイルにインポート文を記述する
- **WHEN** 複数のモジュールをインポートする
- **THEN** 以下の順序でグループ化し、各グループ内でアルファベット順にソートしなければならない:
  1. 標準ライブラリ
  2. サードパーティライブラリ
  3. ローカルモジュール
- **AND** 各グループ間には空行を1行挿入しなければならない

**例**:
```python
# ❌ 不合格
from src.cli.display import display_result
from rich.console import Console
import sys

# ✅ 合格
import sys
from pathlib import Path

from rich.console import Console

from src.cli.display import display_result
```

#### Scenario: 未使用インポートの禁止

- **GIVEN** Pythonファイルにインポート文が存在する
- **WHEN** ruffでチェックを実行する
- **THEN** 使用されていないインポートが存在してはならない
- **AND** F401エラーが発生してはならない

#### Scenario: 行長制限の遵守

- **GIVEN** Pythonコードを記述する
- **WHEN** 1行のコードを記述する
- **THEN** 行の長さは88文字以内に収めなければならない
- **AND** やむを得ず超える場合は、適切に改行して可読性を維持しなければならない

---

### Requirement: 継続的な品質検証

プロジェクトSHALL enforce code quality checks before commits and in CI/CD pipelines. すべてのコード変更は品質基準を満たさなければマージを許可してはならない。

#### Scenario: ローカル開発時の品質チェック

- **GIVEN** コードの変更を行った
- **WHEN** コミット前に品質チェックを実行する
- **THEN** 以下のコマンドがすべて成功しなければならない:
  - `uv run mypy src/` （型チェック）
  - `uv run ruff check src/` （リンター）
  - `uv run pytest` （テスト）

#### Scenario: CI/CDパイプラインでの品質検証

- **GIVEN** プルリクエストまたはマージリクエストを作成する
- **WHEN** CI/CDパイプラインが実行される
- **THEN** 型チェック、リンター、テストがすべて通過しなければならない
- **AND** いずれかが失敗した場合、マージを許可してはならない

#### Scenario: テストカバレッジの維持

- **GIVEN** コードの変更を行った
- **WHEN** テストカバレッジを測定する
- **THEN** 全体のカバレッジは68%以上を維持しなければならない
- **AND** 新規追加コードのカバレッジは75%以上を目指すべきである

---

### Requirement: ドキュメント化とベストプラクティス

プロジェクトSHALL document code quality standards and tool usage. 開発者ガイドには型アノテーション、リンター、テストに関するベストプラクティスを含めなければならない。

#### Scenario: 開発環境のセットアップドキュメント

- **GIVEN** 新しい開発者がプロジェクトに参加する
- **WHEN** README.mdまたは開発者ガイドを参照する
- **THEN** 以下の情報が記載されていなければならない:
  - 必要なツールのインストール方法（mypy, ruff）
  - 品質チェックの実行方法
  - 型アノテーションのベストプラクティス
  - プロジェクト固有の規約

#### Scenario: エディタ/IDE設定の推奨

- **GIVEN** 開発環境を構成する
- **WHEN** エディタまたはIDEを設定する
- **THEN** 以下の機能を有効化することを推奨する:
  - 型チェック（mypy統合）
  - リンター（ruff統合）
  - 保存時の自動フォーマット
  - インポートの自動ソート
