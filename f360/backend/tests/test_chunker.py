"""
F360 – Tests: Document Chunker
"""
import pytest
from app.services.rag.embedder import chunk_text


class TestChunking:
    def test_short_text(self):
        text = "This is a short document."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text(None) == []

    def test_long_text_splitting(self):
        text = "Word " * 500  # ~2500 chars
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) > 1
        # All chunks should have content
        for chunk in chunks:
            assert len(chunk) > 0

    def test_overlap(self):
        text = "A" * 2000
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        # With overlap, later chunks should start before previous chunk ends
        assert len(chunks) >= 4
