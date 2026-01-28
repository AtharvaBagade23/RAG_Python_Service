from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import json
from app.models import IngestResponse
from app.dependencies import (
    get_pdf_service,
    get_embedding_service,
    get_pinecone_service
)
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.utils.chunking import chunk_text
from app.config import get_settings

router = APIRouter(prefix="/ingest", tags=["Admin"])

# Admin ingest request model
class AdminIngestRequest(BaseModel):
    pdf_url: str  # Cloudinary PDF URL
    dept: str     # Department (e.g., "Computer")
    year: str     # Academic year (e.g., "2024")

def validate_admin_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validate admin token from Authorization header
    Expected format: Bearer <admin_token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    admin_key = get_settings().api_secret_key
    
    if token != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return {"authenticated": True}

@router.post("", response_model=IngestResponse)
async def ingest_syllabus(
    request: AdminIngestRequest,
    admin_auth: dict = Depends(validate_admin_token),
    pdf_service: PDFService = Depends(get_pdf_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """
    Admin endpoint: Ingest syllabus PDF into vector DB
    
    Admin provides only:
    - pdf_url: Cloudinary PDF URL
    - dept: Department (e.g., "Computer Science")
    - year: Academic year (e.g., "2024")
    
    Steps:
    1. Fetch PDF from Cloudinary
    2. Extract text
    3. Chunk text with semantic understanding
    4. Create embeddings
    5. Store in Pinecone with college-based metadata
    
    Authorization: Requires Bearer token in header
    """
    try:
        settings = get_settings()
        
        # 1. Fetch PDF
        pdf_bytes = pdf_service.fetch_pdf(request.pdf_url)
        
        # 2. Extract text
        text = pdf_service.extract_text(pdf_bytes)
        
        # 3. Chunk text with semantic understanding
        chunks = chunk_text(
            text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
            use_semantic=True
        )
        
        if not chunks:
            raise ValueError("No chunks created from PDF")
        
        # 4. Extract text content for embedding
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        # 5. Create embeddings
        embeddings = embedding_service.create_embeddings_batch(chunk_texts)
        
        # 6. Prepare rich metadata for each chunk
        metadata_list = []
        for chunk_dict in chunks:
            # Base metadata with only dept and year
            metadata = {
                "dept": request.dept,
                "year": request.year,
                "doc_type": "syllabus",
                "source": "admin_upload",
                "text": chunk_dict['text'],
                "section": chunk_dict.get('section', 'general'),
                "chunk_type": chunk_dict.get('type', 'general'),
                "chunk_size": chunk_dict.get('size', 0)
            }
            
            # Add extracted course information from PDF content
            if chunk_dict.get('metadata'):
                metadata.update(chunk_dict['metadata'])
            
            metadata_list.append(metadata)
        
        # 7. Upsert to Pinecone
        vectors_stored = pinecone_service.upsert_vectors(
            vectors=embeddings,
            metadata_list=metadata_list
        )
        
        print(f"[INGEST] Successfully ingested {vectors_stored} vectors for {request.dept} ({request.year})")
        
        return IngestResponse(
            success=True,
            message=f"Successfully processed syllabus for {request.dept} ({request.year}). Stored {vectors_stored} vectors.",
            chunks_processed=len(chunks),
            vectors_stored=vectors_stored
        )
    
    except Exception as e:
        print(f"[INGEST ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
async def delete_syllabus(
    dept: str,
    year: str,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Delete all vectors for a specific department and year"""
    try:
        pinecone_service.delete_by_filter({
            "dept": dept,
            "year": year
        })
        return {"message": f"Deleted syllabus for {dept} ({year})"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
