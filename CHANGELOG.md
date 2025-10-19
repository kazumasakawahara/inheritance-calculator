# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-19

### Changed
- **依存関係の更新**: `inheritance-calculator-core` v0.9.0に対応
  - GitHubリポジトリからの直接インストールからPyPI版へ移行
  - `inheritance-calculator-core[agents]==0.9.0`を使用
- **型安全性の向上**: PersonID値オブジェクトへの対応
  - `sibling_blood_types`の型を`dict[str, BloodType]`から`dict[PersonID, BloodType]`に変更
  - すべての型チェック(mypy --strict)をパス

### Fixed
- CSV解析での兄弟姉妹の血縁タイプ処理をPersonID対応に修正
- JSONファイル解析での血縁タイプ辞書の型を修正
- テストコードでのPersonID使用に統一

### Technical Details
- 修正ファイル:
  - `src/cli/commands.py`: PersonIDインポートと型定義の更新
  - `src/cli/csv_parser.py`: 戻り値の型とPersonID処理の修正
  - `tests/test_cli/test_csv_parser.py`: テストでのPersonID使用
- テスト結果: 199 passed, 3 skipped
- カバレッジ: 67%

## [1.0.0] - 2025-10-03

### Added
- Neo4jグラフデータベース統合
- 相続ケースのグラフ構造での永続化
- Cypherクエリによる高度な相続人検索
- `--save-to-neo4j` オプションでCLIから直接保存可能
- AI対話型インタビュー機能 (Ollama統合)
- CSV/JSON入出力対応
- PDF/Markdown形式のレポート生成
- 家系図の可視化 (テキスト/Mermaid/Graphviz)

### Features
- 日本の民法に完全準拠した相続計算
- 代襲相続、再転相続、相続放棄、半血兄弟姉妹の処理
- 対話型CLI、ファイル入力、デモモード
- 豊富なテストスイート (131件のテスト)

---

[1.1.0]: https://github.com/kazumasakawahara/inheritance-calculator/releases/tag/v1.1.0
[1.0.0]: https://github.com/kazumasakawahara/inheritance-calculator/releases/tag/v1.0.0
