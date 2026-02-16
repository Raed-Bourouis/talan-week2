"""
Entity Extractor
Extract financial entities using LLMs (amounts, dates, parties, clauses)
"""

from typing import Dict, Any, List, Optional
import re
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract financial entities from documents using patterns and LLMs"""
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        
        # Regex patterns for entity extraction
        self.amount_pattern = re.compile(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
        self.date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{4}-\d{2}-\d{2})')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    
    def extract(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from parsed document
        
        Args:
            document: Parsed document dictionary
            
        Returns:
            Dictionary containing extracted entities
        """
        text_content = self._get_text_content(document)
        
        entities = {
            'amounts': self._extract_amounts(text_content),
            'dates': self._extract_dates(text_content),
            'contacts': self._extract_contacts(text_content),
            'parties': self._extract_parties(text_content),
            'terms': self._extract_payment_terms(text_content),
        }
        
        # Use LLM for advanced extraction if available
        if self.llm_client and document.get('file_type') == 'pdf':
            entities['llm_entities'] = self._llm_extract(text_content)
        
        logger.info(f"Extracted {len(entities['amounts'])} amounts, {len(entities['dates'])} dates")
        
        return entities
    
    def _get_text_content(self, document: Dict[str, Any]) -> str:
        """Extract text content from document"""
        if 'text_content' in document:
            return document['text_content']
        elif 'data' in document:
            # For CSV/Excel, convert to text
            return str(document['data'])
        return ''
    
    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts"""
        amounts = []
        for match in self.amount_pattern.finditer(text):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                amounts.append({
                    'value': amount,
                    'text': match.group(0),
                    'position': match.start()
                })
            except ValueError:
                continue
        return amounts
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates"""
        dates = []
        for match in self.date_pattern.finditer(text):
            date_str = match.group(0)
            dates.append({
                'text': date_str,
                'position': match.start()
            })
        return dates
    
    def _extract_contacts(self, text: str) -> Dict[str, List[str]]:
        """Extract contact information"""
        return {
            'emails': [m.group(0) for m in self.email_pattern.finditer(text)],
            'phones': [m.group(0) for m in self.phone_pattern.finditer(text)]
        }
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names (simple version)"""
        # Look for common patterns like "Company Name Inc." or "ABC Corp"
        party_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|LP|LLP|Co)\.?))\b')
        parties = [m.group(1) for m in party_pattern.finditer(text)]
        return list(set(parties))[:10]  # Return unique, limited
    
    def _extract_payment_terms(self, text: str) -> List[str]:
        """Extract payment terms"""
        terms_patterns = [
            r'Net\s+\d+',
            r'Due\s+(?:on|upon)\s+receipt',
            r'\d+%\s+discount',
            r'Payment\s+terms?:?\s+[^\n]+',
        ]
        
        terms = []
        for pattern in terms_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            terms.extend([m.group(0) for m in matches])
        
        return list(set(terms))[:5]
    
    def _llm_extract(self, text: str) -> Dict[str, Any]:
        """Use LLM for advanced entity extraction"""
        if not self.llm_client:
            return {}
        
        # Truncate text if too long
        max_length = 4000
        truncated_text = text[:max_length] if len(text) > max_length else text
        
        prompt = f"""Extract financial entities from the following document:

{truncated_text}

Extract:
1. Contract parties (supplier, client)
2. Key amounts and what they represent
3. Important dates (start, end, due dates)
4. Payment terms
5. Special clauses or conditions

Return as JSON structure."""

        try:
            # This would use the actual LLM client
            # For now, return empty dict
            return {
                'status': 'llm_extraction_placeholder',
                'note': 'Implement with actual LLM client'
            }
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return {}


def extract_entities(document: Dict[str, Any], llm_client: Optional[Any] = None) -> Dict[str, Any]:
    """Convenience function to extract entities"""
    extractor = EntityExtractor(llm_client)
    return extractor.extract(document)
