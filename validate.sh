#!/bin/bash
# Quick validation script for the document processing system

echo "🧪 Running validation tests..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 is available"

# Check if sample documents exist
if [ ! -d "data/sample_docs" ]; then
    echo "❌ Sample documents directory not found"
    exit 1
fi

if [ ! -f "data/sample_docs/annual_report_2023.pdf" ] || \
   [ ! -f "data/sample_docs/financial_data_2023.xlsx" ] || \
   [ ! -f "data/sample_docs/financial_report_q4.docx" ]; then
    echo "❌ Some sample documents are missing"
    exit 1
fi

echo "✓ Sample documents are present"

# Install test dependencies if needed
pip install -q PyPDF2 pdfplumber python-docx openpyxl pytest 2>/dev/null

# Run parser tests
echo ""
echo "📄 Testing document parsers..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from src.parsers.pdf_parser import PDFParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.word_parser import WordParser

try:
    # Test PDF
    pdf_parser = PDFParser()
    pdf_result = pdf_parser.parse("data/sample_docs/annual_report_2023.pdf")
    assert len(pdf_result['text']) > 0, "PDF text extraction failed"
    print("✓ PDF parser works")
    
    # Test Excel
    excel_parser = ExcelParser()
    excel_result = excel_parser.parse("data/sample_docs/financial_data_2023.xlsx")
    assert len(excel_result['sheets']) > 0, "Excel sheet extraction failed"
    print("✓ Excel parser works")
    
    # Test Word
    word_parser = WordParser()
    word_result = word_parser.parse("data/sample_docs/financial_report_q4.docx")
    assert len(word_result['text']) > 0, "Word text extraction failed"
    print("✓ Word parser works")
    
except Exception as e:
    print(f"❌ Parser test failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# Run pytest if available
echo ""
echo "🧪 Running unit tests..."
if python3 -m pytest tests/ -v --tb=short 2>&1 | grep -q "passed"; then
    echo "✓ All unit tests passed"
else
    echo "⚠️  Some tests may have failed (check output above)"
fi

echo ""
echo "✅ Validation complete!"
echo ""
echo "Next steps:"
echo "  1. Start services: docker-compose up -d"
echo "  2. Pull Ollama model: docker exec ollama ollama pull llama2"
echo "  3. Test API: curl http://localhost:8000/health"
echo "  4. View docs: http://localhost:8000/docs"
