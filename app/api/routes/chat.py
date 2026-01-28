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
    
    # Optional: Allow student data in body as fallback
    dept: Optional[str] = None
    year: Optional[str] = None
    year_level: Optional[str] = None
    enrollment_year: Optional[int] = None
    semester: Optional[str] = None
    program: Optional[str] = None
    token: Optional[str] = None

def parse_student_context(student_data_header: Optional[str] = Header(None, alias="x-student-data")) -> dict:
    """
    Parse student authentication and academic data from header
    
    Expected format: x-student-data header containing JSON:
    {
        "student_id": 25,
        "dept": "Computer",
        "year": "2024",
        "year_level": "2",
        "enrollment_year": 2024,
        "semester": "2",
        "program": "Computer Engineering",
        "token": "abc123",
        "isAuthenticated": true
    }
    
    Returns merged data with all fields properly mapped
    """
    if not student_data_header:
        raise HTTPException(status_code=401, detail="Missing student authentication data in x-student-data header")
    
    try:
        student_data = json.loads(student_data_header)
        
        # Validate essential fields
        if not student_data.get("isAuthenticated"):
            raise HTTPException(status_code=401, detail="Student not authenticated")
        
        if not student_data.get("token"):
            raise HTTPException(status_code=401, detail="Invalid student token")
        
        # Map various field names to standard names (handle different naming conventions)
        # Map 'program' to 'dept' if dept not present
        if student_data.get("program") and not student_data.get("dept"):
            student_data["dept"] = student_data["program"]
        if student_data.get("dept") and not student_data.get("program"):
            student_data["program"] = student_data["dept"]
        
        # Map year_level or enrollment_year to year
        if not student_data.get("year"):
            if student_data.get("year_level"):
                student_data["year"] = str(student_data["year_level"])
            elif student_data.get("enrollment_year"):
                student_data["year"] = str(student_data["enrollment_year"])
        
        # Ensure dept and year exist (required for filtering)
        if not student_data.get("dept"):
            raise HTTPException(status_code=400, detail="Missing department (dept/program) information")
        if not student_data.get("year"):
            raise HTTPException(status_code=400, detail="Missing year information")
        
        return student_data
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid student data format: {str(e)}")

@router.post("", response_model=ChatResponse)
async def chat(
    request: StudentChatRequest,
    student_data: dict = Depends(parse_student_context),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Student endpoint: Ask questions about syllabus
    
    Automatically filters by:
    - Department: From student's academic profile (dept/program)
    - Year: From student's academic profile (year/year_level/enrollment_year)
    - Semester: From student's academic profile (if available)
    
    Requires:
    - x-student-data header: JSON with student info
      {
        "dept": "Computer",
        "year": "2024",
        "semester": "2",
        "program": "Computer Engineering",
        "token": "...",
        "isAuthenticated": true
      }
    - question: Question about the syllabus
    
    Returns:
    - answer: RAG-generated answer with exact context
    - sources: Relevant chunks from the syllabus
    - confidence: High/Medium/Low based on match quality
    """
    try:
        # Extract and validate student context for filtering
        dept = student_data.get("dept") or request.dept
        year = student_data.get("year") or request.year
        semester = student_data.get("semester") or request.semester
        
        # Fallback values if still missing
        if not dept:
            dept = "Computer Science"
        if not year:
            year = "2024"
        
        print(f"[CHAT] Query with filters - Dept: {dept}, Year: {year}, Semester: {semester}")
        print(f"[CHAT] Question: {request.question}")
        print(f"[CHAT] Student Data: {student_data}")
        
        # Get RAG answer with proper filters
        result = chat_service.answer_question(
            question=request.question,
            dept=dept,
            year=year,
            semester=semester
        )
        
        print(f"[CHAT] Response - Confidence: {result['confidence']}, Sources: {len(result['sources'])}")
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    
    except Exception as e:
        print(f"[CHAT ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
