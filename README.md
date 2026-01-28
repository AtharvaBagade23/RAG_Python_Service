# 🚀 StudentPath RAG Service

A production-ready Python RAG (Retrieval-Augmented Generation) service that enables students to ask natural language questions about their syllabus and get personalized answers powered by GPT-4 and Pinecone vector database.

## 📋 Features

- **PDF Ingestion**: Admin endpoint to upload and process syllabus PDFs from Cloudinary
- **Smart Chunking**: Intelligent text splitting with overlap for better context preservation
- **Vector Embeddings**: OpenAI embeddings (text-embedding-3-large) for semantic search
- **Vector Database**: Pinecone serverless for fast, scalable similarity search
- **RAG-based Chat**: GPT-4o-mini powered Q&A with source attribution
- **Department-Year Filtering**: Personalized answers based on student context
- **Health Monitoring**: Service health checks for all integrations
- **Docker Ready**: Complete Docker and Docker Compose setup
- **FastAPI**: Modern async Python framework with automatic API documentation

## 📁 Project Structure

```
rag-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment & settings
│   ├── models.py               # Pydantic models
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── ingest.py      # Admin PDF ingestion
│   │       └── chat.py        # Student chat endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py     # PDF fetching & parsing
│   │   ├── embedding_service.py # OpenAI embeddings
│   │   ├── pinecone_service.py  # Vector DB operations
│   │   └── chat_service.py      # RAG chat logic
│   │
│   └── utils/
│       ├── __init__.py
│       └── chunking.py        # Text chunking utilities
│
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py         # Ingestion endpoint tests
│   └── test_chat.py           # Chat endpoint tests
│
├── .env.example               # Environment variables template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Setup & Installation

### Prerequisites

- Python 3.11+
- OpenAI API key (for embeddings and chat)
- Pinecone API key and index
- Virtual environment (recommended)

### Local Development Setup

#### 1. Clone and Navigate

```bash
cd c:\Users\ADMIN\Desktop\RAG_Python_Service
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
copy .env.example .env
# Edit .env with your actual API keys
```

Fill in the `.env` file with:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX_NAME`: Your Pinecone index name
- `API_SECRET_KEY`: A secret key for admin operations

#### 5. Run the Service

**Option A: Direct Python**

```bash
python -m app.main
```

**Option B: Uvicorn**

```bash
uvicorn app.main:app --reload --port 8000
```

The service will be available at `http://localhost:8000`

### Docker Setup

#### Build and Run with Docker Compose

```bash
docker-compose up --build
```

#### Or Manual Docker

```bash
docker build -t rag-service .
docker run -p 8000:8000 --env-file .env rag-service
```

## 📡 API Endpoints

### 1. Health Check

```bash
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "pinecone_connected": true,
  "openai_connected": true
}
```

### 2. Ingest Syllabus (Admin)

```bash
POST /ingest
Content-Type: application/json

{
  "pdf_url": "https://res.cloudinary.com/.../syllabus.pdf",
  "dept": "Computer Science",
  "year": "2024",
  "course_code": "CS301",
  "semester": "Fall"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed syllabus for Computer Science (2024)",
  "chunks_processed": 45,
  "vectors_stored": 45
}
```

### 3. Delete Syllabus (Admin)

```bash
DELETE /ingest?dept=Computer Science&year=2024
```

**Response:**
```json
{
  "message": "Deleted syllabus for Computer Science (2024)"
}
```

### 4. Ask Question (Student)

```bash
POST /chat
Content-Type: application/json

{
  "question": "What is the marking scheme?",
  "dept": "Computer Science",
  "year": "2024",
  "semester": "Fall"
}
```

**Response:**
```json
{
  "answer": "The marking scheme consists of: assignments (20%), midterm (30%), final exam (50%). All assessments are cumulative.",
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

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_chat.py -v
pytest tests/test_ingest.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

## ⚙️ Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | - | OpenAI API key (required) |
| `PINECONE_API_KEY` | string | - | Pinecone API key (required) |
| `PINECONE_INDEX_NAME` | string | studentpath-syllabus | Pinecone index name |
| `PINECONE_ENVIRONMENT` | string | us-east-1 | Pinecone region |
| `EMBEDDING_MODEL` | string | text-embedding-3-large | OpenAI embedding model |
| `EMBEDDING_DIMENSION` | int | 3072 | Embedding vector dimensions |
| `CHAT_MODEL` | string | gpt-4o-mini | GPT model for responses |
| `TEMPERATURE` | float | 0.2 | GPT temperature (0-1) |
| `MAX_TOKENS` | int | 1000 | Max tokens in response |
| `CHUNK_SIZE` | int | 500 | Characters per text chunk |
| `CHUNK_OVERLAP` | int | 100 | Overlap between chunks |
| `PORT` | int | 8000 | Server port |
| `WORKERS` | int | 4 | Uvicorn worker count |
| `API_SECRET_KEY` | string | - | Admin secret key |
| `ALLOWED_ORIGINS` | string | * | CORS allowed origins |

## 🏗️ Architecture

### Data Flow

```
PDF Upload
    ↓
