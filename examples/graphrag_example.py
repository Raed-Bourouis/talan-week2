"""
Simple integration example demonstrating GraphRAG usage.
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graphrag import (
    EpisodicMemory,
    Client,
    Contract,
    Invoice,
    BudgetEntry,
    ContractStatus,
    InvoiceStatus,
    FinancialEpisode,
    RAGQuery,
)


async def main():
    """Run a simple integration example."""
    
    print("=" * 70)
    print("GraphRAG Component - Integration Example")
    print("=" * 70)
    
    # ── Part 1: Episodic Memory ──
    print("\n1. Testing Episodic Memory")
    print("-" * 70)
    
    memory = EpisodicMemory()
    
    # Create and store episodes
    client_id = uuid4()
    
    episode1 = FinancialEpisode(
        title="Late payment detected",
        description="Client ABC paid invoice 15 days late",
        event_date=datetime.utcnow(),
        entities_involved=[client_id],
        event_type="late_payment",
        context={"delay_days": 15, "amount": 50000},
        tags=["payment", "risk"],
    )
    
    memory.store_episode(episode1)
    print(f"✓ Stored {len(memory._episodes)} episodes")
    
    # Recall similar episodes
    recalled = memory.recall_similar("payment issues", top_k=5)
    print(f"✓ Recalled {len(recalled)} episodes similar to 'payment issues'")
    
    # ── Part 2: Financial Entities ──
    print("\n2. Testing Financial Entity Models")
    print("-" * 70)
    
    # Create a client
    client = Client(
        name="Acme Corporation",
        company_name="Acme Corporation",
        contact_email="finance@acme.com",
        tax_id="FR12345678901",
        credit_rating="A",
    )
    print(f"✓ Created client: {client.company_name}")
    
    # Create a contract
    contract = Contract(
        name="Annual Support Contract 2024",
        reference="CTR-2024-001",
        title="Annual Software Support and Maintenance",
        client_id=client.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        total_amount=Decimal("120000.00"),
        currency="EUR",
        status=ContractStatus.ACTIVE,
    )
    print(f"✓ Created contract: {contract.reference} (Amount: €{contract.total_amount})")
    
    print("\n✓ All core components tested successfully!")


if __name__ == "__main__":
    asyncio.run(main())
