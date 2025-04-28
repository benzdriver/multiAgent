# memory/embedding_client.py

from typing import List, Protocol
from pathlib import Path

class EmbeddingClient(Protocol):
    def load(self):
        """Load the vector index and metadata."""
        ...

    def query(self, query_text: str, top_k: int = 3) -> List[str]:
        """Query top-K relevant chunks based on input text."""
        ...

    def build(self, doc_paths: List[Path]):
        """Build the index from a list of markdown documents."""
        ...


# Default: Local JSON Vector Client
from memory.embedding_db import (
    load_chunks, load_embeddings, cosine_similarity,
    embed_chunks, prepare_db_from_docs, save_vector_db
)
from openai import OpenAI
import json
import numpy as np

class LocalEmbeddingClient:
    def __init__(self):
        self.chunks = []
        self.embeddings = []
        self.model = "text-embedding-3-small"

    def load(self):
        self.chunks = load_chunks()
        self.embeddings = load_embeddings()

    def query(self, query_text: str, top_k: int = 3) -> List[str]:
        sync_client = OpenAI()
        response = sync_client.embeddings.create(model=self.model, input=[query_text])
        query_vec = response.data[0].embedding
        
        scores = [cosine_similarity(query_vec, v) for v in self.embeddings]
        top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [self.chunks[i] for i in top_indices]

    async def build(self, doc_paths: List[Path]):
        chunks = prepare_db_from_docs([str(p) for p in doc_paths])
        vectors = await embed_chunks(chunks)
        save_vector_db(chunks, vectors)
