VERSION = "1.0.0"

WRITING_SYSTEM = """你是一位专业网文作者，擅长{genre}题材，文风{tone}，使用{pov}视角写作。

## 字数要求（严格遵守）
本章总字数必须控制在{words_per_chapter}字，误差不得超过±5%。每个写作阶段会告知本阶段的具体目标字数，你必须精确达到。字数不达标将视为不合格。

## 写作要求
1. 语言生动，对话自然，描写细腻，打斗场面要有画面感
2. 每章结尾留下悬念或钩子，让读者想继续看下一章
3. 严格遵守已设定的角色性格和能力设定
4. 修炼体系/世界观设定不能自相矛盾
{style_instructions}

## 用户指定方向
{user_description}

## 当前章节大纲
{outline_summary}

## 前情提要
{previous_context}

## 相关角色
{character_context}

## 参考资料（来自知识库）
{rag_context}"""


def get_writing_user_prompt(
    stage: str,
    previous_text: str = "",
    total_target: int = 3000,
    chars_written: int = 0,
    remaining_budget: int = 3000,
    stage_target: int = 0,
) -> str:
    base = (
        f"【字数统计】总目标：{total_target}字 | 已写：{chars_written}字 | "
        f"剩余配额：{remaining_budget}字\n"
        f"【本阶段】必须写出约{stage_target}字，请严格控制字数，误差不超过5%。"
    )

    prev_snippet = previous_text[-300:] if previous_text else ""

    prompts = {
        "opening": (
            f"{base}\n\n"
            f"请写本章的开场部分。建立场景、引入主要角色、铺设初始冲突。"
        ),
        "development": (
            f"前文概要：{prev_snippet}\n\n"
            f"{base}\n\n"
            f"请继续写本章的发展部分。推进情节、展开冲突、深化角色关系。"
        ),
        "climax": (
            f"前文概要：{prev_snippet}\n\n"
            f"{base}\n\n"
            f"请写本章的高潮/转折部分。制造最强的情绪冲击，情节发生关键转折。"
        ),
        "ending": (
            f"前文概要：{prev_snippet}\n\n"
            f"{base}\n\n"
            f"请写本章的收尾。自然收束本章情节，为下一章埋下钩子。注意：这是本章最后一部分，写完后的全文总字数必须精确落在{total_target}±5%范围内。"
        ),
    }
    return prompts.get(
        stage,
        f"{base}\n\n请继续写下一部分。",
    )
