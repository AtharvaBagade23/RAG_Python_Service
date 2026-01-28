# 🚀 Quick Start Guide

## Step 1: Setup Environment

### Windows PowerShell
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### macOS/Linux
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys

1. **Get your API keys:**
   - OpenAI: https://platform.openai.com/api-keys
   - Pinecone: https://app.pinecone.io

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your keys:**
   ```env
   OPENAI_API_KEY=sk-your-key-here
   PINECONE_API_KEY=pcsk_your-key-here
   PINECONE_INDEX_NAME=studentpath-syllabus
   API_SECRET_KEY=your-secret-key
   ```

## Step 3: Start the Service

### Option A: Direct Python
```bash
python -m app.main
```

### Option B: Uvicorn (Recommended)
```bash
uvicorn app.main:app --reload --port 8000
```

### Option C: Docker
```bash
docker-compose up --build
```

## Step 4: Test the Service

### Health Check
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "status": "healthy",
  "pinecone_connected": true,
  "openai_connected": true
}
```

### Ingest a Syllabus
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://res.cloudinary.com/your-pdf.pdf",
    "dept": "Computer Science",
    "year": "2024",
    "course_code": "CS301",
    "semester": "Fall"
  }'
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the marking scheme?",
    "dept": "Computer Science",
    "year": "2024"
  }'
```

## Step 5: View API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Make sure virtual environment is activated and all dependencies installed
```bash
pip install -r requirements.txt
```

### Issue: API Key errors
**Solution**: Verify `.env` file has correct keys without extra spaces
```bash
cat .env  # View current values
```

### Issue: Pinecone connection error
**Solution**: Check API key and region in `.env`
```env
PINECONE_API_KEY=pcsk_...
PINECONE_ENVIRONMENT=us-east-1
```

### Issue: Port 8000 already in use
**Solution**: Use a different port
```bash
uvicorn app.main:app --port 8001
```

## Project Files Overview

- **`app/main.py`**: FastAPI application setup
- **`app/config.py`**: Configuration and settings
- **`app/models.py`**: Pydantic request/response models
- **`app/services/`**: Business logic (PDF, embeddings, chat, Pinecone)
- **`app/api/routes/`**: API endpoints (ingest, chat)
- **`app/utils/chunking.py`**: Text chunking utilities
- **`requirements.txt`**: Python dependencies
- **`Dockerfile`**: Docker image definition
- **`docker-compose.yml`**: Docker Compose configuration
- **`tests/`**: Unit and integration tests

## Next Steps

1. ✅ Setup and run the service
2. ✅ Test with sample PDFs
3. ✅ Verify Pinecone vectors are stored
4. ✅ Run unit tests
5. ✅ Deploy to production (Render, Heroku, AWS, etc.)

## Getting Help

- Check `README.md` for detailed documentation
- Review test files (`tests/test_*.py`) for usage examples
- Check FastAPI docs at http://localhost:8000/docs
- Review service code in `app/services/` directory

Happy building! 🎉
