import os
from pathlib import Path
from typing import Optional

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from a file (PDF, TXT, or Markdown).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()

    elif suffix == ".pdf":
        import pdfplumber
        extracted_pages = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(f"--- Page {i + 1} ---\n{page_text}")
        return "\n\n".join(extracted_pages).strip()

    else:
        # Fallback reading as plain text
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Định dạng file không được hỗ trợ ({suffix}): {str(e)}")

