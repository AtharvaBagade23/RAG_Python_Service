from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
from app.config import Settings
import uuid

class PineconeService:
    """Pinecone vector database operations"""
    
    def __init__(self, settings: Settings):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = settings.embedding_dimension
        self.index = None
        self._connected = False
        
        # Try to initialize index
        try:
            self._ensure_index_exists()
            self.index = self.pc.Index(self.index_name)
            self._connected = True
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone index: {str(e)}")
            self._connected = False
    
    def is_connected(self):
        """Check if Pinecone is connected"""
        return self._connected and self.index is not None
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        except Exception as e:
            print(f"Warning: Could not ensure Pinecone index exists: {str(e)}")
            raise
    
    def upsert_vectors(
        self,
        vectors: List[List[float]],
        metadata_list: List[Dict[str, Any]]
    ) -> int:
        """
        Store vectors with metadata
        
        Returns:
            Number of vectors upserted
        """
        vectors_to_upsert = []
        
        for i, (vector, metadata) in enumerate(zip(vectors, metadata_list)):
            vector_id = f"{metadata['dept']}-{metadata['year']}-{uuid.uuid4()}"
            vectors_to_upsert.append({
                "id": vector_id,
                "values": vector,
                "metadata": metadata
            })
        
        # Upsert in batches of 100
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self.index.upsert(vectors=batch)
            total_upserted += len(batch)
        
        return total_upserted
    
    def query(
        self,
        vector: List[float],
        filter_dict: Dict[str, str],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Query vectors with metadata filter
        
        Args:
            vector: Query embedding
            filter_dict: Metadata filters (dept, year, etc.)
            top_k: Number of results
        
        Returns:
            List of matches with metadata and scores
        """
        results = self.index.query(
            vector=vector,
            filter=filter_dict,
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            }
            for match in results.matches
        ]
    
    def delete_by_filter(self, filter_dict: Dict[str, str]):
        """Delete vectors matching filter"""
        self.index.delete(filter=filter_dict)
