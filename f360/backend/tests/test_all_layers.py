"""
F360 – Test complet des 7 couches avec données réelles
=======================================================
Utilise les données de Input/ (CSV gouv, PDF contrats, CUAD)
pour tester chaque layer SANS dépendance à PostgreSQL/Neo4j/OpenAI.

Usage:
    cd f360/backend
    python tests/test_all_layers.py
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# ── Fix path ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent          # f360/backend
sys.path.insert(0, str(ROOT))

INPUT_DIR  = ROOT.parent.parent / "Input"              # TASK_2/Input
GOV_DIR    = INPUT_DIR / "data_economie_gouv"
CONTRACTS_DIR = INPUT_DIR / "Contracts_30_English"

# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def ok(msg: str):
    print(f"  [OK] {msg}")

def fail(msg: str):
    print(f"  [FAIL] {msg}")

def info(msg: str):
    print(f"  [INFO] {msg}")


def read_csv_semicolon(path: Path, max_rows: int = 100) -> list[dict]:
    """Read a semicolon-separated CSV (format data.economie.gouv.fr)."""
    if not path.exists():
        info(f"File not found: {path}")
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)
    return rows


def read_csv_comma(path: Path, max_rows: int = 100) -> list[dict]:
    """Read a comma-separated CSV."""
    if not path.exists():
        info(f"File not found: {path}")
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)
    return rows


# ════════════════════════════════════════════════════════════════
# LAYER 1 – Sources Multimodales
# ════════════════════════════════════════════════════════════════

def test_layer1_parsers():
    """Test PDF and CSV parsing with real data."""
    section("LAYER 1 - Sources Multimodales (parsers)")

    from app.services.sources.parsers import parse_pdf, parse_excel

    # 1a) Parse a real PDF contract
    pdf_path = CONTRACTS_DIR / "Contract_1.pdf"
    if pdf_path.exists():
        raw = pdf_path.read_bytes()
        text = parse_pdf(raw)   # returns str
        assert isinstance(text, str), "parse_pdf should return a str"
        assert len(text) > 100, f"PDF text too short: {len(text)} chars"
        has_amount = any(kw in text.lower() for kw in ["$", "amount", "financed", "payment"])
        assert has_amount, "PDF should contain financial amounts"
        ok(f"PDF parsed: {len(text)} chars, financial terms found")
    else:
        info(f"PDF not found: {pdf_path} -- skipping")

    # 1b) Parse government CSV
    csv_path = GOV_DIR / "plf_2026_budget_vert.csv"
    if csv_path.exists():
        raw = csv_path.read_bytes()
        text = parse_excel(raw, "csv")   # returns str
        assert isinstance(text, str), "parse_excel should return a str"
        assert len(text) > 200, f"CSV text too short: {len(text)} chars"
        ok(f"CSV (Budget Vert) parsed: {len(text)} chars")
    else:
        info(f"CSV not found: {csv_path} -- skipping")

    # 1c) Parse performance CSV
    perf_path = GOV_DIR / "performance_depense_rap.csv"
    if perf_path.exists():
        raw = perf_path.read_bytes()
        text = parse_excel(raw, "csv")
        assert len(text) > 100
        ok(f"CSV (Performance RAP) parsed: {len(text)} chars")

    return True


def test_layer1_connectors():
    """Test connector instantiation and mock fetch."""
    section("LAYER 1 - Sources Multimodales (connectors)")

    from app.services.sources.connectors import (
        CONNECTOR_REGISTRY,
        get_connector,
        S3Connector,
    )

    assert len(CONNECTOR_REGISTRY) == 4, f"Expected 4 connectors, got {len(CONNECTOR_REGISTRY)}"
    ok(f"Connector registry: {list(CONNECTOR_REGISTRY.keys())}")

    # Instantiate each connector with mock config
    for name, cls in CONNECTOR_REGISTRY.items():
        conn = cls({"endpoint": "test", "bucket": "test"})
        assert conn is not None
    ok("All 4 connectors instantiated successfully")

    # Test factory
    conn = get_connector("s3", {"endpoint": "mock"})
    assert isinstance(conn, S3Connector)
    ok("get_connector factory works")

    return True


def test_layer1_iot_logger():
    """Test IoT/Log event collection and anomaly detection."""
    section("LAYER 1 - Sources Multimodales (IoT/Logs)")

    from app.services.sources.iot_logger import IoTLogCollector

    collector = IoTLogCollector()

    # Simulate IoT events from budget data
    budget_data = read_csv_semicolon(GOV_DIR / "situations_mensuelles_budgetaires.csv", max_rows=26)
    iot_ingested = 0
    for i, row in enumerate(budget_data[:10]):
        values = [v for k, v in row.items()
                  if k not in ("Niveau hiérarchique", "Niveau hiérarchique de la ligne",
                               "Catégorie", "Sous-catégorie", "Ligne d'information")]
        for j, val_str in enumerate(values[:3]):
            try:
                val = float(val_str.replace(",", ".").replace(" ", ""))
                collector.ingest_iot({
                    "device_id": f"budget_sensor_{i}",
                    "event_type": "budget_execution",
                    "value": val / 1e9,
                    "unit": "milliards EUR",
                })
                iot_ingested += 1
            except (ValueError, AttributeError):
                pass

    ok(f"Ingested {iot_ingested} IoT events from budget data")

    # Log events
    for level in ["INFO", "WARNING", "ERROR", "INFO", "INFO"]:
        collector.ingest_log({
            "source": "f360_budget_module",
            "level": level,
            "message": f"Budget gap detected: {level}",
        })
    log_count = len(collector.flush_logs())
    ok(f"Ingested {log_count} log events")

    # Add more events for anomaly detection (need >= 10)
    for i in range(20):
        collector.ingest_iot({
            "device_id": "cashflow_monitor",
            "event_type": "cashflow_amount",
            "value": 100.0 + (i * 2),
            "unit": "kEUR",
        })
    # Inject anomalies
    collector.ingest_iot({"device_id": "cashflow_monitor", "event_type": "cashflow_amount", "value": 500.0})
    collector.ingest_iot({"device_id": "cashflow_monitor", "event_type": "cashflow_amount", "value": -200.0})

    anomalies = collector.detect_anomalies()
    ok(f"Anomaly detection: {len(anomalies)} anomalies found")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 2 – Cognitive Ingestion
# ════════════════════════════════════════════════════════════════

def test_layer2_extractor():
    """Test entity extraction from real contract text."""
    section("LAYER 2 - Cognitive Ingestion (extractor)")

    from app.services.cognitive_ingestion.extractor import extract_financial_entities

    # Read a real contract PDF or use fallback
    pdf_path = CONTRACTS_DIR / "Contract_1.pdf"
    if pdf_path.exists():
        from app.services.sources.parsers import parse_pdf
        text = parse_pdf(pdf_path.read_bytes())
    else:
        text = (
            "Car Financing Agreement. "
            "Borrower: Carlos Brown, Boston MA, SSN 360132173. "
            "Lender: FINANCIAL BANK OF AMERICA Inc., EIN 00-0000000, New York NY. "
            "Financed Amount: $82,437.00. "
            "Term: 60 months from 2024-01-15 to 2029-01-15. "
            "Interest Rate: 1.2% monthly. "
            "Penalty for default: 2% of overdue amount + 1% per month. "
            "Payment due on the 15th of each month."
        )

    entities = extract_financial_entities(text)
    assert isinstance(entities, dict), "Should return a dict"

    ok(f"Amounts found:        {len(entities.get('amounts', []))}")
    ok(f"Dates found:          {len(entities.get('dates', []))}")
    ok(f"Counterparties found: {len(entities.get('counterparties', []))}")
    ok(f"Payment terms found:  {len(entities.get('payment_terms', []))}")
    ok(f"Penalties found:      {len(entities.get('penalty_clauses', []))}")
    ok(f"Indexation found:     {len(entities.get('indexation_clauses', []))}")

    total = sum(len(v) for v in entities.values() if isinstance(v, list))
    assert total > 0, "Should extract at least some entities from contract text"
    ok(f"Entity extraction validated: {total} total entities")

    return True


def test_layer2_vectorizer():
    """Test text chunking (no OpenAI embedding)."""
    section("LAYER 2 - Cognitive Ingestion (vectorizer)")

    from app.services.cognitive_ingestion.vectorizer import chunk_text

    # Use government CSV as text input
    csv_path = GOV_DIR / "performance_depense_rap.csv"
    if csv_path.exists():
        text = csv_path.read_text(encoding="utf-8")[:5000]
    else:
        text = "Budget performance review text. " * 200

    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    assert isinstance(chunks, list), "Should return a list of chunks"
    assert len(chunks) > 1, f"Should produce multiple chunks, got {len(chunks)}"

    for i, chunk in enumerate(chunks[:3]):
        ok(f"Chunk {i+1}: {len(chunk)} chars")

    ok(f"Text chunked into {len(chunks)} chunks (size=1000, overlap=200)")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 3 – RAGraph (reasoning only, no DB/LLM)
# ════════════════════════════════════════════════════════════════

def test_layer3_episodic_memory():
    """Test episodic memory storage and recall (in-memory only)."""
    section("LAYER 3 - RAGraph (episodic memory)")

    from app.services.ragraph.episodic_memory import EpisodicMemory, Episode

    memory = EpisodicMemory()

    # Store episodes from real budget data -- context_sources must be list[dict]
    budget_rows = read_csv_semicolon(GOV_DIR / "situations_mensuelles_budgetaires.csv", max_rows=26)
    episodes_stored = 0
    for row in budget_rows[:5]:
        cat = row.get("Catégorie", row.get("Cat\u00e9gorie", "Budget"))
        line = row.get("Ligne d'information", row.get("Ligne d\u2019information", "N/A"))
        ep = Episode(
            query=f"Quel est le solde budgetaire pour {cat} - {line} ?",
            answer=f"Les donnees montrent: {list(row.values())[-3:]}",
            context_sources=[{"type": "csv", "file": "situations_mensuelles_budgetaires.csv"}],
            feedback_score=0.85,
            tags=["budget", "execution", cat.lower()[:20]],
        )
        asyncio.run(memory.store(ep))  # store is async
        episodes_stored += 1

    ok(f"Stored {episodes_stored} episodes from budget data")

    # Recall
    recalled = asyncio.run(memory.recall(query="solde budgetaire", top_k=3))
    assert len(recalled) > 0, "Should recall at least one episode"
    ok(f"Recalled {len(recalled)} episodes for 'solde budgetaire'")

    # Context generation
    context = memory.get_context_for_query(recalled)
    assert len(context) > 0, "Context string should not be empty"
    ok(f"Generated context: {len(context)} chars")

    return True


def test_layer3_reasoning():
    """Test reasoning engine fallback (rule-based, no LLM)."""
    section("LAYER 3 - RAGraph (reasoning engine)")

    from app.services.ragraph.reasoning import ReasoningEngine

    engine = ReasoningEngine()

    # Test rule-based analysis with real RAP data
    rap_rows = read_csv_semicolon(GOV_DIR / "performance_depense_rap.csv", max_rows=20)
    data_points = []
    for row in rap_rows[:10]:
        data_points.append({
            "label": f"{row.get('Mission', 'N/A')} / {row.get('Programme', 'N/A')}",
            "values": {k: v for k, v in row.items()},
        })

    if data_points:
        result = engine._rule_based_analysis(data_points, "performance")
        assert isinstance(result, dict), "Should return a dict"
        ok(f"Rule-based analysis: {len(result)} fields")
        for k, v in result.items():
            if isinstance(v, str):
                info(f"  {k}: {v[:80]}...")
            elif isinstance(v, list):
                info(f"  {k}: {len(v)} items")
            else:
                info(f"  {k}: {v}")
    else:
        info("No RAP data available, testing with synthetic data")
        result = engine._rule_based_analysis(
            [{"label": "Test", "value": 100}], "budget"
        )
        ok(f"Rule-based analysis (synthetic): {len(result)} fields")

    # Test fallback answer
    answer = engine._fallback_answer(
        "What is the budget performance for 2024?",
        "Budget data shows 443B EUR total expenditure."
    )
    assert isinstance(answer, str) and len(answer) > 10
    ok(f"Fallback answer: {len(answer)} chars")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 4 – Real-Time Feedback
# ════════════════════════════════════════════════════════════════

def test_layer4_gap_calculator():
    """Test gap calculation with real budget data."""
    section("LAYER 4 - Real-Time Feedback (gap calculator)")

    from app.services.realtime_feedback.gap_calculator import GapResult

    # Load real budget execution data
    budget_rows = read_csv_semicolon(GOV_DIR / "situations_mensuelles_budgetaires.csv", 26)

    gaps = []
    for row in budget_rows:
        cat = row.get("Catégorie", row.get("Cat\u00e9gorie", ""))
        line = row.get("Ligne d'information", "")
        values = [v for k, v in row.items()
                  if k not in ("Niveau hiérarchique", "Niveau hiérarchique de la ligne",
                               "Catégorie", "Sous-catégorie", "Ligne d'information")]
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v.replace(",", ".").replace(" ", "")))
            except (ValueError, AttributeError):
                pass

        if len(numeric_values) >= 2:
            predicted = numeric_values[-2]
            actual = numeric_values[-1]
            if predicted != 0:
                gap = GapResult(
                    entity_type="budget",
                    entity_id=None,
                    label=f"{cat} / {line}",
                    predicted=predicted,
                    actual=actual,
                )
                gaps.append(gap)

    ok(f"Computed {len(gaps)} gaps from real budget execution data")

    # Analyze severities
    severities: dict[str, int] = {}
    for g in gaps:
        sev = g.severity
        severities[sev] = severities.get(sev, 0) + 1

    for sev, count in sorted(severities.items()):
        info(f"  {sev}: {count} gaps")

    # Top 5 gaps
    sorted_gaps = sorted(gaps, key=lambda g: abs(g.gap_pct), reverse=True)
    info("  Top 5 deviations:")
    for g in sorted_gaps[:5]:
        info(f"    {g.label[:50]}: {g.gap_pct:+.1f}% ({g.severity})")

    return True


def test_layer4_feedback_classifier():
    """Test feedback classification rules."""
    section("LAYER 4 - Real-Time Feedback (classifier)")

    from app.services.realtime_feedback.reindexer import FeedbackReindexer
    from app.services.realtime_feedback.gap_calculator import GapResult

    reindexer = FeedbackReindexer()

    test_cases = [
        ("OPEX under 5%",   "budget", 1000000, 1050000),
        ("CAPEX over 15%",  "budget", 500000,  425000),
        ("HR deviated 25%", "budget", 2000000, 1500000),
        ("IT deviated 40%", "budget", 800000,  480000),
    ]

    for label, entity_type, predicted, actual in test_cases:
        gap = GapResult(
            entity_type=entity_type,
            entity_id=None,
            label=label,
            predicted=predicted,
            actual=actual,
        )
        event = reindexer._classify_gap(gap)
        ok(f"{label}: gap={gap.gap_pct:+.1f}% -> action={event.action}, reward={event.reward:.2f}")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 5 – Simulation
# ════════════════════════════════════════════════════════════════

def test_layer5_budget_simulation():
    """Test budget variation simulation with real parameters."""
    section("LAYER 5 - Simulation (budget variation)")

    from app.services.simulation.parallel_engine import ParallelSimulationEngine

    engine = ParallelSimulationEngine()

    result = engine.run("budget_variation", {
        "base_budget": 443_413_251_207,
        "variation_pct": [-10, -5, 0, 5, 10],
        "categories": ["OPEX", "CAPEX", "HR", "IT", "Marketing"],
    })

    assert isinstance(result, dict), "Should return a dict"
    assert len(result) > 0, "Should have result keys"
    ok(f"Budget variation simulation: {len(result)} result keys")
    for k, v in list(result.items())[:8]:
        if isinstance(v, (int, float)):
            info(f"  {k}: {v:,.2f}")
        else:
            info(f"  {k}: {v}")

    return True


def test_layer5_cashflow_simulation():
    """Test cashflow projection simulation."""
    section("LAYER 5 - Simulation (cashflow projection)")

    from app.services.simulation.parallel_engine import ParallelSimulationEngine

    engine = ParallelSimulationEngine()

    result = engine.run("cashflow_projection", {
        "initial_balance": 50_000_000,
        "daily_inflow_mean": 2_500_000,
        "daily_outflow_mean": 2_300_000,
        "volatility": 0.15,
        "horizon_days": 90,
    })

    assert isinstance(result, dict), "Should return a dict"
    ok(f"Cashflow projection: {len(result)} result keys")
    for k, v in list(result.items())[:5]:
        if isinstance(v, (int, float)):
            info(f"  {k}: {v:,.2f}")
        elif isinstance(v, list):
            info(f"  {k}: {len(v)} entries")
        else:
            info(f"  {k}: {v}")

    return True


def test_layer5_monte_carlo():
    """Test Monte Carlo simulation."""
    section("LAYER 5 - Simulation (Monte Carlo)")

    from app.services.simulation.parallel_engine import ParallelSimulationEngine

    engine = ParallelSimulationEngine()

    result = engine.run("monte_carlo", {
        "base_value": 100_000_000,
        "mean_return": 0.08,
        "volatility": 0.20,
        "horizon_years": 1,
        "iterations": 10_000,
    })

    assert isinstance(result, dict), "Should return a dict"
    ok(f"Monte Carlo: {len(result)} result keys")

    for k in ["mean", "median", "p5", "p25", "p75", "p95", "probability_of_loss", "var_95"]:
        if k in result:
            val = result[k]
            if isinstance(val, float) and abs(val) > 1:
                info(f"  {k}: {val:,.2f}")
            else:
                info(f"  {k}: {val}")

    return True


def test_layer5_renegotiation():
    """Test contract renegotiation simulation."""
    section("LAYER 5 - Simulation (renegotiation)")

    from app.services.simulation.parallel_engine import ParallelSimulationEngine

    engine = ParallelSimulationEngine()

    result = engine.run("renegotiation", {
        "current_annual_cost": 82_437 * 12 / 60,
        "contract_duration_years": 5,
        "proposed_discount_pct": 8.0,
        "inflation_rate": 0.03,
        "exit_penalty": 5000,
    })

    assert isinstance(result, dict), "Should return a dict"
    ok(f"Renegotiation: {len(result)} result keys")
    for k, v in list(result.items())[:8]:
        if isinstance(v, (int, float)):
            info(f"  {k}: {v:,.2f}")
        else:
            info(f"  {k}: {v}")

    return True


def test_layer5_parallel():
    """Test parallel execution of multiple scenarios."""
    section("LAYER 5 - Simulation (parallel)")

    from app.services.simulation.parallel_engine import ParallelSimulationEngine

    engine = ParallelSimulationEngine()

    scenarios = [
        {"simulation_type": "monte_carlo", "parameters": {
            "base_value": 1_000_000, "mean_return": 0.05,
            "volatility": 0.15, "horizon_years": 1, "iterations": 1000}},
        {"simulation_type": "monte_carlo", "parameters": {
            "base_value": 1_000_000, "mean_return": 0.10,
            "volatility": 0.25, "horizon_years": 1, "iterations": 1000}},
        {"simulation_type": "monte_carlo", "parameters": {
            "base_value": 1_000_000, "mean_return": -0.02,
            "volatility": 0.30, "horizon_years": 1, "iterations": 1000}},
    ]

    results = engine.run_parallel(scenarios)
    assert len(results) == 3, f"Should have 3 results, got {len(results)}"
    ok(f"Parallel execution: {len(results)} scenarios completed")

    for i, r in enumerate(results):
        if isinstance(r, dict) and "mean" in r:
            info(f"  Scenario {i+1}: mean={r['mean']:,.2f}, VaR95={r.get('var_95', 'N/A')}")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 6 – Decision Fusion
# ════════════════════════════════════════════════════════════════

def test_layer6_aggregator():
    """Test multi-source signal aggregation with real data."""
    section("LAYER 6 - Decision Fusion (aggregator)")

    from app.services.decision_fusion.aggregator import MultiSourceAggregator, Signal

    aggregator = MultiSourceAggregator()

    # Build signals from real budget data
    budget_rows = read_csv_semicolon(GOV_DIR / "situations_mensuelles_budgetaires.csv", 26)
    signal_count = 0
    for row in budget_rows[:8]:
        cat = row.get("Catégorie", row.get("Cat\u00e9gorie", "budget"))
        values = [v for k, v in row.items()
                  if k not in ("Niveau hiérarchique", "Niveau hiérarchique de la ligne",
                               "Catégorie", "Sous-catégorie", "Ligne d'information")]
        nums = []
        for v in values:
            try:
                nums.append(float(v.replace(",", ".").replace(" ", "")))
            except (ValueError, AttributeError):
                pass
        if len(nums) >= 2:
            gap_pct = ((nums[-1] - nums[-2]) / abs(nums[-2]) * 100) if nums[-2] != 0 else 0
            direction = "negative" if gap_pct < 0 else "positive"
            aggregator.add_signal(Signal(
                source="feedback",
                topic=f"budget_{cat.lower()[:20]}",
                value=gap_pct / 100,
                confidence=0.85,
                direction=direction,
                timestamp=datetime.now(timezone.utc),
            ))
            signal_count += 1

    # Simulation signals
    aggregator.add_signal(Signal(
        source="simulation", topic="cashflow_30d",
        value=-0.12, confidence=0.70, direction="negative",
    ))
    aggregator.add_signal(Signal(
        source="simulation", topic="budget_depenses",
        value=0.05, confidence=0.75, direction="positive",
    ))
    signal_count += 2

    ok(f"Added {signal_count} signals from real budget data + simulation")

    result = aggregator.aggregate()
    assert isinstance(result, dict), "Should return a dict"
    ok(f"Aggregation result: {len(result)} keys")

    if "topics" in result:
        info(f"  Topics aggregated: {len(result['topics'])}")
        for topic, topic_info in list(result["topics"].items())[:5]:
            score = topic_info["score"] if isinstance(topic_info, dict) else topic_info
            info(f"    {topic}: score={score}")

    if "conflicts" in result:
        info(f"  Conflicts detected: {len(result['conflicts'])}")

    if "overall_score" in result:
        info(f"  Overall score: {result['overall_score']:.3f}")

    return True


def test_layer6_tactical():
    """Test tactical decision generation."""
    section("LAYER 6 - Decision Fusion (tactical decisions)")

    from app.services.decision_fusion.tactical import TacticalDecisionEngine

    engine = TacticalDecisionEngine()

    # Feed with realistic gap data
    gaps = [
        {"entity_type": "budget", "entity_id": None, "label": "OPEX", "category": "OPEX",
         "predicted": 5000000, "actual": 5800000, "gap_pct": 16.0, "severity": "warning"},
        {"entity_type": "budget", "entity_id": None, "label": "CAPEX", "category": "CAPEX",
         "predicted": 2000000, "actual": 2900000, "gap_pct": 45.0, "severity": "critical"},
        {"entity_type": "budget", "entity_id": None, "label": "HR",
         "predicted": 3000000, "actual": 2850000, "gap_pct": -5.0, "severity": "nominal"},
        {"entity_type": "cashflow", "entity_id": None, "label": "cashflow_Q4",
         "predicted": 1000000, "actual": 600000, "gap_pct": -40.0, "severity": "alert"},
    ]

    simulation_results = [
        {"type": "monte_carlo", "probability_of_loss": 0.35, "var_95": -250000,
         "mean": 1050000, "risk_assessment": "elevated"},
    ]

    result = asyncio.run(engine.generate_decisions(
        gaps=gaps,
        simulation_results=simulation_results,
    ))

    assert isinstance(result, dict), "Should return a dict"
    decisions = result.get("decisions", [])
    ok(f"Generated {len(decisions)} tactical decisions")

    for d in decisions[:5]:
        if isinstance(d, dict):
            info(f"  [{d.get('priority', '?')}] {d.get('title', 'N/A')[:60]}")
        else:
            info(f"  {d}")

    return True


# ════════════════════════════════════════════════════════════════
# LAYER 7 – Recommendation
# ════════════════════════════════════════════════════════════════

def test_layer7_weak_signals():
    """Test weak signal detection with real data patterns."""
    section("LAYER 7 - Recommendation (weak signals)")

    from app.services.recommendation.weak_signals import (
        WeakSignalCorrelator,
        WeakSignal,
        signal_from_budget_drift,
        signal_from_cashflow_anomaly,
        signal_from_contract_expiry,
        signal_from_rag_insight,
    )

    correlator = WeakSignalCorrelator()

    # Build signals from PLF Budget Vert
    vert_rows = read_csv_semicolon(GOV_DIR / "plf_2026_budget_vert.csv", max_rows=50)
    vert_signals = 0
    for row in vert_rows:
        cotation = row.get("Cotation globale", "")
        mission = row.get("Mission", "")
        if "favorab" in cotation.lower() and "d" in cotation.lower()[:2]:
            correlator.add_signal(WeakSignal(
                source="budget_vert",
                category="ESG_risk",
                description=f"Budget vert defavorable: {mission[:50]}",
                strength=0.6,
                timestamp=datetime.now(timezone.utc),
                metadata={"cotation": cotation, "mission": mission},
            ))
            vert_signals += 1

    # Budget drift signals
    correlator.add_signal(signal_from_budget_drift("OPEX", 18.5))
    correlator.add_signal(signal_from_budget_drift("CAPEX", 32.0))
    correlator.add_signal(signal_from_budget_drift("IT", 12.0))

    # Cashflow anomaly
    correlator.add_signal(signal_from_cashflow_anomaly("Cashflow drop detected Q4", 25.0))

    # Contract expiry
    correlator.add_signal(signal_from_contract_expiry("Capgemini", 30, 500000))
    correlator.add_signal(signal_from_contract_expiry("Sopra Steria", 45, 250000))

    # RAG insight
    correlator.add_signal(signal_from_rag_insight(
        "Multiple contracts show penalty clause activation risk", 0.72
    ))

    ok(f"Total signals: {correlator.signal_count} ({vert_signals} from budget vert)")

    # Detect correlations
    correlations = correlator.detect_correlations()
    ok(f"Correlations detected: {len(correlations)}")

    for c in correlations[:5]:
        info(f"  [{c.risk_type}] strength={c.combined_strength:.2f}: {c.narrative[:60]}...")

    return True


def test_layer7_recommendation_engine():
    """Test recommendation engine with mock budget objects."""
    section("LAYER 7 - Recommendation (engine)")

    from app.services.recommendation.engine import RecommendationEngine

    engine = RecommendationEngine()

    # Create mock budget objects that mimic the ORM Budget model
    class MockBudget:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    company_id = uuid.uuid4()
    budgets = [
        MockBudget(
            id=uuid.uuid4(), company_id=company_id,
            fiscal_year=2025, category="OPEX",
            planned_amount=Decimal("5000000"), actual_amount=Decimal("5900000"),
            currency="EUR",
        ),
        MockBudget(
            id=uuid.uuid4(), company_id=company_id,
            fiscal_year=2025, category="CAPEX",
            planned_amount=Decimal("2000000"), actual_amount=Decimal("3100000"),
            currency="EUR",
        ),
        MockBudget(
            id=uuid.uuid4(), company_id=company_id,
            fiscal_year=2025, category="HR",
            planned_amount=Decimal("3000000"), actual_amount=Decimal("2800000"),
            currency="EUR",
        ),
        MockBudget(
            id=uuid.uuid4(), company_id=company_id,
            fiscal_year=2025, category="IT",
            planned_amount=Decimal("1000000"), actual_amount=Decimal("600000"),
            currency="EUR",
        ),
    ]

    recos = asyncio.run(engine.analyze_budgets(budgets, company_id))
    ok(f"Generated {len(recos)} recommendations")

    for r in recos:
        info(f"  [{r.severity}] {r.title[:60]}")
        info(f"    Action: {r.suggested_action[:60]}...")

    return True


# ════════════════════════════════════════════════════════════════
# INTEGRATION: Full Pipeline (L1 -> L7)
# ════════════════════════════════════════════════════════════════

def test_integration_pipeline():
    """End-to-end pipeline using real data through all layers."""
    section("INTEGRATION - Full Pipeline L1 -> L7")

    from app.services.sources.parsers import parse_pdf, parse_excel
    from app.services.cognitive_ingestion.extractor import extract_financial_entities
    from app.services.cognitive_ingestion.vectorizer import chunk_text
    from app.services.ragraph.episodic_memory import EpisodicMemory, Episode
    from app.services.ragraph.reasoning import ReasoningEngine
    from app.services.realtime_feedback.gap_calculator import GapResult
    from app.services.realtime_feedback.reindexer import FeedbackReindexer
    from app.services.simulation.parallel_engine import ParallelSimulationEngine
    from app.services.decision_fusion.aggregator import MultiSourceAggregator, Signal
    from app.services.decision_fusion.tactical import TacticalDecisionEngine
    from app.services.recommendation.weak_signals import (
        WeakSignalCorrelator, signal_from_budget_drift, signal_from_cashflow_anomaly,
    )

    # -- L1: Parse PDF contract --
    info("L1: Parsing PDF contract...")
    pdf_path = CONTRACTS_DIR / "Contract_1.pdf"
    if pdf_path.exists():
        text = parse_pdf(pdf_path.read_bytes())
    else:
        text = "Car Financing Agreement. Amount: $82,437. Term: 60 months. Interest: 1.2%/month."
    ok(f"L1 -> {len(text)} chars extracted")

    # -- L2: Extract entities + chunk --
    info("L2: Extracting entities & chunking...")
    entities = extract_financial_entities(text)
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    ok(f"L2 -> {len(entities.get('amounts', []))} amounts, {len(chunks)} chunks")

    # -- L3: Store in episodic memory + reason --
    info("L3: Episodic memory + reasoning...")
    memory = EpisodicMemory()
    ep = Episode(
        query="Analyse du contrat Contract_1.pdf",
        answer=f"Entites: {json.dumps(entities, default=str)[:200]}",
        context_sources=[{"type": "pdf", "file": "Contract_1.pdf"}],
        feedback_score=0.8,
    )
    asyncio.run(memory.store(ep))

    reasoning = ReasoningEngine()
    analysis = reasoning._rule_based_analysis(
        [{"label": "Contract_1", "amounts": entities.get("amounts", []),
          "penalties": entities.get("penalty_clauses", [])}],
        "contract"
    )
    ok(f"L3 -> Episode stored, analysis: {len(analysis)} fields")

    # -- L4: Compute gaps --
    info("L4: Computing budget gaps...")
    gaps = [
        GapResult(entity_type="budget", entity_id=None, label="OPEX", predicted=5000000, actual=5900000),
        GapResult(entity_type="budget", entity_id=None, label="CAPEX", predicted=2000000, actual=3100000),
        GapResult(entity_type="budget", entity_id=None, label="IT", predicted=1000000, actual=600000),
    ]
    reindexer = FeedbackReindexer()
    events = [reindexer._classify_gap(g) for g in gaps]
    ok(f"L4 -> {len(gaps)} gaps, actions: {[e.action for e in events]}")

    # -- L5: Run simulation --
    info("L5: Running Monte Carlo simulation...")
    sim_engine = ParallelSimulationEngine()
    sim_result = sim_engine.run("monte_carlo", {
        "base_value": 5000000, "mean_return": 0.05,
        "volatility": 0.20, "horizon_years": 1, "iterations": 5000,
    })
    ok(f"L5 -> MC mean={sim_result.get('mean', 0):,.0f}, P(loss)={sim_result.get('probability_of_loss', 0):.1%}")

    # -- L6: Fusion --
    info("L6: Aggregating signals...")
    aggregator = MultiSourceAggregator()
    for g in gaps:
        aggregator.add_signal(Signal(
            source="feedback", topic=f"gap_{g.label}",
            value=g.gap_pct / 100, confidence=0.85,
            direction="negative" if g.gap_pct > 10 else "positive",
        ))
    aggregator.add_signal(Signal(
        source="simulation", topic="mc_result",
        value=sim_result.get("mean", 0) / 5000000 - 1,
        confidence=0.70, direction="positive",
    ))
    agg_result = aggregator.aggregate()

    tactical = TacticalDecisionEngine()
    gap_dicts = [g.to_dict() for g in gaps]
    decision_result = asyncio.run(tactical.generate_decisions(
        gaps=gap_dicts,
        simulation_results=[sim_result],
    ))
    decisions = decision_result.get("decisions", [])
    ok(f"L6 -> {len(decisions)} tactical decisions")

    # -- L7: Weak signals + recommendations --
    info("L7: Weak signals & recommendations...")
    correlator = WeakSignalCorrelator()
    correlator.add_signal(signal_from_budget_drift("OPEX", gaps[0].gap_pct))
    correlator.add_signal(signal_from_budget_drift("CAPEX", gaps[1].gap_pct))
    correlator.add_signal(signal_from_cashflow_anomaly("IT under-execution", abs(gaps[2].gap_pct)))
    correlations = correlator.detect_correlations()
    ok(f"L7 -> {correlator.signal_count} signals, {len(correlations)} correlations")

    # Final summary
    print(f"\n{'~'*70}")
    print(f"  PIPELINE COMPLETE: L1 -> L7 all layers functional")
    print(f"     Data: Contract PDF + Gov Budget CSV -> Entities -> Chunks")
    print(f"     -> Memory -> Gaps -> Simulation -> Fusion -> Weak Signals")
    print(f"{'~'*70}")

    return True


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

ALL_TESTS = [
    # Layer 1
    ("L1.1 Parsers",            test_layer1_parsers),
    ("L1.2 Connectors",         test_layer1_connectors),
    ("L1.3 IoT/Logs",           test_layer1_iot_logger),
    # Layer 2
    ("L2.1 Extractor",          test_layer2_extractor),
    ("L2.2 Vectorizer",         test_layer2_vectorizer),
    # Layer 3
    ("L3.1 Episodic Memory",    test_layer3_episodic_memory),
    ("L3.2 Reasoning",          test_layer3_reasoning),
    # Layer 4
    ("L4.1 Gap Calculator",     test_layer4_gap_calculator),
    ("L4.2 Feedback Classifier", test_layer4_feedback_classifier),
    # Layer 5
    ("L5.1 Budget Sim",         test_layer5_budget_simulation),
    ("L5.2 Cashflow Sim",       test_layer5_cashflow_simulation),
    ("L5.3 Monte Carlo",        test_layer5_monte_carlo),
    ("L5.4 Renegotiation",      test_layer5_renegotiation),
    ("L5.5 Parallel Exec",      test_layer5_parallel),
    # Layer 6
    ("L6.1 Aggregator",         test_layer6_aggregator),
    ("L6.2 Tactical Decisions", test_layer6_tactical),
    # Layer 7
    ("L7.1 Weak Signals",       test_layer7_weak_signals),
    ("L7.2 Reco Engine",        test_layer7_recommendation_engine),
    # Integration
    ("INTEGRATION Pipeline",    test_integration_pipeline),
]


def main():
    print("\n" + "#" * 70)
    print("  F360 - TEST COMPLET DES 7 COUCHES")
    print("  Donnees: Input/ (PDF contrats, CSV gov, Budget, RAP, CUAD)")
    print("#" * 70)

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            fail(f"{name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*70}")
    print(f"  RESULTAT: {passed} PASSED / {failed} FAILED / {len(ALL_TESTS)} TOTAL")
    print(f"{'='*70}")

    if errors:
        print("\n  Echecs:")
        for name, err in errors:
            print(f"    [FAIL] {name}: {err[:100]}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
