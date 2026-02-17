"""
F360 – LLM & Raisonnement (Reasoning Engine)
Advanced reasoning chains for financial analysis.
Supports multi-step reasoning, chain-of-thought, and structured output.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ReasoningEngine:
    """
    LLM-powered reasoning engine for financial analysis.
    Implements:
    - Chain-of-thought reasoning
    - Multi-step analysis
    - Structured financial insights generation
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
"""

    async def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using LLM with chain-of-thought reasoning."""
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return self._fallback_answer(question, context)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question}",
                    },
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"LLM reasoning failed: {e}")
            return self._fallback_answer(question, context)

    async def chain_of_thought(
        self,
        question: str,
        context: str,
        steps: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Multi-step chain-of-thought reasoning.
        Breaking complex financial questions into analytical steps.
        """
        default_steps = [
            "Identify key facts from the context",
            "Analyze relationships and patterns",
            "Calculate relevant metrics",
            "Assess risks and opportunities",
            "Formulate actionable recommendation",
        ]
        reasoning_steps = steps or default_steps

        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return {
                "question": question,
                "steps": [{"step": s, "result": "LLM unavailable"} for s in reasoning_steps],
                "conclusion": self._fallback_answer(question, context),
            }

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)

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
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            result["question"] = question
            return result

        except Exception as e:
            logger.warning(f"Chain-of-thought reasoning failed: {e}")
            return {
                "question": question,
                "steps": [],
                "conclusion": self._fallback_answer(question, context),
                "error": str(e),
            }

    async def comparative_analysis(
        self,
        data_points: list[dict[str, Any]],
        analysis_type: str = "budget",
    ) -> dict[str, Any]:
        """
        Structured comparative analysis for financial data points.
        Types: budget, contract, cashflow, performance.
        """
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return self._rule_based_analysis(data_points, analysis_type)

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)

            prompt = f"""Perform a {analysis_type} comparative analysis on these data points:

{json.dumps(data_points, indent=2, default=str)}

Provide:
1. Summary of key differences
2. Trend analysis
3. Anomaly detection
4. Risk assessment
5. Recommendations

Respond as JSON with keys: summary, trends, anomalies, risks, recommendations.
"""
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.warning(f"Comparative analysis failed: {e}")
            return self._rule_based_analysis(data_points, analysis_type)

    # ── Fallback / Rule-based ──

    def _fallback_answer(self, question: str, context: str) -> str:
        """Fallback when OpenAI is not available."""
        if not context:
            return "No relevant documents found for your query."
        return (
            f"Based on the retrieved documents, here is the relevant context:\n\n"
            f"{context[:1500]}\n\n"
            f"(Note: Full AI analysis requires a valid OpenAI API key)"
        )

    def _rule_based_analysis(
        self, data_points: list[dict[str, Any]], analysis_type: str,
    ) -> dict[str, Any]:
        """Rule-based analysis when LLM is unavailable."""
        if not data_points:
            return {"summary": "No data points provided", "trends": [], "anomalies": [], "risks": [], "recommendations": []}

        # Simple statistical analysis
        numeric_keys = [k for k, v in data_points[0].items() if isinstance(v, (int, float))]
        trends = []
        anomalies = []

        for key in numeric_keys:
            values = [dp.get(key, 0) for dp in data_points if isinstance(dp.get(key), (int, float))]
            if len(values) >= 2:
                avg = sum(values) / len(values)
                trend = "increasing" if values[-1] > values[0] else "decreasing"
                trends.append({"metric": key, "trend": trend, "average": round(avg, 2)})

                # Flag outliers
                import statistics
                if len(values) >= 3:
                    stdev = statistics.stdev(values)
                    for i, v in enumerate(values):
                        if abs(v - avg) > 2 * stdev:
                            anomalies.append({"metric": key, "index": i, "value": v, "expected": round(avg, 2)})

        return {
            "summary": f"Analysis of {len(data_points)} {analysis_type} data points",
            "trends": trends,
            "anomalies": anomalies,
            "risks": [a for a in anomalies],
            "recommendations": [f"Review {a['metric']} at index {a['index']}" for a in anomalies],
        }
