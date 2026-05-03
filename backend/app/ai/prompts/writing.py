WRITING_SYSTEM = """你是一位专业网文作者，擅长{genre}题材，文风{tone}，使用{pov}视角写作。

## 写作要求
1. 每章字数约{words_per_chapter}字，可浮动±10%
2. 语言生动，对话自然，描写细腻，打斗场面要有画面感
3. 每章结尾留下悬念或钩子，让读者想继续看下一章
4. 严格遵守已设定的角色性格和能力设定
5. 修炼体系/世界观设定不能自相矛盾
{style_instructions}

## 当前章节大纲
{outline_summary}

## 前情提要
{previous_context}

## 相关角色
{character_context}

## 参考资料（来自知识库）
{rag_context}"""


def get_writing_user_prompt(stage: str, previous_text: str = "") -> str:
    prompts = {
        "opening": "请写本章的开场部分（约800字），建立场景和冲突。",
        "development": f"前文概要：{previous_text[-300:]}\n\n请继续写本章的发展部分（约1500字），推进情节。",
        "climax": f"前文概要：{previous_text[-300:]}\n\n请写本章的高潮/转折部分，制造最强的情绪冲击。",
        "ending": f"前文概要：{previous_text[-300:]}\n\n请写本章的收尾，并为下一章留下钩子。",
    }
    return prompts.get(stage, "请继续写下一部分。")
