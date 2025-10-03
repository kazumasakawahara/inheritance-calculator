"""相続情報収集用プロンプトテンプレート

AIエージェントが使用する質問と応答のプロンプトを定義する。
"""
from typing import Dict, List, Optional
from datetime import date


class InheritancePrompts:
    """相続情報収集用のプロンプトテンプレート集"""

    # システムプロンプト
    SYSTEM_PROMPT = """あなたは日本の相続法に精通した専門の相続アシスタントです。
被相続人（故人）の相続に関する情報を丁寧に収集し、法定相続人と相続割合を正確に計算するお手伝いをします。

あなたの役割:
1. ユーザーから相続に関する情報を段階的に収集する
2. 必要に応じて法的な用語を分かりやすく説明する
3. 民法の規定に基づいて正確な情報を提供する
4. ユーザーの回答を確認し、必要なら再質問する

重要な注意事項:
- 法的助言は提供せず、情報収集と計算のみを行う
- 複雑なケースでは弁護士や司法書士への相談を推奨する
- ユーザーの個人情報を尊重し、丁寧な言葉遣いを心がける
- 回答は簡潔かつ明確にする"""

    # 被相続人情報収集
    DECEDENT_INTRO = """これから被相続人（亡くなられた方）の相続に関する情報を収集させていただきます。
順番に質問してまいりますので、お分かりになる範囲でお答えください。

まず、被相続人の基本情報からお伺いします。"""

    DECEDENT_NAME = """被相続人（亡くなられた方）のお名前をお教えください。

（例: 山田太郎）"""

    DECEDENT_DEATH_DATE = """被相続人の死亡日（相続開始日）をお教えください。

形式: YYYY-MM-DD または YYYY年MM月DD日
（例: 2025-06-15 または 2025年6月15日）"""

    DECEDENT_BIRTH_DATE = """被相続人の生年月日をお教えください（任意）。

形式: YYYY-MM-DD または YYYY年MM月DD日
（例: 1950-01-01 または 1950年1月1日）

※分からない場合は「不明」とご入力ください。"""

    # 配偶者情報収集
    SPOUSE_QUESTION = """被相続人に配偶者（法律上の婚姻関係にある方）はいらっしゃいますか？

※内縁関係の方は法定相続人には含まれません。
※離婚された元配偶者も法定相続人には含まれません。

回答: はい / いいえ"""

    SPOUSE_INFO = """配偶者の情報をお教えください。

1. お名前:
2. 現在存命ですか？（はい/いいえ）:
3. 生年月日（分かる場合）:"""

    # 子の情報収集
    CHILDREN_QUESTION = """被相続人にお子様（実子・養子を含む）はいらっしゃいますか？

※胎児も相続人となりますが、生きて生まれることが条件です。
※養子縁組されたお子様も実子と同様に相続人となります。

回答: はい / いいえ"""

    CHILDREN_COUNT = """お子様は何人いらっしゃいますか？

人数: """

    CHILD_INFO_TEMPLATE = """【{index}人目のお子様の情報】

1. お名前:
2. 現在存命ですか？（はい/いいえ）:
3. 生年月日（分かる場合）:
4. 実子ですか、養子ですか？（実子/養子）:
5. 被相続人より先に亡くなっている場合、そのお子様（被相続人の孫）はいますか？（はい/いいえ/該当なし）:"""

    # 代襲相続の確認
    SUBSTITUTION_GRANDCHILDREN = """{child_name}さんのお子様（被相続人の孫）について教えてください。

※{child_name}さんが被相続人より先に亡くなっている場合、そのお子様が代襲相続人となります。

お子様の人数: """

    GRANDCHILD_INFO_TEMPLATE = """【{child_name}さんのお子様 {index}人目の情報】

1. お名前:
2. 現在存命ですか？（はい/いいえ）:
3. 生年月日（分かる場合）:"""

    # 直系尊属（父母・祖父母）の情報収集
    PARENTS_QUESTION = """被相続人のご両親（父母）、またはご健在の祖父母はいらっしゃいますか？

※第1順位の相続人（お子様）がいない場合、第2順位として直系尊属が相続人となります。
※父母がいらっしゃる場合、祖父母は相続人になりません。

回答: はい / いいえ"""

    PARENT_INFO_TEMPLATE = """【直系尊属の情報】

1. 続柄（父/母/祖父/祖母）:
2. お名前:
3. 現在存命ですか？（はい/いいえ）:
4. 生年月日（分かる場合）:"""

    # 兄弟姉妹の情報収集
    SIBLINGS_QUESTION = """被相続人にご兄弟姉妹はいらっしゃいますか？

※第1順位（お子様）および第2順位（直系尊属）の相続人がいない場合のみ、
　兄弟姉妹が第3順位の相続人となります。

回答: はい / いいえ"""

    SIBLINGS_COUNT = """ご兄弟姉妹は何人いらっしゃいますか？

人数: """

    SIBLING_INFO_TEMPLATE = """【{index}人目のご兄弟姉妹の情報】

1. お名前:
2. 続柄（兄/弟/姉/妹）:
3. 現在存命ですか？（はい/いいえ）:
4. 父母との関係（両親とも同じ/父のみ同じ/母のみ同じ）:
   ※これは全血・半血の判定に使用します
5. 被相続人より先に亡くなっている場合、そのお子様（甥・姪）はいますか？（はい/いいえ/該当なし）:"""

    # 相続放棄・欠格・廃除の確認
    RENUNCIATION_QUESTION = """相続放棄をされた方はいらっしゃいますか？

※相続放棄は家庭裁判所に申述して初めて効力が生じます。
※相続放棄をした方は、初めから相続人でなかったものとみなされます。

回答: はい / いいえ"""

    RENUNCIATION_INFO = """相続放棄をされた方のお名前を教えてください（複数いる場合はカンマ区切り）:

例: 山田一郎, 山田二郎"""

    DISQUALIFICATION_QUESTION = """相続欠格者（相続人となれない事由がある方）はいらっしゃいますか？

相続欠格事由の例:
- 被相続人や先順位・同順位の相続人を故意に死亡させた、またはさせようとした
- 被相続人が殺害されたことを知りながら告発・告訴しなかった
- 詐欺・強迫により被相続人の遺言を妨げた、取り消させた、変更させた

回答: はい / いいえ"""

    DISINHERITANCE_QUESTION = """相続廃除された方はいらっしゃいますか？

※相続廃除は、被相続人に対する虐待や重大な侮辱があった場合に、
　家庭裁判所の審判によって相続権を剥奪する制度です。

回答: はい / いいえ"""

    # 再転相続の確認
    RETRANSFER_QUESTION = """遺産分割協議が終わる前に亡くなられた相続人はいらっしゃいますか？

※この場合、その相続人の相続分は、その相続人の相続人に引き継がれます（再転相続）。
※これは代襲相続とは異なります。

回答: はい / いいえ"""

    RETRANSFER_INFO_TEMPLATE = """{heir_name}さんは遺産分割前に亡くなられました。
{heir_name}さんの相続人について教えてください。

1. 配偶者はいますか？（はい/いいえ）:
2. お子様はいますか？（はい/いいえ）:
3. いらっしゃる場合、それぞれのお名前:"""

    # 確認と完了
    CONFIRMATION = """以下の情報で間違いございませんか？

{summary}

確認: はい / いいえ / 修正する項目を教えてください"""

    CALCULATION_START = """情報の収集が完了しました。
これより法定相続人の確定と相続割合の計算を行います。

計算を開始してもよろしいですか？

回答: はい / いいえ"""

    COMPLETION = """相続計算が完了しました。
結果は以下の通りです。

{result}

この結果は法定相続分に基づくものです。
実際の遺産分割は、相続人全員の協議によって決定されます。

※本計算結果は参考情報であり、法的助言ではありません。
※実際の相続手続きについては、弁護士や司法書士にご相談ください。"""

    @staticmethod
    def format_child_info(index: int) -> str:
        """子の情報収集プロンプトをフォーマット"""
        return InheritancePrompts.CHILD_INFO_TEMPLATE.format(index=index)

    @staticmethod
    def format_grandchild_info(child_name: str, index: int) -> str:
        """孫の情報収集プロンプトをフォーマット"""
        return InheritancePrompts.GRANDCHILD_INFO_TEMPLATE.format(
            child_name=child_name,
            index=index
        )

    @staticmethod
    def format_sibling_info(index: int) -> str:
        """兄弟姉妹の情報収集プロンプトをフォーマット"""
        return InheritancePrompts.SIBLING_INFO_TEMPLATE.format(index=index)

    @staticmethod
    def format_confirmation(summary: str) -> str:
        """確認プロンプトをフォーマット"""
        return InheritancePrompts.CONFIRMATION.format(summary=summary)

    @staticmethod
    def format_completion(result: str) -> str:
        """完了メッセージをフォーマット"""
        return InheritancePrompts.COMPLETION.format(result=result)


# 質問フローの定義
QUESTION_FLOW = [
    "decedent_intro",
    "decedent_name",
    "decedent_death_date",
    "decedent_birth_date",
    "spouse_question",
    "children_question",
    "parents_question",
    "siblings_question",
    "renunciation_question",
    "retransfer_question",
    "confirmation",
    "calculation_start",
]
