"""
Cash Flow API Router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from ..models import CashFlowForecastRequest, CashFlowForecastResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/forecast", response_model=CashFlowForecastResponse)
async def forecast_cash_flow(request: CashFlowForecastRequest):
    """
    Forecast cash flow for specified days
    """
    try:
        # Generate mock forecast
        forecast = []
        running_balance = 1000000.0
        
        for i in range(min(request.days, 10)):  # Return first 10 days as sample
            date = datetime.now() + timedelta(days=i)
            daily_inflow = 80000.0 + (i * 1000)
            daily_outflow = 75000.0 + (i * 800)
            net_flow = daily_inflow - daily_outflow
            running_balance += net_flow
            
            forecast.append({
                "date": date.strftime('%Y-%m-%d'),
                "predicted_inflow": round(daily_inflow, 2),
                "predicted_outflow": round(daily_outflow, 2),
                "net_flow": round(net_flow, 2),
                "balance": round(running_balance, 2),
                "confidence_low": round(running_balance * 0.9, 2),
                "confidence_high": round(running_balance * 1.1, 2)
            })
        
        tensions = []
        if running_balance < 500000:
            tensions.append({
                "date": forecast[-1]['date'],
                "type": "low_balance",
                "severity": "medium",
                "balance": running_balance,
                "description": f"Cash balance projected at ${running_balance:,.0f}"
            })
        
        return CashFlowForecastResponse(
            forecast_days=request.days,
            generated_at=datetime.now().isoformat(),
            forecast=forecast,
            tensions=tensions,
            recommendations=[
                "Cash flow forecast looks healthy",
                "Monitor large upcoming payments",
                "Consider accelerating receivables collection"
            ]
        )
        
    except Exception as e:
        logger.error(f"Error forecasting cash flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-invoices")
async def get_pending_invoices():
    """
    Get pending invoices (receivables and payables)
    """
    try:
        # Mock response
        return {
            "receivables": [
                {
                    "invoice_id": "INV-REC-001",
                    "client": "Enterprise Customer",
                    "amount": 50000.0,
                    "due_date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                    "status": "pending",
                    "probability": 0.9
                },
                {
                    "invoice_id": "INV-REC-002",
                    "client": "Corp Client",
                    "amount": 75000.0,
                    "due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    "status": "pending",
                    "probability": 0.85
                }
            ],
            "payables": [
                {
                    "invoice_id": "INV-PAY-001",
                    "supplier": "TechVendor Inc",
                    "amount": 45000.0,
                    "due_date": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "invoice_id": "INV-PAY-002",
                    "supplier": "Office Solutions Ltd",
                    "amount": 30000.0,
                    "due_date": (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
                    "status": "pending",
                    "priority": "medium"
                }
            ],
            "total_receivables": 125000.0,
            "total_payables": 75000.0,
            "net_position": 50000.0
        }
        
    except Exception as e:
        logger.error(f"Error getting pending invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aging")
async def get_invoice_aging():
    """
    Get invoice aging analysis
    """
    try:
        # Mock response
        return {
            "aging_buckets": [
                {"bucket": "Current (0-30 days)", "count": 15, "amount": 375000.0},
                {"bucket": "31-60 days", "count": 8, "amount": 200000.0},
                {"bucket": "61-90 days", "count": 3, "amount": 75000.0},
                {"bucket": "Over 90 days", "count": 2, "amount": 50000.0}
            ],
            "total_outstanding": 700000.0,
            "average_days_outstanding": 42.5,
            "oldest_invoice_days": 125
        }
        
    except Exception as e:
        logger.error(f"Error getting aging analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monte-carlo")
async def run_monte_carlo_simulation(days: int = 90, simulations: int = 1000):
    """
    Run Monte Carlo simulation for cash flow
    """
    try:
        # Mock response
        return {
            "parameters": {
                "num_simulations": simulations,
                "days": days,
                "initial_balance": 1000000.0
            },
            "summary": {
                "mean_final_balance": 1050000.0,
                "p10_final_balance": 850000.0,
                "p50_final_balance": 1045000.0,
                "p90_final_balance": 1250000.0,
                "probability_negative": 2.5
            },
            "risks": [
                {
                    "date": (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
                    "risk_level": "medium",
                    "p10_balance": 450000.0,
                    "description": "10th percentile balance: $450,000"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error running Monte Carlo simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
