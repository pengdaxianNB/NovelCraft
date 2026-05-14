from app.ai.prompts import writing, outline, review, world_setting, character


def get_prompt_versions() -> dict[str, str]:
    return {
        "writing": writing.VERSION,
        "outline": outline.VERSION,
        "review": review.VERSION,
        "world_setting": world_setting.VERSION,
        "character": character.VERSION,
    }
