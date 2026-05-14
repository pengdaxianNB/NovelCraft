import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_management_tools(server: FastMCP):
    # ── Character CRUD ──────────────────────────────────────────────

    @server.tool()
    async def create_character(
        novel_id: str,
        name: str,
        role: str = "配角",
        profile_json: str = "{}",
    ) -> str:
        """手动创建角色档案。profile_json 为 JSON 格式的角色属性"""
        from app.services.character_service import CharacterService
        from app.schemas.character import CharacterCreate

        try:
            profile = json.loads(profile_json) if isinstance(profile_json, str) else profile_json
        except json.JSONDecodeError:
            return json.dumps({"error": "profile_json 解析失败，请提供有效的 JSON 字符串"})

        try:
            async with get_mcp_db() as db:
                svc = CharacterService(db)
                char = await svc.create_character(
                    novel_id, CharacterCreate(name=name, role=role, profile=profile)
                )

            return json.dumps({
                "id": str(char.id),
                "name": char.name,
                "role": char.role,
                "profile": char.profile,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"创建角色失败: {str(e)}"})

    @server.tool()
    async def update_character(
        character_id: str,
        name: str = "",
        role: str = "",
        profile_json: str = "",
    ) -> str:
        """更新已有角色档案。仅传入需要修改的字段"""
        from app.services.character_service import CharacterService
        from app.schemas.character import CharacterUpdate

        profile = None
        if profile_json:
            try:
                profile = json.loads(profile_json)
            except json.JSONDecodeError:
                return json.dumps({"error": "profile_json 解析失败"})

        try:
            async with get_mcp_db() as db:
                svc = CharacterService(db)
                char = await svc.update_character(
                    character_id,
                    CharacterUpdate(
                        name=name or None,
                        role=role or None,
                        profile=profile,
                    ),
                )
                if not char:
                    return json.dumps({"error": f"角色 {character_id} 不存在"})

            return json.dumps({
                "id": str(char.id),
                "name": char.name,
                "role": char.role,
                "profile": char.profile,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"更新角色失败: {str(e)}"})

    # ── World Setting CRUD ─────────────────────────────────────────

    @server.tool()
    async def create_world_setting(
        novel_id: str,
        category: str,
        title: str,
        content: str,
    ) -> str:
        """手动创建世界观设定条目"""
        from app.services.world_setting_service import WorldSettingService
        from app.schemas.world_setting import WorldSettingCreate

        try:
            async with get_mcp_db() as db:
                svc = WorldSettingService(db)
                ws = await svc.create_world_setting(
                    novel_id,
                    WorldSettingCreate(category=category, title=title, content=content),
                )

            return json.dumps({
                "id": str(ws.id),
                "category": ws.category,
                "title": ws.title,
                "content": ws.content,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"创建世界观设定失败: {str(e)}"})

    @server.tool()
    async def update_world_setting(
        setting_id: str,
        category: str = "",
        title: str = "",
        content: str = "",
    ) -> str:
        """更新已有世界观设定条目。仅传入需要修改的字段"""
        from app.services.world_setting_service import WorldSettingService
        from app.schemas.world_setting import WorldSettingUpdate

        try:
            async with get_mcp_db() as db:
                svc = WorldSettingService(db)
                ws = await svc.update_world_setting(
                    setting_id,
                    WorldSettingUpdate(
                        category=category or None,
                        title=title or None,
                        content=content or None,
                    ),
                )
                if not ws:
                    return json.dumps({"error": f"世界观设定 {setting_id} 不存在"})

            return json.dumps({
                "id": str(ws.id),
                "category": ws.category,
                "title": ws.title,
                "content": ws.content,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"更新世界观设定失败: {str(e)}"})

    # ── Outline CRUD ───────────────────────────────────────────────

    @server.tool()
    async def create_outline(
        novel_id: str,
        level: str,
        title: str,
        summary: str = "",
        parent_id: str = "",
        sequence: int = 0,
    ) -> str:
        """手动创建大纲节点。level: volume/arc/chapter"""
        from app.services.outline_service import OutlineService
        from app.schemas.outline import OutlineCreate

        try:
            async with get_mcp_db() as db:
                svc = OutlineService(db)
                outline = await svc.create_outline(
                    novel_id,
                    OutlineCreate(
                        level=level,
                        title=title,
                        summary=summary or None,
                        parent_id=parent_id or None,
                        sequence=sequence,
                    ),
                )

            return json.dumps({
                "id": str(outline.id),
                "level": outline.level,
                "title": outline.title,
                "summary": outline.summary,
                "parent_id": str(outline.parent_id) if outline.parent_id else None,
                "sequence": outline.sequence,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"创建大纲失败: {str(e)}"})

    @server.tool()
    async def update_outline(
        outline_id: str,
        title: str = "",
        summary: str = "",
        status: str = "",
        sequence: int = -1,
    ) -> str:
        """更新大纲节点。仅传入需要修改的字段"""
        from app.services.outline_service import OutlineService
        from app.schemas.outline import OutlineUpdate

        try:
            async with get_mcp_db() as db:
                svc = OutlineService(db)
                outline = await svc.update_outline(
                    outline_id,
                    OutlineUpdate(
                        title=title or None,
                        summary=summary or None,
                        status=status or None,
                        sequence=sequence if sequence >= 0 else None,
                    ),
                )
                if not outline:
                    return json.dumps({"error": f"大纲节点 {outline_id} 不存在"})

            return json.dumps({
                "id": str(outline.id),
                "level": outline.level,
                "title": outline.title,
                "summary": outline.summary,
                "status": outline.status,
                "sequence": outline.sequence,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"更新大纲失败: {str(e)}"})
