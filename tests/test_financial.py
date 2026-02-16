"""
Sample test file for Financial Intelligence Hub
"""

import pytest
from src.ingestion.document_parser import DocumentParser
from src.financial.budget_analyzer import BudgetAnalyzer

def test_document_parser():
    """Test document parser with sample files"""
    parser = DocumentParser()
    
    # Test that parser initializes correctly
    assert parser is not None
    assert len(parser.supported_formats) > 0
    assert '.pdf' in parser.supported_formats
    assert '.csv' in parser.supported_formats


def test_budget_analyzer():
    """Test budget analyzer"""
    analyzer = BudgetAnalyzer(db_connection=None)
    
    # Test analyze_budget with mock data
    result = analyzer.analyze_budget('DEPT001', 2024)
    
    assert result is not None
    assert 'allocated' in result
    assert 'spent' in result
    assert 'variance' in result
    assert 'recommendations' in result
    
    # Check that variance is calculated correctly
    expected_variance = result['spent'] - result['allocated']
    assert result['variance'] == expected_variance


def test_budget_status_classification():
    """Test budget status classification"""
    analyzer = BudgetAnalyzer(db_connection=None)
    
    result = analyzer.analyze_budget('DEPT001', 2024)
    
    # With mock data (spent > allocated), should be over budget
    assert result['status'] in ['over_budget', 'significantly_over_budget', 'under_budget', 'on_track']
    
    # Severity should be set
    assert result['severity'] in ['critical', 'warning', 'info', 'normal']


def test_year_end_forecast():
    """Test year-end budget forecast"""
    analyzer = BudgetAnalyzer(db_connection=None)
    
    forecast = analyzer.forecast_year_end('DEPT001', 2024)
    
    assert forecast is not None
    assert 'projected_year_end' in forecast
    assert 'projected_variance' in forecast
    assert 'months_remaining' in forecast
    assert 'confidence' in forecast


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
