# 🎯 Command Reference Guide

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Running the Service](#running-the-service)
3. [Testing](#testing)
4. [API Testing](#api-testing)
5. [Docker Commands](#docker-commands)
6. [Useful Utilities](#useful-utilities)

---

## Environment Setup

### Create Virtual Environment
```powershell
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

### Activate Virtual Environment
```powershell
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### Deactivate Virtual Environment
```powershell
deactivate
```

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Update Dependencies
```powershell
pip install --upgrade -r requirements.txt
```

### Check Installed Packages
```powershell
pip list
pip list | findstr fastapi  # Search for specific package
```

### Freeze Dependencies
```powershell
pip freeze > requirements.txt
```

---

## Running the Service

### Option 1: Direct Python Execution
```powershell
python -m app.main
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Option 2: Uvicorn (Recommended for Development)
```powershell
# Basic
uvicorn app.main:app

# With reload (auto-restart on code changes)
uvicorn app.main:app --reload

# Custom port
uvicorn app.main:app --port 8001

# Custom host
uvicorn app.main:app --host 0.0.0.0

# Multiple workers
uvicorn app.main:app --workers 4

# Combined options
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

### Option 3: Gunicorn (Production)
```powershell
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app.main:app"
```

### Stop the Service
```powershell
# Press Ctrl+C in the terminal running the service
```

---

## Testing

### Run All Tests
```powershell
pytest tests/ -v
```

### Run Specific Test File
```powershell
pytest tests/test_chat.py -v
pytest tests/test_ingest.py -v
```

### Run Specific Test Class
```powershell
pytest tests/test_chat.py::TestChatEndpoint -v
pytest tests/test_ingest.py::TestIngestEndpoint -v
```

### Run Specific Test Method
```powershell
pytest tests/test_chat.py::TestChatEndpoint::test_chat_success -v
```

### Run with Output
```powershell
# Show print statements
pytest tests/ -v -s

# Verbose with locals
pytest tests/ -vv
```

### Coverage Report
```powershell
pytest tests/ --cov=app --cov-report=html
pytest tests/ --cov=app --cov-report=term-missing
```

### Run Tests in Parallel
```powershell
pip install pytest-xdist
pytest tests/ -n auto
```

### Run Only Failed Tests
```powershell
pytest tests/ --lf
```

### Run Tests with Markers
```powershell
pytest tests/ -m "not slow"
```

---

## API Testing

### Using cURL (Command Line)

#### Health Check
```powershell
curl http://localhost:8000/

# Pretty print JSON
curl http://localhost:8000/ | ConvertFrom-Json
```

#### Ingest Syllabus
```powershell
$body = @{
    pdf_url = "https://example.com/syllabus.pdf"
    dept = "Computer Science"
    year = "2024"
    course_code = "CS301"
    semester = "Fall"
} | ConvertTo-Json

curl -X POST http://localhost:8000/ingest `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

#### Delete Syllabus
```powershell
curl -X DELETE "http://localhost:8000/ingest?dept=Computer Science&year=2024"
```

#### Ask Question
```powershell
$body = @{
    question = "What is the marking scheme?"
    dept = "Computer Science"
    year = "2024"
    semester = "Fall"
} | ConvertTo-Json

curl -X POST http://localhost:8000/chat `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

### Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/")
print(response.json())

# Ingest PDF
data = {
    "pdf_url": "https://example.com/syllabus.pdf",
    "dept": "Computer Science",
    "year": "2024"
}
response = requests.post(f"{BASE_URL}/ingest", json=data)
print(response.json())

# Chat
data = {
    "question": "What is the marking scheme?",
    "dept": "Computer Science",
    "year": "2024"
}
response = requests.post(f"{BASE_URL}/chat", json=data)
print(json.dumps(response.json(), indent=2))
```

### Using Postman

1. **Import OpenAPI**: `http://localhost:8000/openapi.json`
2. **Or Create Manually**:
   - Create new request
   - Method: GET/POST/DELETE
   - URL: http://localhost:8000/...
   - Headers: Content-Type: application/json
   - Body: JSON payload

### Using Swagger UI

1. Navigate to: `http://localhost:8000/docs`
2. Try each endpoint interactively
3. See request/response schemas
4. Copy cURL commands

### Using ReDoc

1. Navigate to: `http://localhost:8000/redoc`
2. View complete API documentation
3. Download OpenAPI spec

---

## Docker Commands

### Build Docker Image
```powershell
docker build -t rag-service .
```

### Run Docker Container
```powershell
# Basic
docker run -p 8000:8000 --env-file .env rag-service

# Interactive with terminal
docker run -it -p 8000:8000 --env-file .env rag-service

# Background (detached)
docker run -d -p 8000:8000 --env-file .env rag-service

# Custom port
docker run -p 8001:8000 --env-file .env rag-service

# With environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e PINECONE_API_KEY=pcsk_... \
  rag-service
```

### Docker Compose Commands

```powershell
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild without cache
docker-compose up --build --no-cache

# Run specific service
docker-compose up rag-service

# Scale services
docker-compose up --scale rag-service=3
```

### Docker Utilities

```powershell
# List running containers
docker ps

# List all containers
docker ps -a

# View container logs
docker logs <container-id>
docker logs -f <container-id>  # Follow logs

# Stop container
docker stop <container-id>

# Remove container
docker rm <container-id>

# List images
docker images

# Remove image
docker rmi rag-service

# Enter container shell
docker exec -it <container-id> /bin/bash

# Copy files from container
docker cp <container-id>:/app/logs ./logs
```

---

## Useful Utilities

### Virtual Environment Management

```powershell
# Check which Python is active
python --version
python -c "import sys; print(sys.executable)"

# Check where packages are installed
pip show fastapi

# List outdated packages
pip list --outdated

# Upgrade pip
python -m pip install --upgrade pip

# Uninstall package
pip uninstall package-name
```

### Project Structure

```powershell
# List directory structure
Get-ChildItem -Recurse -Directory

# Find files by pattern
Get-ChildItem -Recurse -Filter "*.py"

# Count Python files
(Get-ChildItem -Recurse -Filter "*.py").Count

# Show file sizes
Get-ChildItem -Recurse -File | Select-Object FullName, @{Name="SizeMB";Expression={$_.Length/1MB}}
```

### Git Commands

```powershell
# Initialize git
git init

# Add files
git add .

# Commit
git commit -m "Initial commit: Complete RAG service"

# Check status
git status

# View log
git log --oneline

# Create branch
git checkout -b feature/new-feature

# Merge branch
git merge feature/new-feature
```

### Port Management

```powershell
# Check if port is in use
netstat -ano | findstr :8000

# Kill process on port
taskkill /PID <PID> /F

# Check specific process
Get-NetTCPConnection -LocalPort 8000
```

### Environment & Config

```powershell
# View environment variables
Get-ChildItem Env:

# Set temporary environment variable
$env:OPENAI_API_KEY = "sk-..."

# Load .env file (manual)
$env_vars = Get-Content .env | Where-Object {$_ -notmatch '^\s*#'} | Where-Object {$_ -notmatch '^\s*$'}

# View .env content
Get-Content .env
```

### Monitoring & Performance

```powershell
# Check CPU/Memory usage
Get-Process python

# Real-time monitoring
while ($true) { Clear-Host; Get-Process python | Select-Object Name, CPU, Memory; Start-Sleep -Seconds 2 }

# Monitor port activity
netstat -ano | findstr LISTENING
```

---

## Development Workflow

### 1. Start Development
```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Start server with hot reload
uvicorn app.main:app --reload

# Open browser
Start-Process "http://localhost:8000/docs"
```

### 2. Make Changes
```powershell
# Edit files in VS Code or your editor
# Server auto-reloads on save
```

### 3. Test Changes
```powershell
# In a new terminal (keep server running)
pytest tests/ -v -s
```

### 4. Before Committing
```powershell
# Run all tests
pytest tests/ --cov=app

# Check code quality
pip install flake8
flake8 app/

# Format code
pip install black
black app/
```

### 5. Deploy
```powershell
# Build Docker image
docker build -t rag-service:1.0 .

# Push to registry
docker push <registry>/rag-service:1.0

# Or deploy via docker-compose
docker-compose -f docker-compose.yml up -d
```

---

## Troubleshooting Commands

### Common Issues

```powershell
# ModuleNotFoundError
pip install -r requirements.txt

# Port in use
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Virtual environment not activated
.\venv\Scripts\Activate.ps1

# Old Python cache
Remove-Item -Recurse __pycache__
Remove-Item -Recurse .pytest_cache

# Reinstall dependencies
Remove-Item venv -Recurse
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Debug Mode

```powershell
# Run with verbose output
python -m app.main --debug

# Run tests with debugging
pytest tests/ -v -s --tb=short

# Python debug REPL
python -m pdb app/main.py
```

---

## Reference Summary

| Task | Command |
|------|---------|
| Setup | `python -m venv venv` |
| Activate | `.\venv\Scripts\Activate.ps1` |
| Install | `pip install -r requirements.txt` |
| Run | `uvicorn app.main:app --reload` |
| Test | `pytest tests/ -v` |
| Docker | `docker-compose up --build` |
| Docs | `http://localhost:8000/docs` |

---

**Last Updated**: January 2026
**Status**: ✅ Complete Command Reference
