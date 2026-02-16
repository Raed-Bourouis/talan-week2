"""
Document Parser
Multi-format parser for financial documents (PDF, Excel, CSV)
"""

from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parse various financial document formats"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.xlsx', '.xls', '.csv', '.txt', '.docx']
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a document and extract structured content
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing parsed content and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {extension}")
        
        logger.info(f"Parsing document: {file_path.name}")
        
        if extension == '.pdf':
            return self._parse_pdf(file_path)
        elif extension in ['.xlsx', '.xls']:
            return self._parse_excel(file_path)
        elif extension == '.csv':
            return self._parse_csv(file_path)
        elif extension == '.txt':
            return self._parse_text(file_path)
        elif extension == '.docx':
            return self._parse_docx(file_path)
        else:
            raise ValueError(f"Parser not implemented for: {extension}")
    
    def _parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Parse PDF document"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(file_path))
            text_content = []
            
            for page in reader.pages:
                text_content.append(page.extract_text())
            
            full_text = '\n'.join(text_content)
            
            return {
                'file_name': file_path.name,
                'file_type': 'pdf',
                'file_path': str(file_path),
                'num_pages': len(reader.pages),
                'text_content': full_text,
                'metadata': {
                    'author': reader.metadata.get('/Author', '') if reader.metadata else '',
                    'title': reader.metadata.get('/Title', '') if reader.metadata else '',
                }
            }
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Parse Excel document"""
        try:
            import pandas as pd
            
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets_data[sheet_name] = {
                    'data': df.to_dict('records'),
                    'columns': list(df.columns),
                    'row_count': len(df)
                }
            
            return {
                'file_name': file_path.name,
                'file_type': 'excel',
                'file_path': str(file_path),
                'sheets': sheets_data,
                'sheet_names': excel_file.sheet_names,
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error parsing Excel {file_path}: {e}")
            raise
    
    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV document"""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            
            return {
                'file_name': file_path.name,
                'file_type': 'csv',
                'file_path': str(file_path),
                'data': df.to_dict('records'),
                'columns': list(df.columns),
                'row_count': len(df),
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            raise
    
    def _parse_text(self, file_path: Path) -> Dict[str, Any]:
        """Parse plain text document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            return {
                'file_name': file_path.name,
                'file_type': 'text',
                'file_path': str(file_path),
                'text_content': text_content,
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error parsing text {file_path}: {e}")
            raise
    
    def _parse_docx(self, file_path: Path) -> Dict[str, Any]:
        """Parse Word document"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            return {
                'file_name': file_path.name,
                'file_type': 'docx',
                'file_path': str(file_path),
                'text_content': '\n'.join(paragraphs),
                'num_paragraphs': len(paragraphs),
                'metadata': {
                    'author': doc.core_properties.author or '',
                    'title': doc.core_properties.title or '',
                }
            }
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise


def parse_document(file_path: str) -> Dict[str, Any]:
    """Convenience function to parse a document"""
    parser = DocumentParser()
    return parser.parse(file_path)
