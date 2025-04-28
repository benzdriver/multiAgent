from dotenv import load_dotenv
load_dotenv()
import os
from memory.embedding_client import EmbeddingClient
from memory.embedding_client import LocalEmbeddingClient
# from memory.external.pinecone_client import PineconeEmbeddingClient
# from memory.external.weaviate_client import WeaviateEmbeddingClient
# 更多可插拔客户端...

def get_embedding_client(name: str = "local") -> EmbeddingClient:
    """
    Get the embedding client by name.
    Defaults to 'local'. Extendable to Pinecone, Weaviate, etc.
    """
    backend = os.getenv("VECTOR_BACKEND", "local")
    if backend == "local":
        return LocalEmbeddingClient()
    # elif name == "pinecone":
    #     return PineconeEmbeddingClient()
    # elif name == "weaviate":
    #     return WeaviateEmbeddingClient()
    else:
        raise ValueError(f"Unknown embedding client: {name}")
