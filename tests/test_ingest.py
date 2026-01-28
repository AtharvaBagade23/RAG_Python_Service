import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.models import IngestRequest, IngestResponse

client = TestClient(app)

class TestIngestEndpoint:
    """Tests for PDF ingestion endpoint"""
    
    def test_ingest_success(self):
        """Test successful PDF ingestion"""
        request_data = {
            "pdf_url": "https://example.com/syllabus.pdf",
            "dept": "Computer Science",
            "year": "2024",
            "course_code": "CS301",
            "semester": "Fall"
        }
        
        with patch('app.dependencies.get_pdf_service') as mock_pdf, \
             patch('app.dependencies.get_embedding_service') as mock_embed, \
             patch('app.dependencies.get_pinecone_service') as mock_pine:
            
            # Mock PDF service
            mock_pdf_instance = Mock()
            mock_pdf_instance.fetch_pdf.return_value = b"PDF content"
            mock_pdf_instance.extract_text.return_value = "Extracted text from PDF. " * 100
            mock_pdf.return_value = mock_pdf_instance
            
            # Mock embedding service
            mock_embed_instance = Mock()
            mock_embed_instance.create_embeddings_batch.return_value = [[0.1] * 3072]
            mock_embed.return_value = mock_embed_instance
            
            # Mock Pinecone service
            mock_pine_instance = Mock()
            mock_pine_instance.upsert_vectors.return_value = 1
            mock_pine.return_value = mock_pine_instance
            
            response = client.post("/ingest", json=request_data)
            assert response.status_code == 200
            assert response.json()["success"] == True
    
    def test_ingest_invalid_request(self):
        """Test ingestion with invalid request"""
        request_data = {
            "pdf_url": "https://example.com/syllabus.pdf"
            # Missing required fields
        }
        
        response = client.post("/ingest", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_delete_syllabus(self):
        """Test syllabus deletion"""
        with patch('app.dependencies.get_pinecone_service') as mock_pine:
            mock_pine_instance = Mock()
            mock_pine_instance.delete_by_filter.return_value = None
            mock_pine.return_value = mock_pine_instance
            
            response = client.delete("/ingest?dept=CS&year=2024")
            assert response.status_code == 200
            assert "Deleted" in response.json()["message"]
