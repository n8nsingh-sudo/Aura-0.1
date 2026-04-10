from aura import config

try:
    from sentence_transformers import SentenceTransformer
    import chromadb

    _EMBEDDER_OK = True
except ImportError:
    _EMBEDDER_OK = False


class Embedder:
    def __init__(self):
        if not _EMBEDDER_OK:
            print("Embedder: sentence_transformers not installed.")
            self.model = None
            self.collection = None
            return

        print("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.client = chromadb.PersistentClient(path=str(config.VECTORS_DIR))
        self.collection = self.client.get_or_create_collection(
            name="aura_knowledge", metadata={"hnsw:space": "cosine"}
        )
        print(f"Embedder ready. {self.collection.count()} vectors stored.")

    def embed_and_store(self, text: str, doc_id: str, metadata: dict = None):
        if not self.model:
            return
        vector = self.model.encode(text).tolist()
        self.collection.add(
            ids=[doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search_similar(self, query: str, n_results: int = 5) -> list:
        if not self.model:
            return []
        query_vector = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

    def get_total_vectors(self) -> int:
        if not self.collection:
            return 0
        return self.collection.count()
