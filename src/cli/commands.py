"""CLIコマンド定義

各サブコマンドの実装を提供します。
"""
import sys
from pathlib import Path
from typing import Optional, Any
from argparse import Namespace
from rich.console import Console

from src.cli.display import display_result, display_error, display_info
from src.cli.csv_parser import CSVParser
from src.cli.report_generator import ReportGenerator
from src.cli.family_tree_generator import FamilyTreeGenerator
from src.services.inheritance_calculator import InheritanceCalculator

console = Console()


def calculate_command(args: Namespace) -> int:
    """相続計算コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード（0: 成功、1以上: エラー）
    """
    try:
        if args.input_file:
            # ファイル拡張子で形式を判定
            file_ext = args.input_file.suffix.lower()
            if file_ext == '.csv':
                return calculate_from_csv(args.input_file, args.output)
            elif file_ext == '.json':
                return calculate_from_file(args.input_file, args.output)
            else:
                display_error(f"サポートされていないファイル形式です: {file_ext}")
                display_info("対応形式: .json, .csv")
                return 1
        else:
            # 対話モード
            return calculate_interactive()
    except Exception as e:
        display_error(f"計算エラー: {str(e)}")
        return 1


def calculate_from_file(input_file: Path, output_file: Optional[Path] = None) -> int:
    """ファイルから相続計算を実行

    Args:
        input_file: 入力JSONファイルパス
        output_file: 出力ファイルパス（オプション）

    Returns:
        終了コード
    """
    import json
    from datetime import date
    from src.models.person import Person
    from src.models.relationship import BloodType

    try:
        # JSONファイルを読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 被相続人の作成
        decedent_data = data['decedent']
        decedent = Person(
            name=decedent_data['name'],
            is_decedent=True,
            is_alive=False,
            birth_date=date.fromisoformat(decedent_data.get('birth_date')) if decedent_data.get('birth_date') else None,
            death_date=date.fromisoformat(decedent_data['death_date'])
        )

        # 相続人候補の作成
        spouses = []
        for spouse_data in data.get('spouses', []):
            spouse = Person(
                name=spouse_data['name'],
                is_alive=spouse_data.get('is_alive', True),
                birth_date=date.fromisoformat(spouse_data.get('birth_date')) if spouse_data.get('birth_date') else None,
                death_date=date.fromisoformat(spouse_data.get('death_date')) if spouse_data.get('death_date') else None
            )
            spouses.append(spouse)

        children = []
        for child_data in data.get('children', []):
            child = Person(
                name=child_data['name'],
                is_alive=child_data.get('is_alive', True),
                birth_date=date.fromisoformat(child_data.get('birth_date')) if child_data.get('birth_date') else None,
                death_date=date.fromisoformat(child_data.get('death_date')) if child_data.get('death_date') else None
            )
            children.append(child)

        parents = []
        for parent_data in data.get('parents', []):
            parent = Person(
                name=parent_data['name'],
                is_alive=parent_data.get('is_alive', True),
                birth_date=date.fromisoformat(parent_data.get('birth_date')) if parent_data.get('birth_date') else None,
                death_date=date.fromisoformat(parent_data.get('death_date')) if parent_data.get('death_date') else None
            )
            parents.append(parent)

        siblings = []
        sibling_blood_types = {}
        for sibling_data in data.get('siblings', []):
            sibling = Person(
                name=sibling_data['name'],
                is_alive=sibling_data.get('is_alive', True),
                birth_date=date.fromisoformat(sibling_data.get('birth_date')) if sibling_data.get('birth_date') else None,
                death_date=date.fromisoformat(sibling_data.get('death_date')) if sibling_data.get('death_date') else None
            )
            siblings.append(sibling)

            # 血縁タイプの設定
            blood_type_str = sibling_data.get('blood_type', 'full')
            sibling_blood_types[str(sibling.id)] = BloodType.FULL if blood_type_str == 'full' else BloodType.HALF

        # 相続放棄者の名前リストを取得
        renounced_names = data.get('renounced', [])
        renounced = []
        all_persons = spouses + children + parents + siblings
        for name in renounced_names:
            person = next((p for p in all_persons if p.name == name), None)
            if person:
                renounced.append(person)

        # 相続計算の実行
        calculator = InheritanceCalculator()
        result = calculator.calculate(
            decedent=decedent,
            spouses=spouses,
            children=children,
            parents=parents,
            siblings=siblings,
            renounced=renounced if renounced else None,
            sibling_blood_types=sibling_blood_types if sibling_blood_types else None
        )

        # 結果の表示
        display_result(result)

        # 出力ファイルが指定されている場合
        if output_file:
            export_result(result, output_file)
            display_info(f"結果を {output_file} に出力しました。")

        return 0

    except FileNotFoundError:
        display_error(f"ファイルが見つかりません: {input_file}")
        return 1
    except json.JSONDecodeError as e:
        display_error(f"JSONファイルの解析エラー: {str(e)}")
        return 1
    except KeyError as e:
        display_error(f"必須フィールドが不足しています: {str(e)}")
        return 1
    except Exception as e:
        display_error(f"予期しないエラー: {str(e)}")
        return 1


