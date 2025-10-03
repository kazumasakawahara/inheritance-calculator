"""メインCLI

相続計算機のコマンドラインインターフェース
"""
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Protocol

from src.cli import commands
from src.cli.display import display_header, display_error


class CommandFunc(Protocol):
    """コマンド関数の型定義"""
    def __call__(self, args: argparse.Namespace) -> int: ...


def create_parser() -> argparse.ArgumentParser:
    """コマンドラインパーサーを作成

    Returns:
        ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog='inheritance-calculator',
        description='日本の民法に基づく相続計算ツール',
        epilog='詳細は https://github.com/your-repo/inheritance-calculator を参照'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    # サブコマンド
    subparsers = parser.add_subparsers(
        title='サブコマンド',
        description='利用可能なコマンド',
        dest='command',
        help='実行するコマンドを選択'
    )

    # calculate コマンド
    calculate_parser = subparsers.add_parser(
        'calculate',
        aliases=['calc'],
        help='相続計算を実行'
    )
    calculate_parser.add_argument(
        '-i', '--input',
        dest='input_file',
        type=Path,
        help='入力JSONファイルのパス'
    )
    calculate_parser.add_argument(
        '-o', '--output',
        dest='output',
        type=Path,
        help='出力ファイルのパス'
    )
    calculate_parser.set_defaults(func=commands.calculate_command)

    # validate コマンド
    validate_parser = subparsers.add_parser(
        'validate',
        help='入力ファイルを検証'
    )
    validate_parser.add_argument(
        'input_file',
        type=Path,
        help='検証する入力JSONファイルのパス'
    )
    validate_parser.set_defaults(func=commands.validate_command)

    # demo コマンド
    demo_parser = subparsers.add_parser(
        'demo',
        help='デモを実行'
    )
    demo_parser.add_argument(
        'type',
        choices=['basic', 'complex', 'interactive'],
        default='basic',
        nargs='?',
        help='デモのタイプ (basic: 基本ケース, complex: 複雑ケース, interactive: 対話型)'
    )
    demo_parser.set_defaults(func=commands.demo_command)

    # template コマンド
    template_parser = subparsers.add_parser(
        'template',
        help='テンプレートファイルを作成'
    )
    template_parser.add_argument(
        'output_file',
        type=Path,
        help='出力するテンプレートファイルのパス（.csv）'
    )
    template_parser.set_defaults(func=commands.template_command)

    # tree コマンド
    tree_parser = subparsers.add_parser(
        'tree',
        help='家系図を生成'
    )
    tree_parser.add_argument(
        '-i', '--input',
        dest='input_file',
        type=Path,
        required=True,
        help='入力ファイルのパス（JSON or CSV）'
    )
    tree_parser.add_argument(
        '-o', '--output',
        dest='output_file',
        type=Path,
        required=True,
        help='出力ファイルのパス（.txt, .mmd, .png, .pdf, .svg）'
    )
    tree_parser.set_defaults(func=commands.tree_command)

    # interview コマンド
    interview_parser = subparsers.add_parser(
        'interview',
        help='AI対話型インタビューで相続情報を収集'
    )
    interview_parser.add_argument(
        '-o', '--output',
        dest='output',
        type=Path,
        help='計算結果の出力ファイルパス（.json, .md, .pdf）'
    )
    interview_parser.set_defaults(func=commands.interview_command)

    # version コマンド
    version_parser = subparsers.add_parser(
        'version',
        help='バージョン情報を表示'
    )
    version_parser.set_defaults(func=commands.version_command)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """メイン関数

    Args:
        argv: コマンドライン引数（テスト用）

    Returns:
        終了コード
    """
    parser = create_parser()

    # 引数のパース
    if argv is None:
        argv = sys.argv[1:]

    # 引数がない場合はヘルプを表示
    if not argv:
        display_header(
            "相続計算機 (Inheritance Calculator)",
            "日本の民法に基づく相続計算ツール"
        )
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    # サブコマンドが指定されていない場合
    if not hasattr(args, 'func'):
        display_error("サブコマンドを指定してください")
        parser.print_help()
        return 1

    # サブコマンドを実行
    try:
        func: CommandFunc = args.func
        return func(args)
    except KeyboardInterrupt:
        print("\n[yellow]処理を中断しました。[/yellow]")
        return 130
    except Exception as e:
        display_error(f"予期しないエラーが発生しました: {str(e)}")
        return 1


def cli_entry_point() -> None:
    """CLIエントリーポイント（パッケージインストール用）"""
    sys.exit(main())


if __name__ == '__main__':
    sys.exit(main())
