"""メインCLIのテスト"""
import pytest
from unittest.mock import Mock, patch

from src.cli.main import create_parser, main


class TestCreateParser:
    """create_parser関数のテスト"""

    def test_parser_creation(self):
        """パーサーの作成"""
        parser = create_parser()

        assert parser.prog == 'inheritance-calculator'
        assert parser.description == '日本の民法に基づく相続計算ツール'

    def test_parser_version_argument(self):
        """バージョン引数"""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])

    def test_parser_help_argument(self):
        """ヘルプ引数"""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])

    def test_parser_subcommands(self):
        """サブコマンドの存在確認"""
        parser = create_parser()

        # calculate サブコマンド
        args = parser.parse_args(['calculate'])
        assert args.command == 'calculate'
        assert hasattr(args, 'func')

        # calc エイリアス
        args = parser.parse_args(['calc'])
        assert args.command == 'calc'

        # validate サブコマンド
        args = parser.parse_args(['validate', 'test.json'])
        assert args.command == 'validate'
        assert hasattr(args, 'input_file')

        # demo サブコマンド
        args = parser.parse_args(['demo'])
        assert args.command == 'demo'

        # version サブコマンド
        args = parser.parse_args(['version'])
        assert args.command == 'version'

    def test_parser_calculate_options(self):
        """calculateコマンドのオプション"""
        parser = create_parser()

        # 入力ファイル指定
        args = parser.parse_args(['calculate', '-i', 'input.json'])
        assert str(args.input_file) == 'input.json'

        # 出力ファイル指定
        args = parser.parse_args(['calculate', '-o', 'output.json'])
        assert str(args.output) == 'output.json'

        # 両方指定
        args = parser.parse_args(['calculate', '-i', 'in.json', '-o', 'out.json'])
        assert str(args.input_file) == 'in.json'
        assert str(args.output) == 'out.json'

    def test_parser_demo_types(self):
        """demoコマンドのタイプ"""
        parser = create_parser()

        # basic
        args = parser.parse_args(['demo', 'basic'])
        assert args.type == 'basic'

        # complex
        args = parser.parse_args(['demo', 'complex'])
        assert args.type == 'complex'

        # interactive
        args = parser.parse_args(['demo', 'interactive'])
        assert args.type == 'interactive'

        # デフォルト（引数なし）
        args = parser.parse_args(['demo'])
        assert args.type == 'basic'


class TestMain:
    """main関数のテスト"""

    def test_main_no_arguments(self, capsys):
        """引数なしの実行"""
        result = main([])

        assert result == 0

        captured = capsys.readouterr()
        assert "相続計算機" in captured.out
        assert "usage:" in captured.out

    def test_main_help(self, capsys):
        """ヘルプ表示"""
        with pytest.raises(SystemExit):
            main(['--help'])

    def test_main_version(self, capsys):
        """バージョン表示"""
        with pytest.raises(SystemExit):
            main(['--version'])

    @patch('src.cli.commands.calculate_command')
    def test_main_calculate_command(self, mock_calculate):
        """calculateコマンドの実行"""
        mock_calculate.return_value = 0

        result = main(['calculate'])

        assert result == 0
        mock_calculate.assert_called_once()

    @patch('src.cli.commands.validate_command')
    def test_main_validate_command(self, mock_validate):
        """validateコマンドの実行"""
        mock_validate.return_value = 0

        result = main(['validate', 'test.json'])

        assert result == 0
        mock_validate.assert_called_once()

    @patch('src.cli.commands.demo_command')
    def test_main_demo_command(self, mock_demo):
        """demoコマンドの実行"""
        mock_demo.return_value = 0

        result = main(['demo', 'basic'])

        assert result == 0
        mock_demo.assert_called_once()

    @patch('src.cli.commands.version_command')
    def test_main_version_command(self, mock_version):
        """versionコマンドの実行"""
        mock_version.return_value = 0

        result = main(['version'])

        assert result == 0
        mock_version.assert_called_once()

    @patch('src.cli.commands.calculate_command')
    def test_main_command_error(self, mock_calculate):
        """コマンド実行時のエラー"""
        mock_calculate.side_effect = Exception("Test error")

        result = main(['calculate'])

        assert result == 1

    @patch('src.cli.commands.calculate_command')
    def test_main_keyboard_interrupt(self, mock_calculate, capsys):
        """キーボード割り込み"""
        mock_calculate.side_effect = KeyboardInterrupt()

        result = main(['calculate'])

        assert result == 130

        captured = capsys.readouterr()
        assert "中断" in captured.out
