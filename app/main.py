from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import ingest, chat
from app.models import HealthResponse
from app.dependencies import get_pinecone_service, get_embedding_service

settings = get_settings()

app = FastAPI(
    title="StudentPath RAG Service",
    description="Personalized syllabus chatbot with Pinecone + GPT",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(chat.router)

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    pinecone_ok = False
    openai_ok = False
    
    try:
        pinecone_svc = get_pinecone_service()
        # Check if Pinecone is properly connected
        if pinecone_svc.is_connected():
            pinecone_ok = True
    except Exception as e:
        print(f"Pinecone health check failed: {str(e)}")
        pinecone_ok = False
    
    try:
        embedding_svc = get_embedding_service()
        # Check if OpenAI is properly connected
        if embedding_svc.is_connected():
            openai_ok = True
    except Exception as e:
        print(f"OpenAI health check failed: {str(e)}")
        openai_ok = False
    
    # Determine overall status
    if pinecone_ok and openai_ok:
        status = "healthy"
    elif pinecone_ok or openai_ok:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        pinecone_connected=pinecone_ok,
        openai_connected=openai_ok
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        workers=settings.workers,
        reload=True
    )
