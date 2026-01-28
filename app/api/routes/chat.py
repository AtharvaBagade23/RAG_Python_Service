from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
import json
from app.models import ChatResponse
from app.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Student"])

# Student chat request model
class StudentChatRequest(BaseModel):
    """Student asks question using college context"""
    question: str = Field(..., min_length=3, max_length=500)
    # Student data comes from header, not request body

def parse_student_cookie(x_student_data: Optional[str] = Header(None)) -> dict:
    """
    Parse student authentication data from header
    
    Expected format: x-student-data header containing JSON:
    {
        "student_id": 25,
        "first_name": "Shweta",
        "last_name": "Jadhav",
        "email": "sdjadhav@gmail.com",
        "token": "894m0QCWDu57ASOLRXGy",
        "isAuthenticated": true,
        "isAdmin": false,
        "college_id": 1,
        "college_name": "ABC University",
        "program": "Computer Science",
        "current_year": "2024",
        "current_semester": "1"
    }
    """
    if not x_student_data:
        raise HTTPException(status_code=401, detail="Missing student authentication data")
    
    try:
        student_data = json.loads(x_student_data)
        
        # Validate essential fields
        required_fields = ["student_id", "token", "isAuthenticated"]
        for field in required_fields:
            if field not in student_data:
                raise ValueError(f"Missing required field: {field}")
        
        if not student_data.get("isAuthenticated"):
            raise HTTPException(status_code=401, detail="Student not authenticated")
        
        return student_data
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid student data format")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("", response_model=ChatResponse)
async def chat(
    request: StudentChatRequest,
    student_data: dict = Depends(parse_student_cookie),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Student endpoint: Ask questions about syllabus
    
    Automatically filters by:
    - Department: From student's academic profile (program)
    - Year: From student's academic profile (current_year)
    - Semester: From student's academic profile (current_semester)
    
    Requires:
    - x-student-data header: JSON with student info and college context
    - question: Question about the syllabus
    
    Returns:
    - answer: RAG-generated answer
    - sources: Relevant chunks from the syllabus
    - confidence: High/Medium/Low based on match quality
    """
    try:
        # Extract student context for filtering
        dept = student_data.get("program") or student_data.get("dept", "Computer Science")
        year = student_data.get("current_year") or student_data.get("year", "2024")
        semester = student_data.get("current_semester") or student_data.get("semester", "1")
        student_id = student_data.get("student_id")
        
        # Get RAG answer
        result = chat_service.answer_question(
            question=request.question,
            dept=dept,
            year=year,
            semester=semester
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
