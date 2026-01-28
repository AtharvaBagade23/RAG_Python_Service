from pydantic import BaseModel, Field
from typing import Optional, List

class IngestRequest(BaseModel):
    """Admin syllabus upload request"""
    pdf_url: str = Field(..., description="Cloudinary PDF URL")
    dept: str = Field(..., description="Department name")
    year: str = Field(..., description="Academic year")
    course_code: Optional[str] = None
    semester: Optional[str] = None

class IngestResponse(BaseModel):
    """Ingestion result"""
    success: bool
    message: str
    chunks_processed: int
    vectors_stored: int

class ChatRequest(BaseModel):
    """Student chat request"""
    question: str = Field(..., min_length=3, max_length=500)
    dept: str
    year: str
    semester: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response with sources"""
    answer: str
    sources: List[dict]
    confidence: str  # high, medium, low

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    pinecone_connected: bool
    openai_connected: bool
