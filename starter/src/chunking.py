"""Implement fixed-size and structure-aware chunking."""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping character windows and retain page metadata."""
    text = page.text
    step = max(1, size - overlap)
    chunks: list[Chunk] = []
    
    start = 0
    chunk_idx = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunk = Chunk(
                chunk_id=f"{page.document_id}_p{page.page}_fix_{chunk_idx}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata={
                    **page.metadata,
                    "chunk_id": f"{page.document_id}_p{page.page}_fix_{chunk_idx}",
                    "chunk_type": "fixed",
                    "chunk_index": chunk_idx,
                    "page": page.page,
                    "source": page.source,
                    "char_count": len(chunk_text)
                }
            )
            chunks.append(chunk)
            chunk_idx += 1
        start += step
        if end >= len(text):
            break
            
    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 500) -> list[Chunk]:
    """Structure-aware chunking: groups sentences/natural clauses up to max_size.
    Avoids breaking sentences in the middle to maintain high chunk coherence.
    """
    text = page.text
    # Split by sentence end boundaries: periods, question marks, exclamation marks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks: list[Chunk] = []
    current_sentences: list[str] = []
    current_len = 0
    chunk_idx = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        # If adding this sentence exceeds max_size and we already have sentences
        if current_sentences and (current_len + len(sent) + 1 > max_size):
            chunk_text = " ".join(current_sentences).strip()
            chunk = Chunk(
                chunk_id=f"{page.document_id}_p{page.page}_para_{chunk_idx}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata={
                    **page.metadata,
                    "chunk_id": f"{page.document_id}_p{page.page}_para_{chunk_idx}",
                    "chunk_type": "paragraph",
                    "chunk_index": chunk_idx,
                    "page": page.page,
                    "source": page.source,
                    "char_count": len(chunk_text)
                }
            )
            chunks.append(chunk)
            chunk_idx += 1
            current_sentences = []
            current_len = 0
            
        current_sentences.append(sent)
        current_len += len(sent) + 1

    # Remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences).strip()
        chunk = Chunk(
            chunk_id=f"{page.document_id}_p{page.page}_para_{chunk_idx}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=chunk_text,
            metadata={
                **page.metadata,
                "chunk_id": f"{page.document_id}_p{page.page}_para_{chunk_idx}",
                "chunk_type": "paragraph",
                "chunk_index": chunk_idx,
                "page": page.page,
                "source": page.source,
                "char_count": len(chunk_text)
            }
        )
        chunks.append(chunk)

    return chunks
