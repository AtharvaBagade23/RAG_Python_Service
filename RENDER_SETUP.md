# Render Deployment Guide for RAG Service

## Quick Start

### Step 1: Push to GitHub

Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Ready for Render deployment"
git push -u origin main
```

Your repository: `https://github.com/AtharvaBagade23/RAG_Python_Service`

---

## Step 2: Create Render Service

### Option A: Using render.yaml (Recommended)

1. Go to https://dashboard.render.com
2. Click **"New +" → "Web Service"**
3. Select **"Deploy an existing repository"**
4. Connect GitHub and select `RAG_Python_Service`
5. Render will automatically detect `render.yaml` and apply configuration
6. Click **"Create Web Service"**

### Option B: Manual Configuration

1. Go to https://dashboard.render.com
2. Click **"New +" → "Web Service"**
3. Select **"Deploy an existing repository"**
4. Fill in:
   - **Name:** `rag-api-service`
   - **Repository:** `RAG_Python_Service`
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Starter` ($7/month)
5. Click **"Create Web Service"**

---

## Step 3: Add Environment Variables

In Render Dashboard:

1. Go to your service → **Settings**
2. Scroll to **"Environment"**
3. Add these variables:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
PINECONE_API_KEY=pcsk_your-actual-key-here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=studentpath-syllabus
API_SECRET_KEY=rag_studentpath_admin_2026
ALLOWED_ORIGINS=["https://studentpath-rag.vercel.app","https://yourdomain.com"]
PORT=8000
WORKERS=4
```

> ⚠️ **WARNING:** Never commit `.env` file with real keys to Git. Use Render Dashboard for secrets.

---

## Step 4: Deploy

After setting environment variables, Render automatically deploys your service.

**Watch the deployment:**
1. Go to your service in Render Dashboard
2. Click **"Logs"** tab
3. Wait for deployment to complete

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Step 5: Verify Deployment

Once deployed, your service is available at:
```
https://rag-api-service.onrender.com
```

Test the health endpoint:
```bash
curl https://rag-api-service.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "openai": "connected",
    "pinecone": "connected"
  }
}
```

---

## Build & Start Commands Explained

### Build Command
```bash
pip install -r requirements.txt
```
- Runs **once** during deployment
- Installs all Python dependencies
- Caches dependencies for faster redeployments

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- **`uvicorn`**: ASGI server for FastAPI
- **`app.main:app`**: Points to FastAPI app instance
- **`--host 0.0.0.0`**: Listen on all interfaces (required for Render)
- **`--port $PORT`**: Use Render's PORT environment variable (8000)

> Note: `$PORT` is automatically set by Render. Don't hardcode port numbers.

---

## File Structure for Deployment

Your repository should have:

```
RAG_Python_Service/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py
│   ├── models.py
│   ├── dependencies.py
│   ├── api/
│   │   └── routes/
│   │       ├── ingest.py
│   │       └── chat.py
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── pinecone_service.py
│   │   ├── pdf_service.py
│   │   └── chat_service.py
│   └── utils/
│       └── chunking.py
├── tests/
├── requirements.txt         # ✅ Must have
├── .env.example            # ✅ No real keys!
├── .gitignore              # ✅ Includes .env
├── render.yaml             # ✅ Configuration
├── Dockerfile              # ✅ Optional backup
└── README.md
```

---

## Troubleshooting

### Deployment Fails at Build Step

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Ensure `requirements.txt` is in repository root
```bash
ls -la requirements.txt
```

### Service won't start (504 timeout)

**Error:** Service keeps restarting

**Solutions:**
1. Check logs for Python errors: Render Dashboard → Logs
2. Verify environment variables are set correctly
3. Check if API keys are valid
4. Ensure port is `$PORT` not hardcoded

### High Memory Usage

**Issue:** Service runs out of memory

**Solutions:**
- Reduce `WORKERS` to 1 in environment
- Upgrade to Standard plan ($12/month)
- Check for memory leaks in PDF processing

### "Unhealthy" Status

**Issue:** Health check failing

**Solutions:**
1. Verify all environment variables set
2. Check OpenAI API key validity
3. Check Pinecone connection
4. Check Render logs for errors

```bash
# Test locally
curl http://localhost:8000/health
```

---

## Monitoring & Logs

### View Logs
```bash
# In Render Dashboard
1. Select your service
2. Click "Logs" tab
3. View real-time output
```

### Monitor Metrics
```bash
1. Select your service
2. Click "Metrics" tab
3. View CPU, Memory, Network usage
```

### Set Up Alerts (Optional)
```bash
1. Select your service
2. Click "Alerts" tab
3. Create custom alerts
```

---

## Scaling & Optimization

### Vertical Scaling (Upgrade Instance)
- Starter: 512MB RAM, 0.5 CPU ($7/month)
- Standard: 1GB RAM, 1 CPU ($12/month)
- Pro: 2GB RAM, 2 CPU ($29/month)

### Horizontal Scaling
Use Render's load balancer to add more instances:
```bash
1. Service Settings → Instance count
2. Set to 2 or more
3. Render auto-distributes traffic
```

### Performance Tips
- **Caching**: Add Redis for embedding cache
- **CDN**: Use Cloudflare for PDF URLs
- **Async**: FastAPI already uses async/await
- **Batch Processing**: Group multiple requests

---

## Auto-Deploy Configuration

With `render.yaml`, every push to `main` branch auto-deploys:

```bash
# Trigger deployment
git push origin main
```

Render automatically:
1. Detects code changes
2. Builds new image
3. Runs start command
4. Performs health check
5. Routes traffic to new instance

**Disable auto-deploy:** Render Dashboard → Settings → Auto-Deploy: Off

---

## Production Checklist

- [ ] `requirements.txt` has all dependencies
- [ ] `.gitignore` includes `.env`
- [ ] `.env.example` has NO real keys
- [ ] Environment variables set in Render Dashboard
- [ ] Health endpoint returns "healthy"
- [ ] API keys have correct permissions
- [ ] Pinecone index is initialized
- [ ] CORS configured with your domain
- [ ] Rate limiting enabled (optional)
- [ ] Error monitoring setup (Sentry recommended)

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Render Starter | $7/month | Python RAG API |
| OpenAI API | $10-50/month | Depends on usage |
| Pinecone Starter | Free | Up to 100K vectors |
| **Total** | **$17-57/month** | Minimal viable setup |

---

## Next Steps

1. ✅ Create `render.yaml` (DONE)
2. ✅ Push to GitHub (DONE)
3. → Deploy to Render (Follow steps above)
4. → Get your API URL: `https://rag-api-service.onrender.com`
5. → Integrate with Next.js frontend
6. → Deploy Next.js to Vercel
7. → Update CORS and test end-to-end

---

## Useful Commands

```bash
# Test local build/start before deploying
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check if requirements.txt is valid
pip install -r requirements.txt --dry-run

# View Render logs (requires Render CLI)
render logs -f
```

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Uvicorn Docs:** https://www.uvicorn.org/
- **Python on Render:** https://render.com/docs/deploy-python

---

**Deployment Date:** January 28, 2026
**Status:** Ready for Render
