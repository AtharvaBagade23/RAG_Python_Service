from functools import lru_cache
from app.config import get_settings
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.chat_service import ChatService

@lru_cache()
def get_pdf_service():
    return PDFService()

@lru_cache()
def get_embedding_service():
    settings = get_settings()
    return EmbeddingService(settings)

@lru_cache()
def get_pinecone_service():
    settings = get_settings()
    return PineconeService(settings)

@lru_cache()
def get_chat_service():
    settings = get_settings()
    embedding_svc = get_embedding_service()
    pinecone_svc = get_pinecone_service()
    return ChatService(settings, embedding_svc, pinecone_svc)
