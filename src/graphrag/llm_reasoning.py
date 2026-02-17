"""
GraphRAG LLM Reasoning Engine
==============================
LLM-based reasoning for financial analysis with chain-of-thought capabilities.
Provider-agnostic design supporting OpenAI, Mistral, and local models.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .config import GraphRAGConfig, get_config
from .exceptions import LLMReasoningError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ABSTRACT LLM PROVIDER
# ═══════════════════════════════════════════════════════════════

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Generate JSON-structured completion."""
        pass


# ═══════════════════════════════════════════════════════════════
# OPENAI PROVIDER
# ═══════════════════════════════════════════════════════════════

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion with OpenAI."""
        try:
            client = self._get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise LLMReasoningError(f"OpenAI generation failed: {e}")
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Generate JSON-structured completion with OpenAI."""
        try:
            client = self._get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        
        except Exception as e:
            raise LLMReasoningError(f"OpenAI JSON generation failed: {e}")


# ═══════════════════════════════════════════════════════════════
# LOCAL PROVIDER (Ollama, etc.)
# ═══════════════════════════════════════════════════════════════

class LocalLLMProvider(LLMProvider):
    """Local LLM provider (Ollama, LM Studio, etc.)."""
    
    def __init__(self, url: str, model: str = "mistral"):
        self.url = url
        self.model = model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion with local LLM."""
        try:
            import httpx
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False,
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        
        except Exception as e:
            raise LLMReasoningError(f"Local LLM generation failed: {e}")
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Generate JSON-structured completion with local LLM."""
        prompt_with_json = f"{prompt}\n\nRespond ONLY with valid JSON."
        content = await self.generate(
            prompt_with_json, system_prompt, temperature, max_tokens
        )
        
        try:
            # Try to extract JSON from response
            # Sometimes models add explanation before/after JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMReasoningError(f"Failed to parse JSON from local LLM: {e}")


# ═══════════════════════════════════════════════════════════════
# REASONING ENGINE
# ═══════════════════════════════════════════════════════════════

