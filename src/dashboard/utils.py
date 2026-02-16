"""
Dashboard Utility Functions
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')


def get_api_health() -> Dict[str, Any]:
    """Get API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def query_financial_data(question: str) -> Dict[str, Any]:
    """Query financial data using natural language"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"question": question},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_budget_analysis(department_id: str, year: int) -> Dict[str, Any]:
    """Get budget analysis for department"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/budget/analyze",
            json={"department_id": department_id, "year": year},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_departments() -> Dict[str, Any]:
    """Get list of departments"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/budget/departments", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_expiring_contracts(days_ahead: int = 90) -> Dict[str, Any]:
    """Get expiring contracts"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/contracts/expiring",
            json={"days_ahead": days_ahead},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_contract_clauses(contract_id: str) -> Dict[str, Any]:
    """Get contract clauses"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/contracts/{contract_id}/clauses",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_cash_flow_forecast(days: int = 90) -> Dict[str, Any]:
    """Get cash flow forecast"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/cashflow/forecast",
            json={"days": days},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_pending_invoices() -> Dict[str, Any]:
    """Get pending invoices"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/cashflow/pending-invoices", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def get_alerts(status: Optional[str] = None) -> Dict[str, Any]:
    """Get alerts"""
    try:
        params = {}
        if status:
            params['status'] = status
        response = requests.get(
            f"{API_BASE_URL}/api/alerts/list",
            params=params,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def resolve_alert(alert_id: int) -> Dict[str, Any]:
    """Resolve an alert"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/alerts/{alert_id}/resolve",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_percent(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"


def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {
        'critical': '#f44336',
        'high': '#ff9800',
        'medium': '#ffc107',
        'low': '#4caf50'
    }
    return colors.get(severity.lower(), '#666')


def get_status_color(status: str) -> str:
    """Get color for status"""
    colors = {
        'over_budget': '#f44336',
        'under_budget': '#4caf50',
        'on_track': '#2196f3',
        'active': '#4caf50',
        'expiring_soon': '#ff9800',
        'expired': '#f44336'
    }
    return colors.get(status.lower(), '#666')
