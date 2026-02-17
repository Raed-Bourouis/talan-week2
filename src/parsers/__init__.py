"""Document parsers for PDF, Excel, and Word files."""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseParser:
    """Base class for document parsers."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a document and return its content."""
        raise NotImplementedError("Subclasses must implement parse method")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from a document."""
        raise NotImplementedError("Subclasses must implement extract_text method")
