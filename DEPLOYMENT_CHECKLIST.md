# Complete Deployment & Integration Checklist

Quick reference for deploying RAG service to Render and building Next.js frontend.

## Phase 1: Deploy Python RAG API to Render (5 minutes)

### Preparation
- [ ] Ensure `.env` has real API keys (OpenAI, Pinecone)
- [ ] Verify `requirements.txt` is complete
- [ ] Update `.env.example` (NO SECRETS!)
- [ ] Create `.gitignore` with `.env` entry
- [ ] Push code to GitHub

### Render Setup
```bash
# 1. Go to https://dashboard.render.com
# 2. Click "New +" > "Web Service"
# 3. Connect GitHub repo
# 4. Configure:
#    Name: rag-api-service
#    Build Command: pip install -r requirements.txt
#    Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
#    Instance: Starter ($7/mo)
# 5. Add Environment Variables:
OPENAI_API_KEY=sk-proj-xxx
PINECONE_API_KEY=pcsk_xxx
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=studentpath-syllabus
API_SECRET_KEY=your-secret
PORT=8000
WORKERS=4
ALLOWED_ORIGINS=["https://your-nextjs-app.vercel.app"]
```

### Verification
```bash
# After deployment, test:
curl https://rag-api-service.onrender.com/health

# Expected response:
# {"status":"healthy","services":{"openai":"connected","pinecone":"connected"}}
```

**✅ Your API URL:** `https://rag-api-service.onrender.com`

---

## Phase 2: Create Next.js Frontend (10 minutes)

### Project Creation
```bash
# Create new Next.js project
npx create-next-app@latest studentpath-rag --typescript --tailwind
cd studentpath-rag

# Install dependencies
npm install axios zustand react-markdown react-syntax-highlighter lucide-react

# Create directory structure
mkdir -p src/app src/components lib/{api,store,hooks}
```

### Copy Code Files
Create these files in your Next.js project:

1. **`lib/api/rag-client.ts`** - API client wrapper
2. **`lib/store/chat-store.ts`** - Zustand state management
3. **`components/ChatInterface.tsx`** - Main chat UI
4. **`components/MessageBubble.tsx`** - Message styling
5. **`components/IngestPanel.tsx`** - PDF upload
6. **`src/app/page.tsx`** - Home page
7. **.env.local** - Configuration

### Environment Setup
Create `.env.local`:
```
NEXT_PUBLIC_API_URL=https://rag-api-service.onrender.com
NEXT_PUBLIC_API_TIMEOUT=30000
```

### Test Locally
```bash
npm run dev
# Visit http://localhost:3000
```

---

## Phase 3: Deploy Next.js to Vercel (5 minutes)

### GitHub Push
```bash
git init
git add .
git commit -m "Next.js RAG frontend"
git remote add origin https://github.com/yourusername/studentpath-rag.git
git push -u origin main
```

### Vercel Deployment
Option A: Using CLI
```bash
npm install -g vercel
vercel
# Follow prompts
```

Option B: Using Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Click "Add New" > "Project"
3. Import GitHub repository
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://rag-api-service.onrender.com
   ```
5. Click "Deploy"

**✅ Your Frontend URL:** `https://studentpath-rag.vercel.app`

---

## Phase 4: Connect Frontend to API (2 minutes)

### Update CORS on Python API

Go to Render Dashboard:
1. Select `rag-api-service`
2. Go to Settings > Environment
3. Update:
   ```
   ALLOWED_ORIGINS=["https://studentpath-rag.vercel.app"]
   ```
4. Service auto-redeploys

### Test Integration
- Visit `https://studentpath-rag.vercel.app`
- Check green status banner (API Connected)
- Ask a test question
- Upload a PDF

---

## Phase 5: Optional Enhancements

### Add Authentication
```bash
npm install next-auth@beta
# Create [...nextauth].ts with GitHub/Google OAuth
```

### Add Analytics
```bash
npm install @vercel/analytics
# Add <Analytics /> to your layout
```

### Monitor Errors
```bash
npm install @sentry/nextjs
# Setup Sentry for error tracking
```

