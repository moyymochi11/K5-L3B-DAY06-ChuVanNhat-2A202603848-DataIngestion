"""Read and normalize source data."""
import unicodedata
from pathlib import Path
import pypdf
from .models import DocumentPage


def get_section_for_page(page_num: int) -> str:
    """Map physical page number to document section metadata."""
    if 3 <= page_num <= 5:
        return "campus_overview"
    elif 6 <= page_num <= 11:
        return "pre_arrival"
    elif 12 <= page_num <= 29:
        return "arrival_settling_in"
    elif 30 <= page_num <= 37:
        return "academic_support"
    elif 38 <= page_num <= 48:
        return "social_integration"
    elif 49 <= page_num <= 50:
        return "health_and_insurance"
    elif 51 <= page_num <= 54:
        return "legal_and_emergency"
    return "general"


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding sentence structure."""
    if not text:
        return ""
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    # Replace carriage returns with standard newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean up whitespace line by line
    lines = [line.strip() for line in text.split("\n")]
    # Join with standard spacing
    normalized = " ".join(" ".join(lines).split())
    return normalized


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract each physical page; keep page number, source, and metadata.
    Detects and records pages with no text or very short content.
    """
    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []
    
    empty_pages = []
    for idx, raw_page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = raw_page.extract_text() or ""
        norm_text = normalize_text(raw_text)
        
        # Exclude pages with insufficient content (covers, blank separator pages)
        if len(norm_text) < 80:
            empty_pages.append(page_num)
            continue
            
        section = get_section_for_page(page_num)
        page_obj = DocumentPage(
            document_id=document_id,
            source=source,
            page=page_num,
            text=norm_text,
            metadata={
                "section": section,
                "year": 2024,
                "language": "en",
                "char_count": len(norm_text)
            }
        )
        pages.append(page_obj)

    print(f"[Ingestion] Loaded {len(pages)} content pages from {path.name}.")
    print(f"[Ingestion] Excluded {len(empty_pages)} low-text/empty pages: {empty_pages}")
    return pages
