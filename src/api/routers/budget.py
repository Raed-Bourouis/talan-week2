"""
Budget API Router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from ..models import BudgetAnalysisRequest, BudgetAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=BudgetAnalysisResponse)
async def analyze_budget(request: BudgetAnalysisRequest):
    """
    Analyze budget for a specific department and year
    """
    try:
        # Mock response - in production, use actual BudgetAnalyzer
        response = BudgetAnalysisResponse(
            department_id=request.department_id,
            year=request.year,
            allocated=500000.0,
            spent=575000.0,
            remaining=-75000.0,
            variance=-75000.0,
            variance_percent=-15.0,
            status="over_budget",
            severity="warning",
            top_expenses=[
                {"category": "Marketing Campaigns", "amount": 250000, "percent": 43.5},
                {"category": "Events", "amount": 150000, "percent": 26.1},
                {"category": "Software", "amount": 100000, "percent": 17.4},
            ],
            recommendations=[
                "Immediate action required: Budget exceeded by 15%",
                "Review and approve any remaining non-critical expenses",
                "Consider requesting supplemental budget allocation"
            ]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{department_id}/{year}")
async def forecast_budget(department_id: str, year: int):
    """
    Forecast year-end budget position
    """
    try:
        # Mock response
        return {
            "department_id": department_id,
            "year": year,
            "current_spent": 575000.0,
            "projected_year_end": 750000.0,
            "projected_variance": -250000.0,
            "projected_variance_percent": -50.0,
            "months_remaining": 6,
            "confidence": "medium"
        }
        
    except Exception as e:
        logger.error(f"Error forecasting budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments")
async def list_departments():
    """
    List all departments with budget summary
    """
    try:
        # Mock response
        return {
            "departments": [
                {
                    "id": "DEPT001",
                    "name": "Marketing",
                    "budget_status": "over_budget",
                    "variance_percent": -15.0,
                    "allocated": 500000.0,
                    "spent": 575000.0
                },
                {
                    "id": "DEPT002",
                    "name": "R&D",
                    "budget_status": "under_budget",
                    "variance_percent": 10.0,
                    "allocated": 800000.0,
                    "spent": 720000.0
                },
                {
                    "id": "DEPT003",
                    "name": "Operations",
                    "budget_status": "on_track",
                    "variance_percent": 2.0,
                    "allocated": 600000.0,
                    "spent": 588000.0
                }
            ],
            "total_allocated": 1900000.0,
            "total_spent": 1883000.0,
            "overall_variance": 17000.0
        }
        
    except Exception as e:
        logger.error(f"Error listing departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))
