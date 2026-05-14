from dataclasses import dataclass


DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]


@dataclass
class SimpleTextSplitter:
    _chunk_size: int = 800
    _chunk_overlap: int = 100
    separators: list[str] | None = None

    def split_text(self, content: str) -> list[str]:
        content = (content or "").strip()
        if not content:
            return []
        if len(content) <= self._chunk_size:
            return [content]

        chunks: list[str] = []
        start = 0
        while start < len(content):
            hard_end = min(start + self._chunk_size, len(content))
            end = self._best_break(content, start, hard_end)
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(content):
                break
            next_start = max(end - self._chunk_overlap, start + 1)
            start = next_start
        return chunks

    def _best_break(self, content: str, start: int, hard_end: int) -> int:
        window = content[start:hard_end]
        for sep in self.separators or DEFAULT_SEPARATORS:
            if not sep:
                continue
            index = window.rfind(sep)
            if index > 0:
                return start + index + len(sep)
        return hard_end


def create_splitter(chunk_size: int = 800, chunk_overlap: int = 100) -> SimpleTextSplitter:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    return SimpleTextSplitter(
        _chunk_size=chunk_size,
        _chunk_overlap=chunk_overlap,
        separators=DEFAULT_SEPARATORS,
    )


def split_document(content: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    return create_splitter(chunk_size, chunk_overlap).split_text(content)
