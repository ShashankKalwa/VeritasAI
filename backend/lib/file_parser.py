"""
File upload & text extraction utilities.
Supports: PDF, DOCX, TXT
"""
import io
import re
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t.strip())
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file bytes."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from plain text file."""
    try:
        for encoding in ["utf-8", "latin-1", "ascii"]:
            try:
                return file_bytes.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"TXT extraction error: {e}")
        return ""


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Route to correct extractor based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    elif ext in ("txt", "text", "md", "csv"):
        return extract_text_from_txt(file_bytes)
    else:
        return ""


def is_meaningful_content(text: str) -> tuple[bool, str]:
    """
    Check if extracted text contains meaningful news-like content.
    Returns (is_valid, reason).
    """
    text = text.strip()

    if len(text) < 20:
        return False, "Text is too short to analyze. Please upload a file with more content."

    # Check for gibberish / random characters
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio < 0.4:
        return False, "This file does not contain readable text content. Please upload a document with proper text."

    # Check word count
    words = text.split()
    if len(words) < 5:
        return False, "Content is too short — needs at least 5 words of readable text."

    # Check average word length (gibberish tends to have very long or very short "words")
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 2 or avg_word_len > 25:
        return False, "This does not appear to contain proper news content or readable text."

    # Check for sentence-like structure
    has_sentences = bool(re.search(r'[.!?]\s', text)) or len(words) > 10
    if not has_sentences and len(words) < 10:
        return False, "Content does not appear to contain proper sentences or news headlines."

    return True, "Content is valid for analysis"
