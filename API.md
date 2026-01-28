# 📖 Complete API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, endpoints use no authentication. For production, add:
- API key headers
- Bearer tokens
- OAuth2

---

## Health Check

### Endpoint
```
GET /
```

### Description
Check if all services (Pinecone, OpenAI) are operational.

### Response

**Status: 200 OK**

```json
{
  "status": "healthy",
  "pinecone_connected": true,
  "openai_connected": true
}
```

**Possible Status Values:**
- `healthy`: All services operational
- `degraded`: Some services unavailable
- `unhealthy`: Critical services down

---

## Ingest Syllabus (Admin)

### Endpoint
```
POST /ingest
```

### Description
Upload and process a syllabus PDF. Extracts text, creates embeddings, and stores vectors in Pinecone.

### Request Body

```json
{
  "pdf_url": "https://res.cloudinary.com/your-cloud/image/upload/v123/syllabus.pdf",
  "dept": "Computer Science",
  "year": "2024",
  "course_code": "CS301",
  "semester": "Fall"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pdf_url` | string | Yes | URL to PDF file (supports Cloudinary) |
| `dept` | string | Yes | Department name (e.g., "Computer Science") |
| `year` | string | Yes | Academic year (e.g., "2024") |
| `course_code` | string | No | Course code (e.g., "CS301") |
| `semester` | string | No | Semester (e.g., "Fall", "Spring") |

### Response

**Status: 200 OK**

```json
{
  "success": true,
  "message": "Successfully processed syllabus for Computer Science (2024)",
  "chunks_processed": 45,
  "vectors_stored": 45
}
```

### Error Responses

**Status: 422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["body", "pdf_url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Status: 500 Internal Server Error**
```json
{
  "detail": "Failed to fetch PDF: Connection timeout"
}
```

### Process Flow

1. **Fetch**: Download PDF from URL
2. **Extract**: Parse PDF and extract text
3. **Chunk**: Split text into 500-char chunks with 100-char overlap
4. **Embed**: Generate OpenAI embeddings for each chunk
5. **Store**: Upsert vectors with metadata to Pinecone

### Example Request (cURL)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://res.cloudinary.com/example/syllabus.pdf",
    "dept": "Computer Science",
    "year": "2024",
    "course_code": "CS301",
    "semester": "Fall"
  }'
```

### Example Request (Python)

```python
import requests

data = {
    "pdf_url": "https://res.cloudinary.com/example/syllabus.pdf",
    "dept": "Computer Science",
    "year": "2024",
    "course_code": "CS301",
    "semester": "Fall"
}

response = requests.post("http://localhost:8000/ingest", json=data)
print(response.json())
```

### Example Request (JavaScript)

```javascript
const data = {
    pdf_url: "https://res.cloudinary.com/example/syllabus.pdf",
    dept: "Computer Science",
    year: "2024",
    course_code: "CS301",
    semester: "Fall"
};

fetch('http://localhost:8000/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
})
.then(res => res.json())
.then(data => console.log(data))
```

---

## Delete Syllabus (Admin)

### Endpoint
```
DELETE /ingest
```

### Description
Remove all vectors for a specific department and year.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dept` | string | Yes | Department name |
| `year` | string | Yes | Academic year |

### Response

**Status: 200 OK**

```json
{
  "message": "Deleted syllabus for Computer Science (2024)"
}
```

### Error Responses

**Status: 500 Internal Server Error**
```json
{
  "detail": "Failed to delete vectors: Permission denied"
}
```

### Example Request

```bash
curl -X DELETE "http://localhost:8000/ingest?dept=Computer Science&year=2024"
```

---

## Ask Question (Student Chat)

### Endpoint
```
POST /chat
```

### Description
Ask a natural language question about a syllabus. Returns personalized answer based on department/year with source attribution.

### Request Body

```json
{
  "question": "What is the marking scheme?",
  "dept": "Computer Science",
  "year": "2024",
  "semester": "Fall"
}
```

### Parameters

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `question` | string | Yes | Min: 3, Max: 500 | Student question |
| `dept` | string | Yes | - | Department name |
| `year` | string | Yes | - | Academic year |
| `semester` | string | No | - | Semester (for filtering) |

