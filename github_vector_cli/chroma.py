import chromadb
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import hashlib
import os

class VectorDBManager:
    def __init__(self, data_dir: str = ".github_vector_cli"):
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Use new ChromaDB client configuration
        self.client = chromadb.PersistentClient(path=data_dir)
        self.collection = self.client.get_or_create_collection(
            name="github_repos",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def store_repository(self, repo_name: str, documents: Dict[str, str]) -> None:
        """Store repository documents in ChromaDB"""
        ids = []
        embeddings = []
        metadatas = []
        documents_list = []
        
        for path, content in documents.items():
            doc_id = self._generate_doc_id(repo_name, path)
            ids.append(doc_id)
            embeddings.append(self.embedding_model.encode(content))
            metadatas.append({"repo": repo_name, "path": path})
            documents_list.append(content)
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents_list
        )

    def search_repository(self, query: str, repo_name: Optional[str] = None, n_results: int = 5) -> List[Dict]:
        """Search across repositories with optional filtering"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        if repo_name:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"repo": repo_name}
            )
        else:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        
        return self._format_results(results)

    def _format_results(self, results) -> List[Dict]:
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                "id": results['ids'][0][i],
                "repo": results['metadatas'][0][i]['repo'],
                "path": results['metadatas'][0][i]['path'],
                "content": results['documents'][0][i],
                "distance": results['distances'][0][i]
            })
        return formatted

    def _generate_doc_id(self, repo_name: str, path: str) -> str:
        """Generate a unique ID for a document"""
        unique_str = f"{repo_name}_{path}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def clear_repository(self, repo_name: str) -> None:
        """Remove all documents for a specific repository"""
        self.collection.delete(where={"repo": repo_name})