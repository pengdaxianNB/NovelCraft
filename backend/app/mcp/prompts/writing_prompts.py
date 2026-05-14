import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_prompts(server: FastMCP):
    @server.prompt()
    async def continue_writing(novel_id: str, chapter_number: int) -> str:
        """根据当前进度生成续写提示词，聚合上下文"""
        from app.services.novel_service import NovelService
        from app.services.outline_service import OutlineService
        from app.services.character_service import CharacterService
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return f"错误: 小说 {novel_id} 不存在"

                outlines = await OutlineService(db).list_outlines(novel_id)
                characters = await CharacterService(db).list_characters(novel_id)
                chapters = await ChapterService(db).list_chapters(novel_id)

            style = novel.style_config or {}

            def flatten(nodes, depth=0):
                result = []
                for n in nodes:
                    result.append(f"{'  ' * depth}[{n.level}] {n.title}: {n.summary or '(无摘要)'}")
                    if n.children:
                        result.extend(flatten(n.children, depth + 1))
                return result

            outline_text = "\n".join(flatten(outlines)) if outlines else "(暂无大纲)"

            char_text = "\n".join(
                f"- {c.name}({c.role}): "
                + "; ".join(f"{k}: {v}" for k, v in (c.profile or {}).items() if v)
                for c in characters
            ) or "(暂无角色)"

            recent = sorted(chapters, key=lambda x: x.chapter_number, reverse=True)[:2]
            prev_text = "\n\n".join(
                f"## 第{ch.chapter_number}章: {ch.title}\n{(ch.content or '')[-800:]}"
                for ch in recent
            ) or "(暂无前文章节)"

            return f"""你正在续写小说《{novel.title}》（{novel.genre}）第{chapter_number}章。

## 风格配置
- 基调: {style.get('tone', '热血')}
- 视角: {style.get('pov', '第三人称')}
- 每章目标字数: {style.get('words_per_chapter', 3000)}
- 特殊要求: {style.get('custom_instructions', '无')}

## 大纲
{outline_text}

## 角色档案
{char_text}

## 前情提要
{prev_text}

请从上一章结尾处开始，按照大纲规划续写第{chapter_number}章。"""

        except Exception as e:
            return f"构建续写提示词失败: {str(e)}"

    @server.prompt()
    async def character_dialogue(novel_id: str, character_id: str, scene: str) -> str:
        """为特定角色生成对话提示词"""
        from app.services.character_service import CharacterService
        from app.services.novel_service import NovelService

        try:
            async with get_mcp_db() as db:
                character = await CharacterService(db).get_character(character_id)
                if not character or str(character.novel_id) != novel_id:
                    return f"错误: 角色 {character_id} 在小说 {novel_id} 中不存在"

                novel = await NovelService(db).get_novel(novel_id)

            profile_text = (
                json.dumps(character.profile, ensure_ascii=False, indent=2)
                if character.profile
                else "(暂无角色档案)"
            )

            return f"""为小说《{novel.title if novel else '未知'}》中的角色生成对话。

## 角色信息
- 姓名: {character.name}
- 角色定位: {character.role}
- 档案: {profile_text}

## 场景
{scene}

请写出符合该角色性格、背景和当前情绪状态的自然对话。对话应与上述场景一致，并忠实于角色的既定档案。"""

        except Exception as e:
            return f"构建角色对话提示词失败: {str(e)}"

    @server.prompt()
    async def review_chapter(novel_id: str, chapter_number: int) -> str:
        """生成章节审校提示词，检查一致性、剧情、风格"""
        from app.services.novel_service import NovelService
        from app.services.chapter_service import ChapterService
        from app.services.character_service import CharacterService
        from app.services.world_setting_service import WorldSettingService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return f"错误: 小说 {novel_id} 不存在"
                chapters = await ChapterService(db).list_chapters(novel_id)
                target = next((ch for ch in chapters if ch.chapter_number == chapter_number), None)
                if not target or not target.content:
                    return f"错误: 第 {chapter_number} 章不存在或内容为空"

                characters = await CharacterService(db).list_characters(novel_id)
                world_settings = await WorldSettingService(db).list_world_settings(novel_id)

            style = novel.style_config or {}

            char_context = "\n".join(
                f"- {c.name}({c.role})" for c in characters
            ) or "(无角色)"

            world_context = "\n".join(
                f"- [{ws.category}] {ws.title}: {ws.content}" for ws in world_settings
            ) or "(无世界观设定)"

            prev_chapters = [ch for ch in chapters if ch.chapter_number < chapter_number]
            prev_context = "\n\n".join(
                f"第{ch.chapter_number}章 {ch.title}\n{(ch.content or '')[-500:]}"
                for ch in sorted(prev_chapters, key=lambda x: x.chapter_number, reverse=True)[:3]
            ) or "(无前文章节)"

            return f"""请审校小说《{novel.title}》（{novel.genre}）第{chapter_number}章《{target.title}》。

## 风格配置
- 基调: {style.get('tone', '热血')}
- 视角: {style.get('pov', '第三人称')}
- 目标字数: {style.get('words_per_chapter', 3000)}
- 当前字数: {target.word_count}

## 角色清单
{char_context}

## 世界观设定
{world_context}

## 前情提要
{prev_context}

## 待审校正文
---
{target.content}
---

请从以下 5 个维度进行审校：
1. **角色一致性**: 角色性格、能力、关系是否前后矛盾？
2. **剧情连贯性**: 剧情是否与前文衔接自然？是否有逻辑漏洞？
3. **设定合规性**: 是否违反已建立的世界观规则？
4. **风格一致性**: 文风、基调是否与设定一致？
5. **篇幅控制**: 字数是否合理？是否有水字数或节奏过快的问题？

请逐一给出评价和建议。"""

        except Exception as e:
            return f"构建审校提示词失败: {str(e)}"

    @server.prompt()
    async def brainstorm_plot(novel_id: str, scenario: str = "") -> str:
        """生成情节头脑风暴提示词，基于当前设定和进度推演后续发展"""
        from app.services.novel_service import NovelService
        from app.services.outline_service import OutlineService
        from app.services.character_service import CharacterService
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return f"错误: 小说 {novel_id} 不存在"

                outlines = await OutlineService(db).list_outlines(novel_id)
                characters = await CharacterService(db).list_characters(novel_id)
                chapters = await ChapterService(db).list_chapters(novel_id)

            style = novel.style_config or {}

            def flatten(nodes, depth=0):
                result = []
                for n in nodes:
                    result.append(f"{'  ' * depth}[{n.level}] {n.title}: {n.summary or ''}")
                    if n.children:
                        result.extend(flatten(n.children, depth + 1))
                return result

            outline_text = "\n".join(flatten(outlines)) if outlines else "(暂无大纲)"

            char_text = "\n".join(
                f"- {c.name}({c.role}): "
                + "; ".join(f"{k}: {v}" for k, v in list((c.profile or {}).items())[:5] if v)
                for c in characters
            ) or "(暂无角色)"

            latest = max((ch.chapter_number for ch in chapters), default=0)
            recent_chapters = sorted(chapters, key=lambda x: x.chapter_number, reverse=True)[:3]
            progress = f"已写 {len(chapters)} 章，最新章节: 第{latest}章"

            scenario_text = f"\n## 用户指定场景\n{scenario}" if scenario else ""

            return f"""你是一位资深网文策划，请为小说《{novel.title}》（{novel.genre}）进行情节头脑风暴。{scenario_text}

## 小说概况
- 梗概: {novel.synopsis}
- 基调: {style.get('tone', '热血')}
- 写作进度: {progress}

## 大纲结构
{outline_text}

## 角色阵容
{char_text}

## 最近进展
{chr(10).join(f'第{ch.chapter_number}章《{ch.title}》: {(ch.content or "")[:300]}...' for ch in recent_chapters) if recent_chapters else '(暂无已写章节)'}

请从以下几个角度进行头脑风暴：
1. **短期**: 接下来 3-5 章可以发展什么剧情线？
2. **中期**: 当前卷/弧还有哪些未解决的冲突？
3. **长期**: 有什么埋线可以提前布局？
4. **角色发展**: 主要角色可以经历怎样的成长/转折？
5. **爆点/高潮**: 有什么令人意想不到的剧情转折？

请给出具体可行的情节建议，而不是泛泛而谈。"""

        except Exception as e:
            return f"构建头脑风暴提示词失败: {str(e)}"

    @server.prompt()
    async def create_character(novel_id: str, story_role: str = "") -> str:
        """生成角色创建设计提示词，基于已有设定和故事需要"""
        from app.services.novel_service import NovelService
        from app.services.character_service import CharacterService
        from app.services.world_setting_service import WorldSettingService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return f"错误: 小说 {novel_id} 不存在"

                existing = await CharacterService(db).list_characters(novel_id)
                world_settings = await WorldSettingService(db).list_world_settings(novel_id)

            style = novel.style_config or {}

            existing_chars = "\n".join(
                f"- {c.name}({c.role}): "
                + "; ".join(f"{k}: {v}" for k, v in list((c.profile or {}).items())[:4] if v)
                for c in existing
            ) or "(暂无已有角色)"

            world_text = "\n".join(
                f"- [{ws.category}] {ws.title}: {ws.content}" for ws in world_settings
            ) or "(暂无世界观设定)"

            role_hint = f"，该角色在故事中的定位是：{story_role}" if story_role else ""

            return f"""你是一位角色设计师，请为小说《{novel.title}》（{novel.genre}）创建新角色{role_hint}。

## 小说背景
- 梗概: {novel.synopsis}
- 基调: {style.get('tone', '热血')}

## 世界观
{world_text}

## 已有角色（避免重复）
{existing_chars}

请设计一个完整的角色档案，包含：
1. **基本信息**: 姓名、年龄、性别、外貌
2. **性格特征**: 核心性格、优点、缺点、癖好
3. **背景故事**: 出身、重要经历、内心创伤/驱动力
4. **能力体系**: 特殊能力/技能（如有）、等级
5. **人际关系**: 与其他角色的关系、在故事中的立场
6. **成长弧线**: 该角色在故事中可能经历的变化

请确保角色足够立体（有缺点和内心矛盾），与现有角色阵容互补，且符合世界观设定。"""

        except Exception as e:
            return f"构建角色创建提示词失败: {str(e)}"

    @server.prompt()
    async def plan_arc(novel_id: str, arc_purpose: str = "") -> str:
        """生成故事弧线/分卷规划提示词"""
        from app.services.novel_service import NovelService
        from app.services.outline_service import OutlineService
        from app.services.character_service import CharacterService
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return f"错误: 小说 {novel_id} 不存在"

                outlines = await OutlineService(db).list_outlines(novel_id)
                characters = await CharacterService(db).list_characters(novel_id)
                chapters = await ChapterService(db).list_chapters(novel_id)

            style = novel.style_config or {}

            # Volume-level outlines only
            volumes = [n for n in outlines if n.level == "volume"]

            char_summary = "\n".join(
                f"- {c.name}({c.role})" for c in characters
            ) or "(暂无角色)"

            progress = f"已完成 {len(chapters)} 章，最新章节第{max((ch.chapter_number for ch in chapters), default=0)}章"

            NL = "\n"
            vol_text = (
                NL.join(
                    f"### {v.title}" + NL + f"{v.summary or '(无摘要)'}"
                    for v in sorted(volumes, key=lambda x: x.sequence)
                )
                if volumes else "(暂无分卷)"
            )

            purpose_text = f"\n## 规划目标\n{arc_purpose}" if arc_purpose else ""

            return f"""你是一位网文结构策划，请为小说《{novel.title}》（{novel.genre}）进行故事弧线规划。{purpose_text}

## 小说概况
- 梗概: {novel.synopsis}
- 基调: {style.get('tone', '热血')}
- 进度: {progress}

## 已有分卷
{vol_text}

## 角色阵容
{char_summary}

请规划一条完整的故事弧线，包含：
1. **弧线名称和主题**: 这条弧线要讲什么？
2. **起承转合**: 起始状态→激励事件→冲突升级→高潮→结局
3. **章节划分**: 需要多少章？每章核心剧情是什么？
4. **关键角色**: 哪些角色参与？各自的角色弧线是什么？
5. **与主线的关联**: 如何推动主线？解决/制造什么问题？
6. **情感曲线**: 读者情绪应如何起伏？（紧张/轻松/感动/爽快）

请给出具体可执行的分章方案，每章包含核心冲突和关键场景。"""

        except Exception as e:
            return f"构建弧线规划提示词失败: {str(e)}"
