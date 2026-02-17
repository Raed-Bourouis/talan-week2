"""
F360 – Knowledge Graph Service (Neo4j)
Schema definition, population and query utilities.
"""
from __future__ import annotations

import uuid
from typing import Any

from app.core.neo4j_client import neo4j_session


# ═══════════════════════════════════════════════════════════════
# SCHEMA INITIALIZATION
# ═══════════════════════════════════════════════════════════════

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT budget_id IF NOT EXISTS FOR (b:Budget) REQUIRE b.id IS UNIQUE",
    "CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT client_id IF NOT EXISTS FOR (c:Client) REQUIRE c.id IS UNIQUE",
]


async def initialize_graph_schema() -> None:
    """Create uniqueness constraints on all node types."""
    async with neo4j_session() as session:
        for constraint in SCHEMA_CONSTRAINTS:
            await session.run(constraint)


# ═══════════════════════════════════════════════════════════════
# NODE CREATION
# ═══════════════════════════════════════════════════════════════

async def upsert_company(company_id: str, name: str, **props) -> None:
    async with neo4j_session() as session:
        await session.run(
            """
            MERGE (c:Company {id: $id})
            SET c.name = $name, c += $props
            """,
            id=company_id, name=name, props=props,
        )


async def upsert_contract(contract_id: str, reference: str, company_id: str, **props) -> None:
    async with neo4j_session() as session:
        await session.run(
            """
            MERGE (ct:Contract {id: $contract_id})
            SET ct.reference = $reference, ct += $props
            WITH ct
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:GENERATES]->(ct)
            """,
            contract_id=contract_id, reference=reference,
            company_id=company_id, props=props,
        )


async def upsert_invoice(
    invoice_id: str, invoice_number: str, company_id: str,
    contract_id: str | None = None, counterparty_id: str | None = None,
    **props,
) -> None:
    async with neo4j_session() as session:
        # Create invoice node
        await session.run(
            """
            MERGE (i:Invoice {id: $invoice_id})
            SET i.invoice_number = $invoice_number, i += $props
            WITH i
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:GENERATES]->(i)
            """,
            invoice_id=invoice_id, invoice_number=invoice_number,
            company_id=company_id, props=props,
        )
        # Link invoice to contract
        if contract_id:
            await session.run(
                """
                MATCH (ct:Contract {id: $contract_id})
                MATCH (i:Invoice {id: $invoice_id})
                MERGE (ct)-[:LINKS_TO]->(i)
                """,
                contract_id=contract_id, invoice_id=invoice_id,
            )
        # Link invoice to counterparty (supplier pays)
        if counterparty_id:
            await session.run(
                """
                MATCH (s {id: $counterparty_id})
                MATCH (i:Invoice {id: $invoice_id})
                MERGE (s)-[:PAYS]->(i)
                """,
                counterparty_id=counterparty_id, invoice_id=invoice_id,
            )


async def upsert_budget(budget_id: str, company_id: str, department_id: str | None = None, **props) -> None:
    async with neo4j_session() as session:
        await session.run(
            """
            MERGE (b:Budget {id: $budget_id})
            SET b += $props
            WITH b
            MATCH (c:Company {id: $company_id})
            MERGE (b)-[:BELONGS_TO]->(c)
            """,
            budget_id=budget_id, company_id=company_id, props=props,
        )
        if department_id:
            await session.run(
                """
                MATCH (b:Budget {id: $budget_id})
                MATCH (d:Department {id: $department_id})
                MERGE (b)-[:BELONGS_TO]->(d)
                """,
                budget_id=budget_id, department_id=department_id,
            )


async def upsert_supplier(supplier_id: str, name: str, company_id: str, **props) -> None:
    async with neo4j_session() as session:
        await session.run(
            """
            MERGE (s:Supplier {id: $supplier_id})
            SET s.name = $name, s += $props
            WITH s
            MATCH (c:Company {id: $company_id})
            MERGE (s)-[:BELONGS_TO]->(c)
            """,
            supplier_id=supplier_id, name=name, company_id=company_id, props=props,
        )


async def mark_budget_exceeded(budget_id: str, invoice_id: str) -> None:
    """Create an EXCEEDS edge when invoice spending surpasses budget."""
    async with neo4j_session() as session:
        await session.run(
            """
            MATCH (i:Invoice {id: $invoice_id})
            MATCH (b:Budget {id: $budget_id})
            MERGE (i)-[:EXCEEDS]->(b)
            """,
            invoice_id=invoice_id, budget_id=budget_id,
        )


# ═══════════════════════════════════════════════════════════════
# EXAMPLE CYPHER QUERIES
# ═══════════════════════════════════════════════════════════════

EXAMPLE_QUERIES = {
    "all_contracts_for_company": """
        MATCH (c:Company {id: $company_id})-[:GENERATES]->(ct:Contract)
        RETURN ct.reference AS reference, ct.title AS title, ct.total_amount AS amount
        ORDER BY ct.end_date
    """,
    "invoices_linked_to_contract": """
        MATCH (ct:Contract {id: $contract_id})-[:LINKS_TO]->(i:Invoice)
        RETURN i.invoice_number AS invoice, i.amount_ttc AS amount, i.status AS status
    """,
    "supplier_payment_history": """
        MATCH (s:Supplier {id: $supplier_id})-[:PAYS]->(i:Invoice)
        RETURN i.invoice_number AS invoice, i.amount_ttc AS amount,
               i.invoice_date AS date, i.status AS status
        ORDER BY i.invoice_date DESC
    """,
    "budget_overruns": """
        MATCH (i:Invoice)-[:EXCEEDS]->(b:Budget)
        RETURN b.category AS budget_category, b.planned_amount AS planned,
               collect(i.invoice_number) AS exceeding_invoices
    """,
    "contract_invoice_budget_path": """
        MATCH path = (c:Company)-[:GENERATES]->(ct:Contract)-[:LINKS_TO]->(i:Invoice)
        WHERE c.id = $company_id
        RETURN ct.reference AS contract, i.invoice_number AS invoice,
               i.amount_ttc AS amount
    """,
    "departments_over_budget": """
        MATCH (d:Department)<-[:BELONGS_TO]-(b:Budget)
        WHERE b.actual_amount > b.planned_amount
        RETURN d.name AS department, b.category AS category,
               b.planned_amount AS planned, b.actual_amount AS actual,
               round((b.actual_amount - b.planned_amount) / b.planned_amount * 100) AS deviation_pct
        ORDER BY deviation_pct DESC
    """,
}


async def run_graph_query(query_name: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a named graph query and return results as list of dicts."""
    cypher = EXAMPLE_QUERIES.get(query_name)
    if not cypher:
        raise ValueError(f"Unknown query: {query_name}. Available: {list(EXAMPLE_QUERIES.keys())}")

    async with neo4j_session() as session:
        result = await session.run(cypher, **(params or {}))
        records = await result.data()
        return records