class ReasoningEngine:
    """
    LLM-powered reasoning engine for financial analysis.
    Supports chain-of-thought, multi-step reasoning, and structured insights.
    """
    
    SYSTEM_PROMPT = """You are F360, an AI-powered financial analyst assistant.
You analyze financial documents, contracts, invoices, budgets, and cashflow data.

Reasoning guidelines:
1. Base your answers ONLY on the provided context.
2. If context is insufficient, state explicitly what information is missing.
3. Always cite source documents when referencing specific data.
4. Use structured reasoning: identify key facts → analyze → conclude.
5. Provide actionable insights when possible.
6. Flag risks, anomalies, or opportunities in the data.
7. Respond in the same language as the question.

When analyzing financial data:
- Compare planned vs actual figures
- Identify trends and deviations
- Highlight contractual risks (penalties, indexation, expiry)
- Consider cashflow implications
- Reference historical patterns when available
"""
    
    def __init__(self, config: Optional[GraphRAGConfig] = None):
        self.config = config or get_config()
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider:
        """Create LLM provider based on configuration."""
        llm_config = self.config.get_llm_config()
        
        if llm_config["provider"] == "openai":
            if not llm_config.get("api_key"):
                raise LLMReasoningError("OpenAI API key not configured")
            return OpenAIProvider(
                api_key=llm_config["api_key"],
                model=llm_config["model"],
            )
        elif llm_config["provider"] == "local":
            return LocalLLMProvider(
                url=llm_config["url"],
                model=llm_config["model"],
            )
        else:
            raise LLMReasoningError(f"Unsupported LLM provider: {llm_config['provider']}")
    
    async def generate_answer(
        self,
        question: str,
        context: str,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate an answer to a financial question with context."""
        temp = temperature if temperature is not None else self.config.openai_temperature
        
        prompt = f"""Context:
{context}

Question: {question}

Provide a clear, well-reasoned answer based on the context above."""
        
        try:
            answer = await self.provider.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temp,
                max_tokens=self.config.openai_max_tokens,
            )
            return answer
        
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return self._fallback_answer(question, context)
    
    async def chain_of_thought(
        self,
        question: str,
        context: str,
        steps: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Multi-step chain-of-thought reasoning.
        Breaks down complex financial questions into analytical steps.
        """
        default_steps = [
            "Identify key facts from the context",
            "Analyze relationships and patterns",
            "Calculate relevant metrics",
            "Assess risks and opportunities",
            "Formulate actionable recommendation",
        ]
        
        reasoning_steps = steps or default_steps
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(reasoning_steps))
        
        prompt = f"""Analyze this financial question step by step.

Context:
{context}

Question: {question}

Follow these analytical steps and provide your reasoning for each:
{steps_text}

Respond as JSON with this structure:
{{
  "steps": [
    {{"step": "step description", "reasoning": "your analysis", "findings": ["key finding 1", "key finding 2"]}}
  ],
  "conclusion": "overall answer",
  "confidence": 0.0-1.0,
  "risks": ["identified risk 1"],
  "recommendations": ["recommendation 1"]
}}
"""
        
        try:
            result = await self.provider.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=self.config.openai_temperature,
                max_tokens=self.config.openai_max_tokens,
            )
            result["question"] = question
            return result
        
        except Exception as e:
            logger.error(f"Chain-of-thought reasoning failed: {e}")
            return {
                "question": question,
                "steps": [],
                "conclusion": self._fallback_answer(question, context),
                "error": str(e),
            }
    
    async def analyze_anomaly(
        self,
        data: dict[str, Any],
        expected: dict[str, Any],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze a financial anomaly or deviation."""
        prompt = f"""Analyze this financial anomaly:

Expected values:
{json.dumps(expected, indent=2, default=str)}

Actual values:
{json.dumps(data, indent=2, default=str)}

{f'Additional context: {context}' if context else ''}

Provide analysis as JSON:
{{
  "severity": "low|medium|high|critical",
  "deviations": [{{"metric": "...", "expected": ..., "actual": ..., "variance_pct": ...}}],
  "possible_causes": ["cause 1", "cause 2"],
  "impact_assessment": "description of potential impact",
  "recommended_actions": ["action 1", "action 2"]
}}
"""
        
        try:
            result = await self.provider.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=1500,
            )
            return result
        
        except Exception as e:
            logger.error(f"Anomaly analysis failed: {e}")
            return {
                "severity": "unknown",
                "error": str(e),
                "deviations": [],
                "possible_causes": [],
                "recommended_actions": [],
            }
    
    async def summarize_financial_period(
        self,
        period_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a summary of a financial period."""
        prompt = f"""Summarize this financial period:

Period Data:
{json.dumps(period_data, indent=2, default=str)}

Provide summary as JSON:
{{
  "period": "period identifier",
  "key_metrics": {{"metric": value}},
  "highlights": ["positive point 1"],
  "concerns": ["concerning point 1"],
  "trends": ["trend description 1"],
  "outlook": "brief outlook statement"
}}
"""
        
        try:
            result = await self.provider.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=1500,
            )
            return result
        
        except Exception as e:
            logger.error(f"Period summary failed: {e}")
            return {"period": "unknown", "error": str(e)}
    
    async def generate_recommendation(
        self,
        situation: str,
        options: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Generate financial recommendations for a given situation."""
        options_text = ""
        if options:
            options_text = "\n\nAvailable options:\n" + "\n".join(f"- {opt}" for opt in options)
        
        prompt = f"""Analyze this financial situation and provide recommendations:

Situation:
{situation}{options_text}

Provide recommendations as JSON:
{{
  "primary_recommendation": "main recommended action",
  "rationale": "explanation of why this is recommended",
  "alternatives": ["alternative 1", "alternative 2"],
  "pros": ["benefit 1"],
  "cons": ["drawback 1"],
  "estimated_impact": "description of expected impact",
  "confidence": 0.0-1.0
}}
"""
        
        try:
            result = await self.provider.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=1500,
            )
            return result
        
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {"primary_recommendation": "Unable to generate recommendation", "error": str(e)}
    
    def _fallback_answer(self, question: str, context: str) -> str:
        """Fallback answer when LLM is unavailable."""
        if not context:
            return "No relevant information found to answer the question."
        
        # Return truncated context as fallback
        max_context = 1500
        truncated = context[:max_context]
        if len(context) > max_context:
            truncated += "\n\n[Context truncated...]"
        
        return (
            f"Based on the available information:\n\n"
            f"{truncated}\n\n"
            f"(Note: Full AI analysis requires a properly configured LLM provider)"
        )
