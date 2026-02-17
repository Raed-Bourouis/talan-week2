"""
F360 – Financial Entity Extractor
Extracts structured entities from raw document text using regex + heuristics.
In production, this would be augmented with LLM-based extraction.
"""
from __future__ import annotations

import re
from typing import Any


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
    # Match patterns like: 1 234,56 €, €1,234.56, 1234.56 EUR, etc.
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

    # Deduplicate amounts
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

    # ── Counterparties (heuristic: look for company names) ──
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