def calculate_from_csv(input_file: Path, output_file: Optional[Path] = None) -> int:
    """CSVファイルから相続計算を実行

    Args:
        input_file: 入力CSVファイルパス
        output_file: 出力ファイルパス（オプション）

    Returns:
        終了コード
    """
    try:
        # CSVファイルを読み込み
        decedent, spouses, children, parents, siblings, renounced, sibling_blood_types = \
            CSVParser.parse_csv_file(input_file)

        # 相続計算の実行
        calculator = InheritanceCalculator()
        result = calculator.calculate(
            decedent=decedent,
            spouses=spouses,
            children=children,
            parents=parents,
            siblings=siblings,
            renounced=renounced if renounced else None,
            sibling_blood_types=sibling_blood_types if sibling_blood_types else None
        )

        # 結果の表示
        display_result(result)

        # 出力ファイルが指定されている場合
        if output_file:
            export_result(result, output_file)
            display_info(f"結果を {output_file} に出力しました。")

        return 0

    except FileNotFoundError:
        display_error(f"ファイルが見つかりません: {input_file}")
        return 1
    except Exception as e:
        display_error(f"CSVファイルの処理エラー: {str(e)}")
        return 1


def calculate_interactive() -> int:
    """対話モードで相続計算を実行

    Returns:
        終了コード
    """
    from examples.demo_interactive import main as interactive_main

    try:
        interactive_main()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]計算を中断しました。[/yellow]")
        return 130
    except Exception as e:
        display_error(f"エラーが発生しました: {str(e)}")
        return 1


