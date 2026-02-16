"""
Contracts API Router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from ..models import ContractExpiryRequest, ContractExpiryResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/expiring", response_model=ContractExpiryResponse)
async def get_expiring_contracts(request: ContractExpiryRequest):
    """
    Get contracts expiring within specified days
    """
    try:
        # Mock response
        cutoff_date = datetime.now() + timedelta(days=request.days_ahead)
        
        contracts = [
            {
                "contract_id": "CONTRACT002",
                "name": "Office Supplies Framework",
                "supplier": "Office Solutions Ltd",
                "end_date": (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
                "days_until_expiry": 45,
                "value": 50000.0,
                "auto_renew": False,
                "urgency": "high"
            },
            {
                "contract_id": "CONTRACT003",
                "name": "Cloud Services Agreement",
                "supplier": "Cloud Provider Inc",
                "end_date": (datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d'),
                "days_until_expiry": 75,
                "value": 200000.0,
                "auto_renew": True,
                "urgency": "medium"
            }
        ]
        
        return ContractExpiryResponse(
            contracts=contracts,
            total_count=len(contracts),
            total_value=sum(c['value'] for c in contracts)
        )
        
    except Exception as e:
        logger.error(f"Error getting expiring contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contract_id}/clauses")
async def extract_contract_clauses(contract_id: str):
    """
    Extract and categorize contract clauses
    """
    try:
        # Mock response
        return {
            "contract_id": contract_id,
            "contract_name": "Annual Software License",
            "contract_value": 120000.0,
            "clauses": {
                "payment_terms": ["Net 30"],
                "auto_renewal": ["Auto-renewal clause active"],
                "price_indexation": ["Price indexation +3% annually"],
                "sla": ["SLA 99.9% uptime"],
                "penalties": [],
                "other": []
            },
            "risks": [
                {
                    "type": "auto_renewal",
                    "severity": "medium",
                    "description": "Contract has auto-renewal clause - requires proactive cancellation",
                    "recommendation": "Review 90 days before expiry"
                },
                {
                    "type": "price_increase",
                    "severity": "low",
                    "description": "Contract includes price indexation",
                    "recommendation": "Factor into next year budget planning"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error extracting clauses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supplier/{supplier_id}/performance")
async def get_supplier_performance(supplier_id: str):
    """
    Get supplier performance score
    """
    try:
        # Mock response
        return {
            "supplier_id": supplier_id,
            "performance_score": 85.3,
            "rating": "good",
            "total_invoices": 24,
            "on_time_invoices": 20,
            "late_invoices": 4,
            "on_time_percent": 83.3,
            "avg_days_late": 4.5,
            "total_contract_value": 288000.0
        }
        
    except Exception as e:
        logger.error(f"Error getting supplier performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_contracts(status: str = None):
    """
    List all contracts with optional status filter
    """
    try:
        # Mock response
        contracts = [
            {
                "contract_id": "CONTRACT001",
                "name": "Annual Software License",
                "supplier": "TechVendor Inc",
                "status": "active",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "value": 120000.0
            },
            {
                "contract_id": "CONTRACT002",
                "name": "Office Supplies Framework",
                "supplier": "Office Solutions Ltd",
                "status": "expiring_soon",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
                "value": 50000.0
            }
        ]
        
        if status:
            contracts = [c for c in contracts if c['status'] == status]
        
        return {
            "contracts": contracts,
            "total_count": len(contracts),
            "total_value": sum(c['value'] for c in contracts)
        }
        
    except Exception as e:
        logger.error(f"Error listing contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
