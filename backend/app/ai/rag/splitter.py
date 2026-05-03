from langchain.text_splitter import RecursiveCharacterTextSplitter


def create_splitter(chunk_size: int = 800, chunk_overlap: int = 100):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
    )


def split_document(content: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    splitter = create_splitter(chunk_size, chunk_overlap)
    return splitter.split_text(content)
