from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    
    # Pinecone
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "studentpath-syllabus"
    
    # Embedding
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072
    
    # Chat
    chat_model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 1000
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    # Server
    port: int = 8000
    workers: int = 4
    allowed_origins: list[str] = ["*"]
    
    # Security
    api_secret_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
