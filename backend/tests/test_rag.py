"""Tests for RAG engine — splitter and retriever, no database needed."""

from app.ai.rag.splitter import create_splitter, split_document
from app.ai.rag.retriever import _rrf_fusion


class TestSplitter:
    def test_create_splitter_defaults(self):
        splitter = create_splitter()
        assert splitter._chunk_size == 800
        assert splitter._chunk_overlap == 100

    def test_create_splitter_custom(self):
        splitter = create_splitter(chunk_size=400, chunk_overlap=50)
        assert splitter._chunk_size == 400
        assert splitter._chunk_overlap == 50

    def test_split_short_text(self):
        result = split_document("短短一句话。")
        assert len(result) == 1
        assert result[0] == "短短一句话。"

    def test_split_long_text(self):
        text = "第一章　陨落的天才。\n\n" + "测试内容。" * 500
        chunks = split_document(text, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 210  # allow some slack

    def test_split_empty(self):
        chunks = split_document("")
        assert len(chunks) == 0

    def test_chinese_separators(self):
        text = "第一段。第二段！第三段？第四段，第五段"
        chunks = split_document(text, chunk_size=4, chunk_overlap=0)
        assert len(chunks) >= 1

    def test_paragraph_splitting(self):
        text = "段落一\n\n段落二\n\n段落三"
        chunks = split_document(text, chunk_size=5, chunk_overlap=0)
        assert len(chunks) >= 3


class TestRRFFusion:
    def test_empty_inputs(self):
        result = _rrf_fusion([], [])
        assert result == []

    def test_only_vector_results(self):
        vector = [
            {"id": "1", "content": "doc1"},
            {"id": "2", "content": "doc2"},
        ]
        result = _rrf_fusion(vector, [])
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_only_keyword_results(self):
        keyword = [
            {"id": "3", "content": "doc3"},
        ]
        result = _rrf_fusion([], keyword)
        assert len(result) == 1
        assert result[0]["id"] == "3"

    def test_merges_and_deduplicates(self):
        vector = [{"id": "1", "content": "v1"}, {"id": "2", "content": "v2"}]
        keyword = [{"id": "2", "content": "k2"}, {"id": "3", "content": "k3"}]
        result = _rrf_fusion(vector, keyword)
        ids = [r["id"] for r in result]
        assert len(result) == 3
        assert "1" in ids
        assert "2" in ids
        assert "3" in ids

    def test_boosted_documents_rank_higher(self):
        vector = [{"id": "2", "content": "v2"}]
        keyword = [{"id": "1", "content": "k1"}, {"id": "2", "content": "k2"}]
        result = _rrf_fusion(vector, keyword)
        # doc "2" appears in both lists and should rank higher
        assert result[0]["id"] == "2"

    def test_preserves_document_data(self):
        vector = [{"id": "a", "content": "text", "similarity": 0.95}]
        result = _rrf_fusion(vector, [])
        assert result[0]["content"] == "text"
        assert result[0]["similarity"] == 0.95
