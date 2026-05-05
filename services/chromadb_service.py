import chromadb
from chromadb.utils import embedding_functions
import os

class ChromaDBService:
    def __init__(self, persist_directory: str = "data/chroma"):
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using sentence-transformers for local embeddings
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="local_rag_collection",
            embedding_function=self.emb_fn
        )

    def add_documents(self, chunks: list, file_id: str, file_name: str):
        ids = [f"{file_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"file_id": file_id, "file_name": file_name} for _ in chunks]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    def query(self, query_text: str, file_id: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"file_id": file_id}
        )
        return results['documents'][0] if results['documents'] else []
