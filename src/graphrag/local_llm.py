"""
Local LLM using Ollama
100% FREE - No API keys required!
"""

from typing import Optional, Dict, Any, List
import requests
import json
import logging
import os

logger = logging.getLogger(__name__)


class LocalFinancialLLM:
    """
    Free local LLM using Ollama.
    No API keys needed - runs completely locally!
    """
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: Optional[str] = None,
        temperature: float = 0.1
    ):
        """
        Initialize local LLM.
        
        Args:
            model: Ollama model name (llama3.1:8b, mistral:7b, phi3:3b)
            base_url: Ollama server URL
            temperature: Temperature for generation (0.0 = deterministic, 1.0 = creative)
        """
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature
        logger.info(f"Initialized LocalLLM with model: {model} at {self.base_url}")
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            
        Returns:
            Generated text
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens
            }
        }
        
        if stop:
            payload["stop"] = stop
        
        try:
            logger.debug(f"Generating with prompt: {prompt[:100]}...")
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def extract_contract_clauses(self, contract_text: str) -> Dict[str, Any]:
        """
        Extract financial clauses from contract text.
        
        Args:
            contract_text: Raw contract text
            
        Returns:
            Structured dict with extracted clauses
        """
        prompt = f"""You are a financial analyst. Extract key clauses from this contract and return ONLY valid JSON.

Contract Text:
{contract_text[:2000]}  # Limit length

Extract the following information and return as JSON:
{{
    "payment_terms": "payment schedule and terms",
    "contract_value": "total contract value",
    "renewal_clause": "auto-renewal terms if any",
    "termination_clause": "termination conditions",
    "penalties": "penalty clauses for breach",
    "expiration_date": "contract end date",
    "key_obligations": ["list of main obligations"]
}}

Return ONLY the JSON object, no additional text."""

        try:
            response = self.generate(prompt, temperature=0.1)
            # Try to parse JSON from response
            # Sometimes LLM adds extra text, so we extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                logger.warning("Could not extract JSON from response")
                return {"raw_response": response}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {"error": "Failed to parse", "raw_response": response}
        except Exception as e:
            logger.error(f"Error extracting clauses: {e}")
            return {"error": str(e)}
    
    def extract_financial_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract financial entities from text.
        
        Args:
            text: Financial document text
            
        Returns:
            Dict with extracted entities
        """
        prompt = f"""Extract financial entities from this text and return ONLY valid JSON.

Text:
{text[:1500]}

Extract and return as JSON:
{{
    "amounts": [list of monetary amounts with context],
    "dates": [list of important dates with context],
    "parties": [list of parties/entities mentioned],
    "account_numbers": [any account or reference numbers],
    "categories": [budget categories or expense types]
}}

Return ONLY the JSON object."""

        try:
            response = self.generate(prompt, temperature=0.1)
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"raw_response": response}
        except json.JSONDecodeError:
            return {"error": "Failed to parse", "raw_response": response}
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"error": str(e)}
    
    def answer_financial_query(self, query: str, context: str) -> str:
        """
        Answer a financial query using provided context.
        
        Args:
            query: User's question
            context: Retrieved context from GraphRAG
            
        Returns:
            Natural language answer
        """
        prompt = f"""You are a financial intelligence assistant. Answer the user's question based on the provided context.

Context:
{context}

Question: {query}

Provide a clear, detailed financial analysis. Include specific numbers, dates, and entities from the context.
If you cannot answer based on the context, say so clearly.

Answer:"""

        return self.generate(prompt, temperature=0.2)
    
    def generate_recommendation(
        self,
        situation: str,
        data: str
    ) -> str:
        """
        Generate tactical recommendation for a financial situation.
        
        Args:
            situation: Description of the situation
            data: Relevant financial data
            
        Returns:
            Recommendation text
        """
        prompt = f"""You are a financial advisor. Based on the situation and data provided, give actionable recommendations.

Situation:
{situation}

Data:
{data}

Provide:
1. Analysis of the current situation
2. Specific actionable recommendations
3. Expected impact and risks

Recommendation:"""

        return self.generate(prompt, temperature=0.3)
    
    def analyze_pattern(self, pattern_data: str) -> str:
        """
        Analyze a financial pattern and provide insights.
        
        Args:
            pattern_data: Historical pattern data
            
        Returns:
            Analysis and recommendations
        """
        prompt = f"""Analyze this financial pattern and provide insights:

Pattern Data:
{pattern_data}

What pattern do you see? Provide:
1. Pattern description
2. Confidence level
3. Recommendation for action

Analysis:"""

        return self.generate(prompt, temperature=0.2)
    
    def check_health(self) -> bool:
        """
        Check if Ollama server is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# Singleton instance
_llm_instance = None


def get_llm(
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> LocalFinancialLLM:
    """
    Get or create singleton LLM instance.
    
    Args:
        model: Model name to use
        base_url: Ollama base URL
        
    Returns:
        LocalFinancialLLM instance
    """
    global _llm_instance
    if _llm_instance is None:
        model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        _llm_instance = LocalFinancialLLM(model=model, base_url=base_url)
    return _llm_instance
