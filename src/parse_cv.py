from pathlib import Path
from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    """Extract raw text from a CV PDF, page by page."""
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


if __name__ == "__main__":
    path = Path("profiles/cv.pdf")
    if not path.exists():
        raise FileNotFoundError(f"{path} not found - place your CV there first")
    text = extract_text(str(path))
    print(f"extracted {len(text)} characters, {text.count(chr(10))} lines\n")
    print(text[:800])