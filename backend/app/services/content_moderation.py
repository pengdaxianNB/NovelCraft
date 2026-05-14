from dataclasses import dataclass, field

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_BLOCKED_PATTERNS: list[str] = []


@dataclass
class ModerationResult:
    passed: bool
    flags: list[str] = field(default_factory=list)
    severity: str = "none"


class ContentModerationService:
    def __init__(self, patterns: list[str] | None = None):
        self._patterns = patterns or DEFAULT_BLOCKED_PATTERNS

    def check(self, content: str) -> ModerationResult:
        if not content.strip():
            return ModerationResult(passed=True)

        flags: list[str] = []
        for pattern in self._patterns:
            if pattern and pattern in content:
                flags.append(f"matched_blocked_pattern")

        if flags:
            logger.warning("Content moderation flagged", flag_count=len(flags))
            return ModerationResult(passed=False, flags=flags, severity="warning")

        return ModerationResult(passed=True)


_moderation_service: ContentModerationService | None = None


def get_moderation_service() -> ContentModerationService:
    global _moderation_service
    if _moderation_service is None:
        blocked = settings.content_moderation_blocked_words
        patterns = [w.strip() for w in blocked.split(",") if w.strip()] if blocked else []
        _moderation_service = ContentModerationService(patterns)
    return _moderation_service
