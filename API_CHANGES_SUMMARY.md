# API Routes Updated for Student Authentication

## Changes Made to Your RAG API

### 1. Admin Ingest Route (`app/api/routes/ingest.py`)

**Old Model:** Required `pdf_url`, `dept`, `year`, `course_code`, `semester`

**New Model:**
```python
class AdminIngestRequest(BaseModel):
    pdf_url: str  # Only PDF URL from admin
    dept: str     # Department
    year: str     # Academic year
```

**Authentication:** Bearer token in Authorization header
```
Authorization: Bearer <your_admin_secret_key>
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer rag_studentpath_admin_2026" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://cloudinary.com/path/to/syllabus.pdf",
    "dept": "Computer Science",
    "year": "2024"
  }'
```

**Metadata Stored:**
- dept, year, doc_type, source
- Extracted course info (course_code, semester, credits, etc. from PDF)

---

### 2. Student Chat Route (`app/api/routes/chat.py`)

**Old Model:** Required `question`, `dept`, `year`, `semester` in request body

**New Model:**
```python
class StudentChatRequest(BaseModel):
    question: str  # Only question required
```

**Authentication:** Student data in `x-student-data` header
```
x-student-data: {
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
```

**Auto-Filtering:**
- **department:** From `program` field in student data
- **year:** From `current_year` field
- **semester:** From `current_semester` field

**Example Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "x-student-data: {\"student_id\":25,\"token\":\"...\",\"isAuthenticated\":true,\"program\":\"Computer Science\",\"current_year\":\"2024\",\"current_semester\":\"1\"}" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the marking scheme?"}'
```

---

## Implementation in Next.js

### RAG Client Setup

```typescript
// Automatically sends student cookie as x-student-data header
const response = await ragClient.chat({
  question: "What are the prerequisites?"
});

// Admin ingest with Bearer token
await ragClient.adminIngest(
  {
    pdf_url: "https://cloudinary.com/syllabus.pdf",
    dept: "Computer Science",
    year: "2024"
  },
  "rag_studentpath_admin_2026"
);
```

### Component Usage

**For Students:**
```typescript
// Student page automatically:
// 1. Reads student cookie
// 2. Extracts dept, year, semester
// 3. Sends with every chat request
// 4. API auto-filters by these values

<ChatInterface />
```

**For Admins:**
```typescript
// Admin panel accepts:
// - PDF URL (from Cloudinary)
// - Department
// - Year
// No need to provide semester/course_code - extracted from PDF

<AdminIngestPanel adminToken="rag_studentpath_admin_2026" />
```

---

## Key Benefits

✅ **Simplified Admin Input:** Only 3 fields (pdf_url, dept, year)

✅ **Automatic Student Filtering:** Student's dept/year/semester used automatically

✅ **Secure Admin Access:** Bearer token protection on ingest endpoint

✅ **College-Based Data:** Student college context available for filtering

✅ **Multi-tenant Safe:** Each student sees their own program's content

✅ **Scalable:** Easy to extend with more student context (GPA, interests, etc.)

---

## Database Integration

Your Next.js backend already provides student data via the `/api/student` endpoint. This includes:

```typescript
{
  program: "Computer Science",        // Maps to dept
  current_year: "2024",               // Maps to year
  current_semester: "1",              // Maps to semester
  academic_interests: [],             // Optional filtering
  technical_skills: {},               // Optional filtering
  career_goals: {},                   // Optional filtering
}
```

All this data flows to RAG API → filters Pinecone queries → returns personalized results.

---

## File Changes Summary

| File | Changes |
|------|---------|
| `app/api/routes/ingest.py` | New `AdminIngestRequest` model, Bearer token validation, simplified metadata |
| `app/api/routes/chat.py` | New `StudentChatRequest` model, `x-student-data` header parsing, auto-filtering |
| `NEXTJS_STUDENT_AUTH.md` | **NEW** Complete Next.js integration guide with student auth |

---

## Next Steps

1. ✅ Update ingest route (DONE)
2. ✅ Update chat route (DONE)
3. → Follow `NEXTJS_STUDENT_AUTH.md` to integrate with your Next.js app
4. → Test with your student cookie
5. → Deploy to Render + Vercel

All documentation is in your project folder!
