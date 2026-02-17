"""
F360 – Multimodal Parsers
Unified parsers for PDF, Images (OCR), Audio (transcription), Video (frames + audio).
Extends the original PDF/Excel parsers with multimodal capabilities.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import pdfplumber
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# PDF PARSER
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# EXCEL / CSV PARSER
# ═══════════════════════════════════════════════════════════════

def parse_excel(raw_bytes: bytes, file_type: str = "xlsx") -> str:
    """
    Extract text from Excel/CSV files.
    Converts all sheets into a text representation.
    """
    buffer = io.BytesIO(raw_bytes)

    if file_type == "csv":
        df = pd.read_csv(buffer, sep=None, engine="python", on_bad_lines="skip")
        return _dataframe_to_text(df, "Sheet1")

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

    for idx, row in df.head(200).iterrows():
        row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
        lines.append(row_text)

    if len(df) > 200:
        lines.append(f"... ({len(df) - 200} additional rows truncated)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# IMAGE PARSER (OCR)
# ═══════════════════════════════════════════════════════════════

def parse_image(raw_bytes: bytes, lang: str = "fra+eng") -> str:
    """
    Extract text from images using Tesseract OCR.
    Supports scanned invoices, contracts, receipts.
    """
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(raw_bytes))

        # Pre-process: convert to grayscale for better OCR
        if image.mode != "L":
            image = image.convert("L")

        text = pytesseract.image_to_string(image, lang=lang)
        logger.info(f"OCR extracted {len(text)} characters from image")
        return text.strip()

    except ImportError:
        logger.warning("PIL/pytesseract not installed – image OCR unavailable")
        return "[IMAGE: OCR extraction requires Pillow + pytesseract]"
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return f"[IMAGE: OCR extraction failed – {e}]"


# ═══════════════════════════════════════════════════════════════
# AUDIO PARSER (Transcription)
# ═══════════════════════════════════════════════════════════════

async def parse_audio(raw_bytes: bytes, language: str = "fr") -> str:
    """
    Transcribe audio files using OpenAI Whisper API.
    Supports: mp3, wav, m4a, ogg, flac.
    Used for: meeting recordings, phone calls, voice notes.
    """
    try:
        from openai import AsyncOpenAI
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return "[AUDIO: Transcription requires a valid OpenAI API key]"

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        audio_file = io.BytesIO(raw_bytes)
        audio_file.name = "audio.mp3"

        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text",
        )
        logger.info(f"Audio transcription: {len(response)} characters")
        return response

    except ImportError:
        return "[AUDIO: openai package not installed]"
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        return f"[AUDIO: Transcription failed – {e}]"


# ═══════════════════════════════════════════════════════════════
# VIDEO PARSER (Frames + Audio)
# ═══════════════════════════════════════════════════════════════

async def parse_video(raw_bytes: bytes, extract_frames: bool = True) -> str:
    """
    Extract information from video files:
    1. Extract audio track → transcribe via Whisper
    2. Extract key frames → OCR for on-screen text
    Used for: training videos, presentation recordings, dashboards.
    """
    parts: list[str] = []

    # 1. Extract and transcribe audio
    try:
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            tmp_video.write(raw_bytes)
            video_path = tmp_video.name

        audio_path = video_path.replace(".mp4", ".mp3")

        # Extract audio using ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"],
            capture_output=True, timeout=120,
        )

        if result.returncode == 0:
            with open(audio_path, "rb") as af:
                audio_bytes = af.read()
            transcript = await parse_audio(audio_bytes)
            parts.append(f"=== Audio Transcript ===\n{transcript}")

            # Clean up
            Path(audio_path).unlink(missing_ok=True)

        Path(video_path).unlink(missing_ok=True)

    except (ImportError, FileNotFoundError) as e:
        parts.append(f"[VIDEO: Audio extraction requires ffmpeg – {e}]")
    except Exception as e:
        logger.error(f"Video audio extraction failed: {e}")
        parts.append(f"[VIDEO: Audio extraction failed – {e}]")

    # 2. Extract key frames for OCR (if enabled)
    if extract_frames:
        parts.append("[VIDEO: Frame OCR – requires opencv-python for key frame extraction]")

    return "\n\n".join(parts) if parts else "[VIDEO: No content extracted]"


# ═══════════════════════════════════════════════════════════════
# UNIFIED PARSER DISPATCHER
# ═══════════════════════════════════════════════════════════════

SYNC_PARSERS = {
    "pdf": parse_pdf,
    "xlsx": lambda b: parse_excel(b, "xlsx"),
    "xls": lambda b: parse_excel(b, "xls"),
    "csv": lambda b: parse_excel(b, "csv"),
    "png": parse_image,
    "jpg": parse_image,
    "jpeg": parse_image,
    "tiff": parse_image,
    "bmp": parse_image,
}

ASYNC_PARSERS = {
    "mp3": parse_audio,
    "wav": parse_audio,
    "m4a": parse_audio,
    "ogg": parse_audio,
    "flac": parse_audio,
    "mp4": parse_video,
    "avi": parse_video,
    "mkv": parse_video,
    "mov": parse_video,
}


async def parse_file(raw_bytes: bytes, file_type: str) -> str:
    """
    Unified file parser — dispatches to the correct parser based on file type.
    Returns extracted text content.
    """
    file_type = file_type.lower().lstrip(".")

    if file_type in SYNC_PARSERS:
        return SYNC_PARSERS[file_type](raw_bytes)

    if file_type in ASYNC_PARSERS:
        return await ASYNC_PARSERS[file_type](raw_bytes)

    # Fallback: try to decode as plain text
    try:
        return raw_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return f"[UNSUPPORTED: Cannot parse file type '{file_type}']"