### Response

**Status: 200 OK**

```json
{
  "answer": "The marking scheme consists of: assignments (20%), midterm exam (30%), final exam (50%). All assessments are cumulative.",
  "sources": [
    {
      "score": 0.92,
      "dept": "Computer Science",
      "year": "2024"
    }
  ],
  "confidence": "high"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer from GPT-4 based on syllabus context |
| `sources` | array | Source documents and similarity scores |
| `confidence` | string | Confidence level: "high" (>0.8), "medium" (0.6-0.8), "low" (<0.6) |

### Error Responses

**Status: 422 Unprocessable Entity** (Invalid question length)
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.string.too_short"
    }
  ]
}
```

**Status: 500 Internal Server Error**
```json
{
  "detail": "Embedding failed: Rate limit exceeded"
}
```

### Process Flow

1. **Embed**: Create embedding for the question
2. **Filter**: Apply dept/year/semester filters
3. **Query**: Search Pinecone for top 3 matching chunks
4. **Build Context**: Combine relevant passages
5. **Generate**: Call GPT-4 with context + question
6. **Respond**: Return answer with sources and confidence

### Example Request (cURL)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the marking scheme?",
    "dept": "Computer Science",
    "year": "2024",
    "semester": "Fall"
  }'
```

### Example Request (Python)

```python
import requests

data = {
    "question": "What is the marking scheme?",
    "dept": "Computer Science",
    "year": "2024",
    "semester": "Fall"
}

response = requests.post("http://localhost:8000/chat", json=data)
result = response.json()

print("Answer:", result["answer"])
print("Confidence:", result["confidence"])
for source in result["sources"]:
    print(f"  Score: {source['score']}")
```

### Example Request (JavaScript)

```javascript
const data = {
    question: "What is the marking scheme?",
    dept: "Computer Science",
    year: "2024",
    semester: "Fall"
};

fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
})
.then(res => res.json())
.then(data => {
    console.log("Answer:", data.answer);
    console.log("Confidence:", data.confidence);
    console.log("Sources:", data.sources);
})
```

### Example Questions

Good questions the system handles well:

- "What is the marking scheme?"
- "What is the attendance policy?"
- "How many assignments will there be?"
- "What is the course objectives?"
- "How should I prepare for the exam?"
- "What are the grading criteria?"
- "What textbooks are required?"
- "What is the late submission policy?"

---

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {
    "key": "value"
  }
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

---

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Successful ingestion, chat response |
| 422 | Validation Error | Invalid input format |
| 500 | Server Error | API key invalid, PDF extraction failed |

---

## Rate Limiting (Future)

Currently no rate limiting. Production deployment should implement:

```
- 100 requests/minute per IP for /chat
- 10 requests/minute per IP for /ingest
- 1000 requests/day per API key
```

---

## CORS Configuration

Allowed origins (configurable in `.env`):
```
http://localhost:3000
http://localhost:5000
https://yourdomain.com
```

---

## WebSocket Support (Future)

Planned for real-time chat responses:
```
WS ws://localhost:8000/ws/chat/{dept}/{year}
```

---

## API Clients

### Generate SDK

Using FastAPI, auto-generated clients are available:

**TypeScript/JavaScript:**
```bash
npx openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-fetch
```

**Python:**
```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python
```

---

## Testing Endpoints

### Using Postman

1. Import OpenAPI spec: `http://localhost:8000/openapi.json`
2. Auto-populated endpoints
3. Test each endpoint

### Using Swagger UI

Visit: `http://localhost:8000/docs`

- Interactive API documentation
- Try out endpoints directly
- View schemas

---

## Best Practices

1. **Cache Results**: Cache frequently asked questions
2. **Batch Ingestion**: Upload multiple PDFs in parallel
3. **Error Handling**: Implement retry logic with exponential backoff
4. **Logging**: Log all requests for debugging
5. **Monitoring**: Track API latency and error rates
6. **Validation**: Always validate input on client side

---

## Support

For issues:
1. Check `/docs` API documentation
2. Review error response details
3. Check application logs
4. Open GitHub issue with error details

---

**Last Updated**: January 2026