PDF Service (fetch + extract)
    ↓
Text Chunking
    ↓
Embedding Service (OpenAI)
    ↓
Pinecone Service (store vectors)
    ↓
Vector Database
```

### Chat Flow

```
Student Question
    ↓
Embedding Service (encode question)
    ↓
Pinecone Query (similarity search)
    ↓
Chat Service (build prompt)
    ↓
GPT-4 API (generate answer)
    ↓
Response to Student
```

## 🔐 Security

### Best Practices Implemented

1. **Environment Variables**: Sensitive keys stored in `.env` (not in repo)
2. **Input Validation**: Pydantic models validate all inputs
3. **CORS Middleware**: Configured and adjustable
4. **Error Handling**: Comprehensive exception handling
5. **API Keys**: Securely passed to external services

### Recommended Security Enhancements

1. Add API key authentication for admin endpoints
2. Implement rate limiting (use `slowapi`)
3. Add request logging and monitoring
4. Use HTTPS only in production
5. Add API versioning
6. Implement refresh token for long-lived sessions

## 🚀 Deployment

### Render.com (Recommended)

1. **Create New Web Service** on Render
2. **Connect GitHub Repository**
3. **Set Environment Variables** in Render dashboard
4. **Build Command**:
   ```
   pip install -r requirements.txt
   ```
5. **Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. **Deploy**

### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set PINECONE_API_KEY=pcsk_...
git push heroku main
```

### AWS (ECS/Fargate)

1. Build Docker image
2. Push to ECR
3. Create ECS task definition
4. Deploy to Fargate

## 📊 Performance Tuning

### Optimization Tips

- **Chunk Size**: Increase for longer documents, decrease for granular answers
- **Overlap**: Increase (100-200) to prevent missing context
- **Top-K**: Adjust `top_k=3` in Pinecone query for more/fewer results
- **Temperature**: Lower (0.1-0.3) for factual answers, higher (0.7-1.0) for creative
- **Batch Processing**: Process embeddings in batches (100 at a time)

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Errors

```
ValueError: Embedding failed: Invalid API key
```

**Solution**: Check `.env` file has correct API keys without extra spaces

#### 2. Pinecone Connection Issues

```
pinecone.exceptions.PineconeException: Failed to connect
```

**Solution**: Verify Pinecone API key and region in `.env`

#### 3. PDF Extraction Errors

```
ValueError: No text extracted from PDF
```

**Solution**: Ensure PDF is text-based (not scanned image)

#### 4. Port Already in Use

```
OSError: [Errno 48] Address already in use
```

**Solution**: Change PORT in `.env` or kill process on 8000

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.0 | Web framework |
| uvicorn | 0.27.0 | ASGI server |
| pydantic | 2.5.3 | Data validation |
| pydantic-settings | 2.1.0 | Settings management |
| python-dotenv | 1.0.0 | Environment variables |
| pdfplumber | 0.10.3 | PDF text extraction |
| PyPDF2 | 3.0.1 | PDF processing |
| openai | 1.10.0 | OpenAI API |
| pinecone-client | 3.0.0 | Pinecone vector DB |
| requests | 2.31.0 | HTTP client |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

For issues, questions, or suggestions:
- Open a GitHub Issue
- Check existing documentation
- Review test cases for usage examples

## 🎯 Roadmap

- [ ] Add authentication with JWT tokens
- [ ] Implement rate limiting
- [ ] Add request logging with Loguru
- [ ] Setup monitoring with Sentry
- [ ] Add multi-language support
- [ ] Implement caching layer (Redis)
- [ ] Add web UI for admin panel
- [ ] Support for other vector DBs (Weaviate, Milvus)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Embeddings by [OpenAI](https://openai.com/)
- Vectors stored in [Pinecone](https://www.pinecone.io/)
- PDF processing with [pdfplumber](https://github.com/jsvine/pdfplumber)

---

**Happy Building! 🚀**
#   R A G _ P y t h o n _ S e r v i c e  
 