"""Entity extraction using local LLM via Ollama."""
import logging
from typing import Dict, Any, List, Optional
import json
import ollama
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FinancialEntity(BaseModel):
    """Financial entity model."""
    entity_type: str = Field(..., description="Type of entity (e.g., company, amount, date, person)")
    value: str = Field(..., description="The extracted value")
    context: Optional[str] = Field(None, description="Context in which the entity appears")
    confidence: Optional[float] = Field(None, description="Confidence score")


class EntityExtractor:
    """Extract entities from text using Ollama LLM."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        """Initialize entity extractor.
        
        Args:
            base_url: Ollama base URL
            model: Model name to use
        """
        self.base_url = base_url
        self.model = model
        self.client = None
        
    def _initialize_client(self):
        """Initialize Ollama client."""
        if self.client is None:
            try:
                # Test connection
                ollama.list()
                self.client = True
                logger.info(f"Connected to Ollama at {self.base_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise
    
    def extract_entities(self, text: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract entities from text.
        
        Args:
            text: Text to extract entities from
            entity_types: Optional list of entity types to extract
            
        Returns:
            List of extracted entities
        """
        try:
            self._initialize_client()
            
            if entity_types is None:
                entity_types = [
                    "company_name",
                    "monetary_amount",
                    "date",
                    "person_name",
                    "financial_metric",
                    "location"
                ]
            
            prompt = self._build_extraction_prompt(text, entity_types)
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            entities = self._parse_response(response['response'])
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def extract_financial_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial entities specifically.
        
        Args:
            text: Text to extract financial entities from
            
        Returns:
            List of extracted financial entities
        """
        financial_entity_types = [
            "company_name",
            "stock_symbol",
            "monetary_amount",
            "revenue",
            "profit",
            "loss",
            "financial_ratio",
            "date",
            "fiscal_year",
            "quarter"
        ]
        
        return self.extract_entities(text, financial_entity_types)
    
    def _build_extraction_prompt(self, text: str, entity_types: List[str]) -> str:
        """Build prompt for entity extraction."""
        entity_types_str = ", ".join(entity_types)
        
        prompt = f"""You are a financial document entity extractor. Extract the following types of entities from the text: {entity_types_str}

Text:
{text}

Extract all entities and return them in JSON format as a list. Each entity should have:
- entity_type: one of the types listed above
- value: the actual value extracted
- context: a brief context where it appears (optional)

Return ONLY a valid JSON array, nothing else. Example format:
[
  {{"entity_type": "company_name", "value": "Apple Inc.", "context": "quarterly report"}},
  {{"entity_type": "monetary_amount", "value": "$50 million", "context": "revenue"}}
]

JSON Response:"""
        
        return prompt
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract entities."""
        try:
            # Try to find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                entities = json.loads(json_str)
                return entities
            else:
                logger.warning("No JSON array found in response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return []
