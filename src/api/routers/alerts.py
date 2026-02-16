"""
Alerts API Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

from ..models import Alert, AlertListResponse, AlertSeverity, AlertType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by type")
):
    """
    List all alerts with optional filters
    """
    try:
        # Mock alerts
        alerts = [
            Alert(
                id=1,
                type=AlertType.budget,
                severity=AlertSeverity.high,
                title="Marketing Budget Exceeded",
                description="Marketing department is 15% over budget",
                entity_type="department",
                entity_id="DEPT001",
                status="active",
                created_at=datetime.now()
            ),
            Alert(
                id=2,
                type=AlertType.contract,
                severity=AlertSeverity.medium,
                title="Contract Expiring Soon",
                description="Office Supplies Framework expires in 45 days",
                entity_type="contract",
                entity_id="CONTRACT002",
                status="active",
                created_at=datetime.now()
            ),
            Alert(
                id=3,
                type=AlertType.payment,
                severity=AlertSeverity.low,
                title="Late Payment Detected",
                description="Invoice INV-2024-001 paid 6 days late",
                entity_type="invoice",
                entity_id="INV001",
                status="active",
                created_at=datetime.now()
            ),
            Alert(
                id=4,
                type=AlertType.risk,
                severity=AlertSeverity.medium,
                title="Supplier Risk Alert",
                description="Supplier risk score increased to 0.65",
                entity_type="supplier",
                entity_id="SUPP003",
                status="active",
                created_at=datetime.now()
            )
        ]
        
        # Apply filters
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]
        
        active_count = sum(1 for a in alerts if a.status == "active")
        
        return AlertListResponse(
            alerts=alerts,
            total_count=len(alerts),
            active_count=active_count
        )
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: int):
    """
    Get specific alert by ID
    """
    try:
        # Mock response
        alert = Alert(
            id=alert_id,
            type=AlertType.budget,
            severity=AlertSeverity.high,
            title="Marketing Budget Exceeded",
            description="Marketing department is 15% over budget. Immediate action required.",
            entity_type="department",
            entity_id="DEPT001",
            status="active",
            created_at=datetime.now()
        )
        
        return alert
        
    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """
    Mark alert as resolved
    """
    try:
        # Mock response
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_at": datetime.now().isoformat(),
            "message": "Alert marked as resolved"
        }
        
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/by-type")
async def get_alerts_summary():
    """
    Get alert summary grouped by type and severity
    """
    try:
        # Mock response
        return {
            "by_type": {
                "budget": 5,
                "contract": 3,
                "payment": 8,
                "risk": 2,
                "compliance": 1
            },
            "by_severity": {
                "critical": 2,
                "high": 4,
                "medium": 9,
                "low": 4
            },
            "total_active": 19,
            "total_resolved_today": 5,
            "requires_immediate_attention": 6
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies/detect")
async def detect_anomalies():
    """
    Run anomaly detection on financial data
    """
    try:
        # Mock response
        return {
            "anomalies": [
                {
                    "type": "duplicate_invoice",
                    "severity": "high",
                    "description": "Potential duplicate invoices: INV-2024-045 and INV-2024-046",
                    "invoice_ids": ["INV-2024-045", "INV-2024-046"],
                    "amount": 15000.0,
                    "detected_at": datetime.now().isoformat()
                },
                {
                    "type": "unusual_amount",
                    "severity": "medium",
                    "description": "Invoice INV-2024-050 has unusually high amount",
                    "invoice_id": "INV-2024-050",
                    "amount": 250000.0,
                    "detected_at": datetime.now().isoformat()
                }
            ],
            "total_anomalies": 2,
            "high_severity": 1,
            "medium_severity": 1
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
