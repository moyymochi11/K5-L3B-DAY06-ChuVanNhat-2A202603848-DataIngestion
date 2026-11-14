"""Store and search vectors using persistent Chroma vector store."""
from pathlib import Path
from typing import Any
import chromadb
from .models import Chunk


class ChromaVectorStore:
    """Persistent Chroma vector store with metadata filtering and cosine similarity."""

    def __init__(self, persist_dir: str = "starter/chroma_store", dimensions: int = 384) -> None:
        self.persist_dir = persist_dir
        self.dimensions = dimensions
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        print(f"[Store] Persistent ChromaDB initialized at {self.persist_dir}")

    def create_schema(self) -> None:
        """Schema is dynamically managed by Chroma collections with cosine metric."""
        pass

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Insert or replace chunks cleanly without duplicates.
        When re-ingesting, existing collection for this strategy is recreated.
        """
        if len(chunks) != len(vectors):
            raise ValueError(f"Length mismatch: {len(chunks)} chunks vs {len(vectors)} vectors.")

        collection_name = f"strategy_{strategy.lower()}"
        
        # Reset collection to ensure clean, non-duplicate state
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass

        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            
            ids = [c.chunk_id for c in batch_chunks]
            documents = [c.text for c in batch_chunks]
            metadatas = [c.metadata for c in batch_chunks]
            
            collection.add(
                ids=ids,
                embeddings=batch_vectors,
                documents=documents,
                metadatas=metadatas
            )

        print(f"[Store] Upserted {len(chunks)} chunks into collection '{collection_name}'.")

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Filter metadata in vector store, rank by cosine similarity, return top-k hits."""
        collection_name = f"strategy_{strategy.lower()}"
        collection = self.client.get_collection(collection_name)

        where_filter = filters if filters else None

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter
        )

        hits: list[dict[str, Any]] = []
        if results and results["ids"] and results["ids"][0]:
            num_hits = len(results["ids"][0])
            for i in range(num_hits):
                chunk_id = results["ids"][0][i]
                doc_text = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                # Cosine similarity = 1 - cosine distance
                score = 1.0 - distance
                
                hits.append({
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "score": score,
                    "distance": distance,
                    "metadata": meta
                })

        return hits
