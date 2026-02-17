"""Test document parsers."""
import pytest
import os
from pathlib import Path

from src.parsers.pdf_parser import PDFParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.word_parser import WordParser


@pytest.fixture
def sample_docs_dir():
    """Get sample documents directory."""
    return Path(__file__).parent.parent / "data" / "sample_docs"


class TestPDFParser:
    """Test PDF parser."""
    
    def test_parse_pdf(self, sample_docs_dir):
        """Test parsing a PDF document."""
        parser = PDFParser()
        pdf_path = sample_docs_dir / "annual_report_2023.pdf"
        
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")
        
        result = parser.parse(str(pdf_path))
        
        assert result is not None
        assert "text" in result
        assert "file_type" in result
        assert result["file_type"] == "pdf"
        assert len(result["text"]) > 0
    
    def test_extract_text(self, sample_docs_dir):
        """Test extracting text from PDF."""
        parser = PDFParser()
        pdf_path = sample_docs_dir / "annual_report_2023.pdf"
        
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")
        
        text = parser.extract_text(str(pdf_path))
        
        assert text is not None
        assert len(text) > 0
        assert "TechCorp" in text or "Financial" in text


class TestExcelParser:
    """Test Excel parser."""
    
    def test_parse_excel(self, sample_docs_dir):
        """Test parsing an Excel document."""
        parser = ExcelParser()
        excel_path = sample_docs_dir / "financial_data_2023.xlsx"
        
        if not excel_path.exists():
            pytest.skip("Sample Excel not found")
        
        result = parser.parse(str(excel_path))
        
        assert result is not None
        assert "text" in result
        assert "sheets" in result
        assert "file_type" in result
        assert result["file_type"] == "excel"
        assert len(result["sheets"]) > 0
    
    def test_extract_text(self, sample_docs_dir):
        """Test extracting text from Excel."""
        parser = ExcelParser()
        excel_path = sample_docs_dir / "financial_data_2023.xlsx"
        
        if not excel_path.exists():
            pytest.skip("Sample Excel not found")
        
        text = parser.extract_text(str(excel_path))
        
        assert text is not None
        assert len(text) > 0


class TestWordParser:
    """Test Word parser."""
    
    def test_parse_word(self, sample_docs_dir):
        """Test parsing a Word document."""
        parser = WordParser()
        word_path = sample_docs_dir / "financial_report_q4.docx"
        
        if not word_path.exists():
            pytest.skip("Sample Word document not found")
        
        result = parser.parse(str(word_path))
        
        assert result is not None
        assert "text" in result
        assert "paragraphs" in result
        assert "file_type" in result
        assert result["file_type"] == "word"
    
    def test_extract_text(self, sample_docs_dir):
        """Test extracting text from Word."""
        parser = WordParser()
        word_path = sample_docs_dir / "financial_report_q4.docx"
        
        if not word_path.exists():
            pytest.skip("Sample Word document not found")
        
        text = parser.extract_text(str(word_path))
        
        assert text is not None
        assert len(text) > 0
        assert "TechCorp" in text or "Financial" in text
