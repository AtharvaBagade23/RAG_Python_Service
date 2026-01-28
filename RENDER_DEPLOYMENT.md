# Deploying RAG Service to Render

## Prerequisites
- Render account (https://render.com)
- GitHub repository with your code
- API keys ready (OpenAI, Pinecone)

## Step 1: Prepare Your Repository

### 1.1 Update `.env.example` (NO SECRETS IN REPO)
```bash
# .env.example - DO NOT include real keys!
OPENAI_API_KEY=sk-proj-your-key-here
PINECONE_API_KEY=pcsk_your-key-here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=studentpath-syllabus
PORT=8000
WORKERS=4
API_SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

### 1.2 Create `render.yaml` in project root
```yaml
services:
  - type: web
    name: rag-api-service
    runtime: python
    pythonVersion: 3.11
    
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
    
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    
    envVars:
      - key: PORT
        value: 8000
      - key: WORKERS
        value: 4
      - key: PYTHON_VERSION
        value: 3.11.0
    
    autoDeploy: true
    
    # Secret environment variables (set in Render dashboard)
    # - OPENAI_API_KEY
    # - PINECONE_API_KEY
    # - API_SECRET_KEY
```

### 1.3 Update `.gitignore`
```bash
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Step 2: Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial RAG service setup for Render deployment"
git branch -M main
git remote add origin https://github.com/your-username/RAG_Python_Service.git
git push -u origin main
```

## Step 3: Create Render Service

### 3.1 Sign in to Render Dashboard
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Select "Deploy an existing repository"
4. Connect your GitHub account
5. Select the RAG_Python_Service repository

### 3.2 Configure Service
- **Name:** `rag-api-service`
- **Environment:** `Python 3`
- **Region:** Choose closest to your users
- **Branch:** `main`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Starter ($7/month) or higher based on load

### 3.3 Add Environment Variables
In Render Dashboard → Settings → Environment:

```
OPENAI_API_KEY=sk-proj-your-actual-key
PINECONE_API_KEY=pcsk_your-actual-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=studentpath-syllabus
API_SECRET_KEY=your-production-secret-key
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com","https://your-nextjs-app.vercel.app"]
PORT=8000
WORKERS=4
PYTHON_VERSION=3.11.0
```

### 3.4 Deploy
- Click "Create Web Service"
- Render will auto-deploy from GitHub
- Service will be available at: `https://rag-api-service.onrender.com`

## Step 4: Verify Deployment

```bash
# Check health endpoint
curl https://rag-api-service.onrender.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00Z",
  "services": {
    "openai": "connected",
    "pinecone": "connected"
  }
}
```

## Step 5: Production Configuration

### 5.1 Update ALLOWED_ORIGINS
Add your Next.js app URL to `.env` on Render:
```
ALLOWED_ORIGINS=["https://your-nextjs-app.vercel.app","https://your-domain.com"]
```

### 5.2 Enable Auto-Deploy
- Dashboard → Settings → Auto-Deploy: `Yes`
- Every push to `main` branch auto-deploys

### 5.3 Monitor Logs
Dashboard → Logs tab to watch deployment and errors

## Useful Render Features

### Cron Jobs (Optional)
For periodic tasks like cache clearing:
```yaml
services:
  - type: cron
    name: cache-cleaner
    runtime: python
    startCommand: python scripts/cleanup.py
    schedule: "0 2 * * *"  # Daily at 2 AM
```

### Scaling
- **Vertical:** Upgrade instance type in Render dashboard
- **Horizontal:** Add more instances with load balancer

## Troubleshooting

### Service Won't Start
1. Check logs: Dashboard → Logs
2. Verify environment variables set
3. Check `requirements.txt` for version conflicts
4. Ensure Python 3.11 compatibility

### High Memory Usage
- Reduce `WORKERS` in environment
- Check for memory leaks in embeddings/chunking
- Monitor with Render's metrics

### Pinecone Connection Failed
- Verify API key is correct
- Check index name matches
- Ensure environment variable spelled correctly
- Wait 60 seconds after Render deployment completes

## CI/CD with GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger Render deployment
        run: |
          curl https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }}
```

## Cost Optimization

- **Starter Plan:** $7/month (512MB RAM, 0.5 CPU)
- **Standard Plan:** $12/month (1GB RAM, 1 CPU)
- **Performance Plan:** Variable pricing

For RAG service with ~10 concurrent users, Starter is sufficient.
Consider upgrade if:
- Timeout errors on long PDF processing
- Slow response times during peak hours
- Multiple simultaneous ingest requests

## Next Steps

1. ✅ Deploy to Render
2. ✅ Get production API URL
3. → Integrate with Next.js (see NEXTJS_INTEGRATION.md)
4. → Add authentication middleware
5. → Setup monitoring (Sentry)
6. → Configure rate limiting