### Rate Limiting (Python)
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    ...
```

---

## File Structure Reference

```
RAG_Python_Service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── pinecone_service.py
│   │   ├── pdf_service.py
│   │   └── chat_service.py
│   ├── utils/
│   │   └── chunking.py
│   └── api/
│       └── routes/
│           ├── ingest.py
│           └── chat.py
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env (local only, not in git)
├── .env.example
├── .gitignore
├── RENDER_DEPLOYMENT.md
├── NEXTJS_INTEGRATION.md
└── README.md

studentpath-rag/ (Next.js)
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── favicon.ico
│   └── components/
│       ├── ChatInterface.tsx
│       ├── MessageBubble.tsx
│       └── IngestPanel.tsx
├── lib/
│   ├── api/
│   │   └── rag-client.ts
│   └── store/
│       └── chat-store.ts
├── public/
├── .env.local (local only)
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── package-lock.json
```

---

## Troubleshooting

### "Failed to fetch"
- Check if Render service is running: https://rag-api-service.onrender.com/health
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

### "API is not responding"
- Render free tier goes to sleep after 15 min inactivity
- Visit https://rag-api-service.onrender.com to wake it up
- Or upgrade to Starter plan ($7/mo)

### Long PDF upload timeout
- Default timeout is 30 seconds
- Increase in `.env.local`:
  ```
  NEXT_PUBLIC_API_TIMEOUT=60000
  ```
- Or upgrade Render instance

### CORS error in browser
- Check Python backend `.env` ALLOWED_ORIGINS
- Should include your Vercel domain
- Restart Render service after update

---

## Performance Tips

### Frontend Optimization
```typescript
// lib/hooks/useDebounce.ts
export function useDebounce(value: string, delay: number) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
}

// Use in search
const debouncedQuestion = useDebounce(question, 500);
```

### API Optimization
```python
# Add caching to chat responses
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_embedding(text: str):
    return embedding_service.create_embedding(text)
```

### Database Indexing
Pinecone already optimizes for speed - no action needed!

---

## Cost Breakdown (Monthly)

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| Render | Starter | $7 | Python RAG API |
| Vercel | Free | $0 | Next.js frontend |
| OpenAI | Pay-as-you-go | ~$10-50 | Depends on queries |
| Pinecone | Starter | $0 | Free tier with limits |
| **Total** | | **$17-57** | Per month |

---

## Security Checklist

- [ ] API keys NOT in `.env` tracked to GitHub
- [ ] `.env.example` has placeholder values only
- [ ] `.gitignore` includes `.env` and `node_modules`
- [ ] CORS limited to known domains only
- [ ] Rate limiting enabled on `/chat` endpoint
- [ ] Request validation with Pydantic
- [ ] HTTPS enforced (automatic with Render/Vercel)
- [ ] Environment variables set in Render dashboard (not in code)
- [ ] No sensitive data in Next.js public folder

---

## Success Indicators

✅ **API Deployment**
- Health check returns `status: healthy`
- OpenAI and Pinecone show `connected`
- No errors in Render logs

✅ **Frontend Deployment**
- Page loads at Vercel URL
- Green API status banner shows
- Can submit questions

✅ **Integration Complete**
- Questions return answers from RAG
- PDF upload creates chunks
- Sources and confidence shown
- No CORS errors in browser console

---

## Next Steps

1. **Monitor Performance**
   - Check Render metrics for CPU/memory
   - Monitor Vercel Analytics
   - Track OpenAI usage/costs

2. **Collect Feedback**
   - Add rating/feedback button
   - Track which questions fail
   - Monitor user behavior

3. **Improve Chunking**
   - Add table detection
   - Better section boundaries
   - Custom extraction for your domain

4. **Scale Up**
   - Upgrade Render to Standard ($12)
   - Add caching layer (Redis)
   - Implement request queuing

---

## Documentation Links

- **Python API:** See `RENDER_DEPLOYMENT.md`
- **Next.js Frontend:** See `NEXTJS_INTEGRATION.md`
- **Chunking Details:** See `app/utils/chunking.py`
- **API Endpoints:** See `API.md`

---

**Questions?** Check the troubleshooting sections or review the detailed guides in this repo.
