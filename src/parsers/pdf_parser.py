"""PDF document parser."""
import logging
from typing import Dict, Any, List
import PyPDF2
import pdfplumber

from . import BaseParser

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF documents."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a PDF document and extract structured data."""
        try:
            text = self.extract_text(file_path)
            metadata = self._extract_metadata(file_path)
            tables = self._extract_tables(file_path)
            
            return {
                "text": text,
                "metadata": metadata,
                "tables": tables,
                "file_type": "pdf"
            }
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF document."""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata
                
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "pages": len(pdf_reader.pages)
                }
        except Exception as e:
            logger.warning(f"Error extracting metadata from PDF {file_path}: {e}")
            return {}
    
    def _extract_tables(self, file_path: str) -> List[List[List[str]]]:
        """Extract tables from PDF."""
        try:
            tables = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            return tables
        except Exception as e:
            logger.warning(f"Error extracting tables from PDF {file_path}: {e}")
            return []
