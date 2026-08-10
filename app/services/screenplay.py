from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract all readable text from a PDF screenplay.
    """

    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages).strip()