"""
F360 – Tests: Entity Extractor
"""
import pytest
from app.services.ingestion.entity_extractor import extract_financial_entities


class TestAmountExtraction:
    def test_euro_amounts(self):
        text = "Le montant total est de 150 000,50 € TTC."
        result = extract_financial_entities(text)
        assert len(result["amounts"]) > 0

    def test_eur_suffix(self):
        text = "Total: 25000 EUR"
        result = extract_financial_entities(text)
        assert len(result["amounts"]) > 0

    def test_multiple_amounts(self):
        text = "Montant HT: 10000 € – TVA: 2000 € – Total TTC: 12000 €"
        result = extract_financial_entities(text)
        assert len(result["amounts"]) >= 2


class TestDateExtraction:
    def test_french_date(self):
        text = "Date de facturation: 15/03/2026"
        result = extract_financial_entities(text)
        assert "15/03/2026" in result["dates"]

    def test_iso_date(self):
        text = "Échéance: 2026-04-30"
        result = extract_financial_entities(text)
        assert "2026-04-30" in result["dates"]


class TestPaymentTerms:
    def test_payment_days(self):
        text = "Paiement à 30 jours date de facture."
        result = extract_financial_entities(text)
        assert len(result["payment_terms"]) > 0


class TestPenaltyClauses:
    def test_penalty_detection(self):
        text = "En cas de retard, une pénalité de 3% par mois sera appliquée."
        result = extract_financial_entities(text)
        assert len(result["penalty_clauses"]) > 0


class TestIndexationClauses:
    def test_inflation_indexation(self):
        text = "Le prix est indexé sur l'indice d'inflation CPI publié par l'INSEE."
        result = extract_financial_entities(text)
        assert len(result["indexation_clauses"]) > 0
