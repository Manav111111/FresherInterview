import io
import re
import logging
from typing import Union
from pypdf import PdfReader

logger = logging.getLogger("fresherai.pdf")


def extract_pdf_text(file_content: Union[bytes, io.BytesIO]) -> str:
    """
    Extracts plain text from a PDF file buffer.
    Removes extraneous control characters and normalizes whitespace.
    """
    try:
        if isinstance(file_content, bytes):
            pdf_stream = io.BytesIO(file_content)
        else:
            pdf_stream = file_content

        reader = PdfReader(pdf_stream)
        text_parts = []

        for page_index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()

        # Clean non-printable characters while preserving newlines
        cleaned_text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", full_text)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        if not cleaned_text:
            logger.warning("PDF extraction returned empty text.")
            return ""

        return cleaned_text

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Failed to read and parse PDF file: {str(e)}")
