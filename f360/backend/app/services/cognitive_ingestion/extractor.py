"""
F360 – Cognitive Extractor
Entity extraction + enrichment from raw document text.
Combines regex heuristics with optional LLM-based extraction.
"""
from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# FINANCIAL ENTITY EXTRACTION (Regex + Heuristics)
# ═══════════════════════════════════════════════════════════════

def extract_financial_entities(text: str) -> dict[str, Any]:
    """
    Extract key financial entities from raw text:
    - Amounts (EUR)
    - Dates
    - Counterparties (heuristic)
    - Payment terms
    - Contract clauses (penalty, indexation)
    """
    entities: dict[str, Any] = {
        "amounts": [],
        "dates": [],
        "counterparties": [],
        "payment_terms": [],
        "penalty_clauses": [],
        "indexation_clauses": [],
    }

    # ── Amounts ──
    amount_patterns = [
        r"(\d[\d\s]*[\d](?:[.,]\d{2})?)\s*(?:€|EUR|euros?)",
        r"(?:€|EUR)\s*(\d[\d\s]*[\d](?:[.,]\d{2})?)",
        r"[Mm]ontant\s*(?::\s*|de\s+)(\d[\d\s]*[\d](?:[.,]\d{2})?)",
        r"[Tt]otal\s*(?::\s*|TTC\s*:\s*)(\d[\d\s]*[\d](?:[.,]\d{2})?)",
    ]
    for pattern in amount_patterns:
        for match in re.finditer(pattern, text):
            raw_amount = match.group(1).replace(" ", "").replace(",", ".")
            try:
                amount = float(raw_amount)
                if amount > 0:
                    entities["amounts"].append(amount)
            except ValueError:
                pass

    entities["amounts"] = sorted(set(entities["amounts"]), reverse=True)

    # ── Dates ──
    date_patterns = [
        r"(\d{2}[/.-]\d{2}[/.-]\d{4})",
        r"(\d{4}[/.-]\d{2}[/.-]\d{2})",
        r"(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})",
    ]
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities["dates"].append(match.group(1))

    entities["dates"] = list(set(entities["dates"]))

    # ── Payment Terms ──
    payment_patterns = [
        r"(?:paiement|règlement|payment)\s*(?:à|:)?\s*([\w\s]+(?:jours?|days?))",
        r"(net\s+\d+\s*(?:jours?|days?))",
        r"(\d+\s*(?:jours?|days?)\s*(?:date\s+de\s+facture|fin\s+de\s+mois))",
    ]
    for pattern in payment_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities["payment_terms"].append(match.group(1).strip())

    # ── Penalty Clauses ──
    penalty_patterns = [
        r"((?:pénalité|penalty|indemnité)[^.]*\.)",
        r"((?:clause\s+pénale|liquidated\s+damages)[^.]*\.)",
        r"((?:retard|late\s+payment)[^.]*(?:intérêt|interest|pénalité|penalty)[^.]*\.)",
    ]
    for pattern in penalty_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities["penalty_clauses"].append(match.group(1).strip())

    # ── Indexation Clauses ──
    indexation_patterns = [
        r"((?:indexation|indexé|indexed|révision)[^.]*(?:inflation|CPI|IPC|indice|index)[^.]*\.)",
        r"((?:inflation|CPI|IPC)[^.]*(?:clause|ajustement|adjustment)[^.]*\.)",
    ]
    for pattern in indexation_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities["indexation_clauses"].append(match.group(1).strip())

    # ── Counterparties ──
    company_patterns = [
        r"(?:société|company|fournisseur|supplier|client|prestataire)\s*(?::\s*)?([A-Z][\w\s&.-]{2,50}(?:SAS|SARL|SA|SNC|EURL|GmbH|Ltd|Inc|Corp)?)",
    ]
    for pattern in company_patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if len(name) > 2:
                entities["counterparties"].append(name)

    entities["counterparties"] = list(set(entities["counterparties"]))

    return entities


# ═══════════════════════════════════════════════════════════════
# LLM-ENHANCED EXTRACTION
# ═══════════════════════════════════════════════════════════════

async def extract_entities_with_llm(text: str, entity_types: list[str] | None = None) -> dict[str, Any]:
    """
    Use LLM for advanced entity extraction when regex is insufficient.
    Handles complex/unstructured documents with higher accuracy.
    Falls back to regex extraction if LLM is unavailable.
    """
    from app.core.config import get_settings
    settings = get_settings()

    # Always start with regex extraction
    entities = extract_financial_entities(text)

    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
        return entities

    try:
        from openai import AsyncOpenAI
        import json

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        prompt = f"""Analyze this financial document and extract structured entities.
Return a JSON object with these keys:
- amounts: list of monetary amounts (as numbers)
- dates: list of dates found
- counterparties: list of company/person names
- payment_terms: list of payment conditions
- penalty_clauses: list of penalty clause descriptions
- indexation_clauses: list of indexation clause descriptions  
- key_terms: list of important contractual terms
- risk_indicators: list of identified risks

Document text (first 3000 chars):
{text[:3000]}
"""
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a financial document analyst. Extract entities as JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        llm_entities = json.loads(response.choices[0].message.content)

        # Merge LLM results with regex results (deduplicated)
        for key in ["amounts", "counterparties", "payment_terms", "penalty_clauses", "indexation_clauses"]:
            if key in llm_entities:
                existing = set(map(str, entities.get(key, [])))
                for item in llm_entities[key]:
                    if str(item) not in existing:
                        entities[key].append(item)

        # Add LLM-only fields
        entities["key_terms"] = llm_entities.get("key_terms", [])
        entities["risk_indicators"] = llm_entities.get("risk_indicators", [])

        logger.info(f"LLM extraction enriched entities for document")
        return entities

    except Exception as e:
        logger.warning(f"LLM extraction failed, using regex only: {e}")
        return entities
