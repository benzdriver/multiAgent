# memory/embedding_db.py

import os
import json
from pathlib import Path
from typing import List
import numpy as np
import tiktoken
from openai import AsyncOpenAI

# Global config
DB_PATH = Path("data/vector/architecture_embeddings.json")
CHUNK_PATH = Path("data/vector/chunks.json")
MODEL = "text-embedding-3-small"
ENCODING = tiktoken.encoding_for_model(MODEL)

client = AsyncOpenAI()

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_embeddings():
    if not DB_PATH.exists():
        return []
    return json.loads(DB_PATH.read_text())

def load_chunks():
    if not CHUNK_PATH.exists():
        return []
    return json.loads(CHUNK_PATH.read_text())

def save_vector_db(chunks: List[str], embeddings: List[List[float]]):
    assert len(chunks) == len(embeddings), "Mismatch between chunks and embeddings count"
    CHUNK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHUNK_PATH.write_text(json.dumps(chunks, indent=2, ensure_ascii=False))
    DB_PATH.write_text(json.dumps(embeddings, indent=2))

async def embed_chunks(text_chunks: List[str]) -> List[List[float]]:
    response = await client.embeddings.create(
        model=MODEL,
        input=text_chunks
    )
    return [d.embedding for d in response.data]

def truncate(text: str, max_tokens=200) -> str:
    tokens = ENCODING.encode(text)
    return ENCODING.decode(tokens[:max_tokens])

def prepare_db_from_docs(docs: List[str]):
    from llm.token_splitter import split_text_by_tokens
    all_chunks = []
    for doc in docs:
        with open(doc, "r") as f:
            text = f.read()
            chunks = split_text_by_tokens(text, ENCODING, 200)
            print(f"📄 {doc} split into {len(chunks)} chunks.")
            all_chunks.extend(chunks)
    print(f"🧩 Total {len(all_chunks)} chunks prepared from markdown files.")
    return all_chunks

async def build_embedding_db(doc_paths: List[Path]):
    chunks = prepare_db_from_docs([str(p) for p in doc_paths])
    embeddings = await embed_chunks(chunks)
    save_vector_db(chunks, embeddings)

def query_relevant_excerpts(module_name: str, top_k=3) -> List[str]:
    if not DB_PATH.exists() or not CHUNK_PATH.exists():
        return []

    all_chunks = load_chunks()
    all_embeddings = load_embeddings()

    from openai import OpenAI
    sync_client = OpenAI()
    response = sync_client.embeddings.create(model=MODEL, input=[module_name])
    query_vec = response.data[0].embedding

    scores = [cosine_similarity(query_vec, vec) for vec in all_embeddings]
    top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]

    return [all_chunks[i] for i in top_indices]