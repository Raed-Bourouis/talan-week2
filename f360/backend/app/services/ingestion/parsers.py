"""
F360 – Document Parsers (PDF, Excel, CSV)
"""
from __future__ import annotations

import io
from typing import Any

import pdfplumber
import pandas as pd


def parse_pdf(raw_bytes: bytes) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Falls back gracefully on OCR-resistant PDFs.
    """
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

            # Also extract tables as structured text
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                    text_parts.append(" | ".join(cleaned_row))

    return "\n".join(text_parts)


def parse_excel(raw_bytes: bytes, file_type: str = "xlsx") -> str:
    """
    Extract text from Excel/CSV files.
    Converts all sheets into a text representation.
    """
    buffer = io.BytesIO(raw_bytes)

    if file_type == "csv":
        df = pd.read_csv(buffer, sep=None, engine="python", on_bad_lines="skip")
        return _dataframe_to_text(df, "Sheet1")

    # Excel files may have multiple sheets
    xls = pd.ExcelFile(buffer)
    text_parts: list[str] = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        text_parts.append(_dataframe_to_text(df, sheet_name))

    return "\n\n".join(text_parts)


def _dataframe_to_text(df: pd.DataFrame, sheet_name: str) -> str:
    """Convert a DataFrame to a structured text representation."""
    lines = [f"=== Sheet: {sheet_name} ==="]
    lines.append(f"Columns: {', '.join(df.columns.astype(str))}")
    lines.append(f"Rows: {len(df)}")
    lines.append("")

    # Include header + first 200 rows max for reasonable chunk sizes
    for idx, row in df.head(200).iterrows():
        row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
        lines.append(row_text)

    if len(df) > 200:
        lines.append(f"... ({len(df) - 200} additional rows truncated)")

    return "\n".join(lines)