def export_result(result: Any, output_file: Path) -> None:
    """計算結果をファイルにエクスポート

    Args:
        result: 相続計算結果
        output_file: 出力ファイルパス
    """
    import json

    # ファイル拡張子で出力形式を判定
    file_ext = output_file.suffix.lower()

    if file_ext == '.json':
        # JSON形式
        output_data = {
            "decedent": str(result.decedent),
            "total_heirs": result.total_heirs,
            "has_spouse": result.has_spouse,
            "has_children": result.has_children,
            "has_parents": result.has_parents,
            "has_siblings": result.has_siblings,
            "heirs": [
                {
                    "name": str(heir.person),
                    "rank": heir.rank.value,
                    "share": str(heir.share),
                    "share_percentage": float(heir.share_percentage)
                }
                for heir in result.heirs
            ],
            "calculation_basis": result.calculation_basis
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    elif file_ext == '.md':
        # Markdown形式
        ReportGenerator.generate_markdown(result, output_file)

    elif file_ext == '.pdf':
        # PDF形式
        ReportGenerator.generate_pdf(result, output_file)

    else:
        raise ValueError(f"サポートされていない出力形式です: {file_ext}")


def validate_command(args: Namespace) -> int:
    """入力ファイルの検証コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    import json

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 必須フィールドの検証
        required_fields = ['decedent']
        for field in required_fields:
            if field not in data:
                display_error(f"必須フィールドが不足しています: {field}")
                return 1

        # 被相続人の検証
        decedent = data['decedent']
        if 'name' not in decedent:
            display_error("被相続人の氏名が不足しています")
            return 1
        if 'death_date' not in decedent:
            display_error("被相続人の死亡日が不足しています")
            return 1

        display_info(f"✓ {args.input_file} は有効な入力ファイルです")
        return 0

    except FileNotFoundError:
        display_error(f"ファイルが見つかりません: {args.input_file}")
        return 1
    except json.JSONDecodeError as e:
        display_error(f"JSONファイルの解析エラー: {str(e)}")
        return 1
    except Exception as e:
        display_error(f"検証エラー: {str(e)}")
        return 1


def template_command(args: Namespace) -> int:
    """テンプレートファイル作成コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    try:
        output_file = args.output_file

        if output_file.suffix.lower() == '.csv':
            CSVParser.create_template_csv(output_file)
            display_info(f"CSVテンプレートを作成しました: {output_file}")
        else:
            display_error(f"サポートされていないファイル形式です: {output_file.suffix}")
            display_info("対応形式: .csv")
            return 1

        return 0

    except Exception as e:
        display_error(f"テンプレート作成エラー: {str(e)}")
        return 1


def demo_command(args: Namespace) -> int:
    """デモ実行コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    try:
        if args.type == 'basic':
            from examples.demo_basic_cases import main as demo_main
        elif args.type == 'complex':
            from examples.demo_complex_cases import main as demo_main
        elif args.type == 'interactive':
            from examples.demo_interactive import main as demo_main
        else:
            display_error(f"不明なデモタイプ: {args.type}")
            return 1

        demo_main()
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]デモを中断しました。[/yellow]")
        return 130
    except Exception as e:
        display_error(f"デモ実行エラー: {str(e)}")
        return 1


def tree_command(args: Namespace) -> int:
    """家系図生成コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    try:
        # 入力ファイルから計算
        if args.input_file.suffix.lower() == '.csv':
            decedent, spouses, children, parents, siblings, renounced, sibling_blood_types = \
                CSVParser.parse_csv_file(args.input_file)
        else:
            # JSON形式の読み込み（calculate_from_fileと同様）
            import json
            from datetime import date
            from src.models.person import Person
            from src.models.relationship import BloodType

            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            decedent_data = data['decedent']
            decedent = Person(
                name=decedent_data['name'],
                is_decedent=True,
                is_alive=False,
                birth_date=date.fromisoformat(decedent_data.get('birth_date')) if decedent_data.get('birth_date') else None,
                death_date=date.fromisoformat(decedent_data['death_date'])
            )

            spouses = []
            for spouse_data in data.get('spouses', []):
                spouse = Person(
                    name=spouse_data['name'],
                    is_alive=spouse_data.get('is_alive', True),
                    birth_date=date.fromisoformat(spouse_data.get('birth_date')) if spouse_data.get('birth_date') else None,
                    death_date=date.fromisoformat(spouse_data.get('death_date')) if spouse_data.get('death_date') else None
                )
                spouses.append(spouse)

            children = []
            for child_data in data.get('children', []):
                child = Person(
                    name=child_data['name'],
                    is_alive=child_data.get('is_alive', True),
                    birth_date=date.fromisoformat(child_data.get('birth_date')) if child_data.get('birth_date') else None,
                    death_date=date.fromisoformat(child_data.get('death_date')) if child_data.get('death_date') else None
                )
                children.append(child)

            parents = []
            for parent_data in data.get('parents', []):
                parent = Person(
                    name=parent_data['name'],
                    is_alive=parent_data.get('is_alive', True),
                    birth_date=date.fromisoformat(parent_data.get('birth_date')) if parent_data.get('birth_date') else None,
                    death_date=date.fromisoformat(parent_data.get('death_date')) if parent_data.get('death_date') else None
                )
                parents.append(parent)

            siblings = []
            sibling_blood_types = {}
            for sibling_data in data.get('siblings', []):
                sibling = Person(
                    name=sibling_data['name'],
                    is_alive=sibling_data.get('is_alive', True),
                    birth_date=date.fromisoformat(sibling_data.get('birth_date')) if sibling_data.get('birth_date') else None,
                    death_date=date.fromisoformat(sibling_data.get('death_date')) if sibling_data.get('death_date') else None
                )
                siblings.append(sibling)
                blood_type_str = sibling_data.get('blood_type', 'full')
                sibling_blood_types[str(sibling.id)] = BloodType.FULL if blood_type_str == 'full' else BloodType.HALF

            renounced_names = data.get('renounced', [])
            renounced = []
            all_persons = spouses + children + parents + siblings
            for name in renounced_names:
                person = next((p for p in all_persons if p.name == name), None)
                if person:
                    renounced.append(person)

        # 相続計算の実行
        calculator = InheritanceCalculator()
        result = calculator.calculate(
            decedent=decedent,
            spouses=spouses,
            children=children,
            parents=parents,
            siblings=siblings,
            renounced=renounced if renounced else None,
            sibling_blood_types=sibling_blood_types if sibling_blood_types else None
        )

        # 家系図の生成
        output_path = args.output_file
        file_ext = output_path.suffix.lower()

        if file_ext == '.txt':
            # テキスト形式
            tree_text = FamilyTreeGenerator.generate_text_tree(result, output_path)
            console.print(tree_text)
            display_info(f"テキスト形式の家系図を {output_path} に出力しました。")

        elif file_ext == '.mmd' or file_ext == '.md':
            # Mermaid形式
            FamilyTreeGenerator.generate_mermaid(result, output_path)
            display_info(f"Mermaid形式の家系図を {output_path} に出力しました。")
            display_info("GitHubやMermaid対応エディタで表示できます。")

        else:
            # Graphviz形式（拡張子なしまたはpng, pdf, svgなど）
            format_type = file_ext[1:] if file_ext else 'png'
            if format_type not in ['png', 'pdf', 'svg', 'jpg']:
                format_type = 'png'

            # 拡張子を除いたパス
            output_stem = output_path.parent / output_path.stem

            FamilyTreeGenerator.generate_graphviz(result, output_stem, format=format_type)
            display_info(f"Graphviz形式の家系図を {output_stem}.{format_type} に出力しました。")

        return 0

    except FileNotFoundError:
        display_error(f"ファイルが見つかりません: {args.input_file}")
        return 1
    except Exception as e:
        display_error(f"家系図生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def version_command(args: Namespace) -> int:
    """バージョン表示コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    console.print("[bold green]相続計算機 (Inheritance Calculator)[/bold green]")
    console.print("バージョン: 1.0.0")
    console.print("日本の民法に基づく相続計算ツール")
    return 0
