import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models import ChatRequest, ChatResponse

client = TestClient(app)

class TestChatEndpoint:
    """Tests for chat endpoint"""
    
    def test_chat_success(self):
        """Test successful chat response"""
        request_data = {
            "question": "What is the marking scheme?",
            "dept": "Computer Science",
            "year": "2024",
            "semester": "Fall"
        }
        
        with patch('app.dependencies.get_chat_service') as mock_chat:
            mock_chat_instance = Mock()
            mock_chat_instance.answer_question.return_value = {
                "answer": "The marking scheme is based on assignments and exams.",
                "sources": [{"score": 0.95, "dept": "Computer Science", "year": "2024"}],
                "confidence": "high"
            }
            mock_chat.return_value = mock_chat_instance
            
            response = client.post("/chat", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "confidence" in data
            assert data["confidence"] == "high"
    
    def test_chat_invalid_question(self):
        """Test chat with invalid question"""
        request_data = {
            "question": "Hi",  # Too short (min_length=3 but "Hi" is 2 chars)
            "dept": "Computer Science",
            "year": "2024"
        }
        
        response = client.post("/chat", json=request_data)
        # Note: "Hi" is 2 chars, min is 3, so this should fail
        assert response.status_code == 422
    
    def test_chat_missing_fields(self):
        """Test chat with missing required fields"""
        request_data = {
            "question": "What is the marking scheme?"
            # Missing dept and year
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 422
    
    def test_chat_no_results(self):
        """Test chat when no relevant documents found"""
        request_data = {
            "question": "What is the marking scheme?",
            "dept": "Computer Science",
            "year": "2024"
        }
        
        with patch('app.dependencies.get_chat_service') as mock_chat:
            mock_chat_instance = Mock()
            mock_chat_instance.answer_question.return_value = {
                "answer": "I couldn't find relevant information in your syllabus. Please rephrase your question or contact your department.",
                "sources": [],
                "confidence": "low"
            }
            mock_chat.return_value = mock_chat_instance
            
            response = client.post("/chat", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["confidence"] == "low"
            assert len(data["sources"]) == 0

class TestHealthCheck:
    """Tests for health check endpoint"""
    
    def test_health_check_healthy(self):
        """Test health check when everything is working"""
        with patch('app.dependencies.get_pinecone_service') as mock_pine, \
             patch('app.dependencies.get_embedding_service') as mock_embed:
            
            mock_pine_instance = Mock()
            mock_pine_instance.index = Mock()
            mock_pine.return_value = mock_pine_instance
            
            mock_embed_instance = Mock()
            mock_embed_instance.create_embedding.return_value = [0.1] * 3072
            mock_embed.return_value = mock_embed_instance
            
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "degraded"]
    
    def test_health_check_unhealthy(self):
        """Test health check when services are down"""
        with patch('app.dependencies.get_pinecone_service') as mock_pine:
            mock_pine.side_effect = Exception("Connection failed")
            
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
