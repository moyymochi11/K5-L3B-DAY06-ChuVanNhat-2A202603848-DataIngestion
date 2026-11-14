"""Real embedding provider adapter using local ONNX Sentence Transformers."""
from typing import Protocol
from chromadb.utils import embedding_functions


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Local Sentence Transformers embedder (all-MiniLM-L6-v2, 384 dimensions).
    Runs via ONNX runtime locally without requiring paid API keys or external services.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._ef = embedding_functions.DefaultEmbeddingFunction()
        # Verify model initialization and dimension
        sample_vector = self._ef(["test"])[0]
        self.dimensions = len(sample_vector)
        print(f"[Embedder] Initialized {self.model_name} with {self.dimensions} dimensions.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of document chunks."""
        if not texts:
            return []
        vectors = self._ef(texts)
        # Convert numpy floats/arrays to standard list of lists of floats
        return [list(map(float, vec)) for vec in vectors]

    def embed_query(self, question: str) -> list[float]:
        """Generate embedding vector for a single query string."""
        vectors = self._ef([question])
        return [float(x) for x in vectors[0]]
