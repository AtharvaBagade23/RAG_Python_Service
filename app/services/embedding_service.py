from openai import OpenAI
from typing import List
from app.config import Settings

class EmbeddingService:
    """OpenAI embedding generation"""
    
    def __init__(self, settings: Settings):
        try:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.embedding_model
            self._connected = True
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {str(e)}")
            self.client = None
            self.model = settings.embedding_model
            self._connected = False
    
    def is_connected(self):
        """Check if OpenAI client is properly initialized"""
        return self._connected and self.client is not None
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self.is_connected():
            raise ValueError("OpenAI client not connected")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise ValueError(f"Embedding failed: {str(e)}")
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.is_connected():
            raise ValueError("OpenAI client not connected")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise ValueError(f"Batch embedding failed: {str(e)}")

