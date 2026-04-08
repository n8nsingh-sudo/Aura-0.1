from sentence_transformers import SentenceTransformer
import chromadb
from aura import config


class Embedder:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.client = chromadb.PersistentClient(path=str(config.VECTORS_DIR))
        self.collection = self.client.get_or_create_collection(
            name="aura_knowledge", metadata={"hnsw:space": "cosine"}
        )
        print(f"Embedder ready. {self.collection.count()} vectors stored.")

    def embed_and_store(self, text: str, doc_id: str, metadata: dict = None):
        vector = self.model.encode(text).tolist()
        self.collection.add(
            ids=[doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search_similar(self, query: str, n_results: int = 5) -> list:
        query_vector = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

    def get_total_vectors(self) -> int:
        return self.collection.count()
