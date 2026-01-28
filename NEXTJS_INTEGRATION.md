# Integrating RAG API with Next.js Frontend

Complete guide to build a Next.js web application that uses your RAG service.

## Project Setup

### 1. Create Next.js Project

```bash
npx create-next-app@latest studentpath-rag --typescript --tailwind --eslint
cd studentpath-rag
```

Choose these options:
- **TypeScript:** Yes
- **ESLint:** Yes
- **Tailwind CSS:** Yes
- **App Router:** Yes
- **Use src directory:** Yes

### 2. Install Dependencies

```bash
npm install axios zustand react-markdown react-syntax-highlighter lucide-react
npm install -D @types/react-syntax-highlighter
```

**Package purposes:**
- `axios` - HTTP client with better error handling than fetch
- `zustand` - Lightweight state management
- `react-markdown` - Render markdown responses
- `react-syntax-highlighter` - Code syntax highlighting
- `lucide-react` - Beautiful icons

### 3. Environment Setup

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000

# For production (Render deployment)
# NEXT_PUBLIC_API_URL=https://rag-api-service.onrender.com
```

> **Important:** Variables with `NEXT_PUBLIC_` are exposed to browser. Don't put secrets there.

---

## API Integration Layer

### Create `lib/api/rag-client.ts`

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000');

interface IngestRequest {
  file: File;
  dept: string;
  year: string;
  doc_type: string;
  source: string;
}

interface IngestResponse {
  status: string;
  chunks_created: number;
  metadata: Record<string, string>;
  message: string;
}

interface ChatRequest {
  question: string;
  dept?: string;
  year?: string;
  semester?: string;
}

interface ChatResponse {
  answer: string;
  sources: Array<{
    chunk: string;
    metadata: Record<string, string>;
  }>;
  confidence: 'high' | 'medium' | 'low';
  tokens_used: number;
}

interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    openai: 'connected' | 'disconnected';
    pinecone: 'connected' | 'disconnected';
  };
}

class RAGClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for global error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 422) {
          throw new Error(`Validation Error: ${JSON.stringify(error.response.data)}`);
        }
        if (error.response?.status === 500) {
          throw new Error('Server error. Please try again later.');
        }
        if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
          throw new Error('Connection timeout. Check if API is running.');
        }
        throw error;
      }
    );
  }

  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>('/health');
    return data;
  }

  async ingest(request: IngestRequest): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('dept', request.dept);
    formData.append('year', request.year);
    formData.append('doc_type', request.doc_type);
    formData.append('source', request.source);

    const { data } = await this.client.post<IngestResponse>('/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await this.client.post<ChatResponse>('/chat', request);
    return data;
  }

  async deleteSyllabus(dept: string, year: string): Promise<{ status: string; message: string }> {
    const { data } = await this.client.delete(`/ingest`, {
      data: { dept, year },
    });
    return data;
  }

  getApiUrl(): string {
    return API_BASE_URL;
  }
}

export const ragClient = new RAGClient();
```

### Create `lib/store/chat-store.ts` (State Management)

```typescript
import { create } from 'zustand';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    chunk: string;
    metadata: Record<string, string>;
  }>;
  confidence?: 'high' | 'medium' | 'low';
  timestamp: Date;
}

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  dept: string;
  year: string;
  semester: string;

  // Actions
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (dept: string, year: string, semester: string) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  error: null,
  dept: 'Computer Science',
  year: '2024',
  semester: '1',

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  clearMessages: () => set({ messages: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  setFilters: (dept, year, semester) => set({
    dept,
    year,
    semester,
  }),
}));
```

---

## Components

### Create `components/ChatInterface.tsx`

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2 } from 'lucide-react';
import { ragClient } from '@/lib/api/rag-client';
import { useChatStore, Message } from '@/lib/store/chat-store';
import MessageBubble from './MessageBubble';

export default function ChatInterface() {
  const {
    messages,
    isLoading,
    error,
    dept,
    year,
    semester,
    addMessage,
    setLoading,
    setError,
    clearMessages,
  } = useChatStore();

  const [question, setQuestion] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setQuestion('');
    setLoading(true);
    setError(null);

    try {
      const response = await ragClient.chat({
        question,
        dept,
        year,
        semester,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        timestamp: new Date(),
      };

      addMessage(assistantMessage);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response';
      setError(errorMessage);

      const errorBubble: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`,
        timestamp: new Date(),
      };
      addMessage(errorBubble);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto flex items-center gap-2">
          <MessageCircle className="w-6 h-6 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">StudentPath RAG</h1>
            <p className="text-sm text-gray-600">
              {dept} - Year {year}, Semester {semester}
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-20">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>Ask me anything about the course syllabus!</p>
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about the course..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Send
            </button>
          </div>
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </form>
      </div>
    </div>
  );
}
```

### Create `components/MessageBubble.tsx`

```typescript
'use client';

import { Message } from '@/lib/store/chat-store';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-2xl px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
        }`}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            components={{
              code: ({ node, inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-gray-100 px-2 py-1 rounded text-sm" {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown
        </div>

        {/* Sources & Confidence */}
        {!isUser && (message.sources || message.confidence) && (
          <div className="mt-3 pt-3 border-t border-gray-200 text-xs">
            {message.confidence && (
              <div className="flex items-center gap-1 mb-2">
                {message.confidence === 'high' && (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span className="text-green-700">
                      High confidence match
                    </span>
                  </>
                )}
                {message.confidence === 'medium' && (
                  <>
                    <AlertCircle className="w-4 h-4 text-yellow-600" />
                    <span className="text-yellow-700">
                      Medium confidence match
                    </span>
                  </>
                )}
                {message.confidence === 'low' && (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <span className="text-red-700">
                      Low confidence match
                    </span>
                  </>
                )}
              </div>
            )}

            {message.sources && message.sources.length > 0 && (
              <details className="cursor-pointer">
                <summary className="font-semibold text-gray-600 hover:text-gray-900">
                  View sources ({message.sources.length})
                </summary>
                <div className="mt-2 space-y-1">
                  {message.sources.map((source, i) => (
                    <div key={i} className="bg-gray-50 p-2 rounded text-xs">
                      <p className="font-mono text-gray-700 line-clamp-2">
                        {source.chunk.substring(0, 100)}...
                      </p>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

### Create `components/IngestPanel.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { ragClient } from '@/lib/api/rag-client';

export default function IngestPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [dept, setDept] = useState('Computer Science');
  const [year, setYear] = useState('2024');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select a PDF file');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const response = await ragClient.ingest({
        file,
        dept,
        year,
        doc_type: 'syllabus',
        source: 'Web Upload',
      });

      setMessage(`✅ Success! Created ${response.chunks_created} chunks.`);
      setFile(null);
      setDept('Computer Science');
      setYear('2024');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Upload failed';
      setMessage(`❌ Error: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-blue-200">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Upload className="w-5 h-5" />
        Upload Syllabus
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Department
          </label>
          <input
            type="text"
            value={dept}
            onChange={(e) => setDept(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Year
          </label>
          <input
            type="text"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            PDF File
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="w-full"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !file}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload PDF
            </>
          )}
        </button>

        {message && (
          <div
            className={`p-3 rounded text-sm ${
              message.startsWith('✅')
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {message}
          </div>
        )}
      </form>
    </div>
  );
}
```

---

## Pages

### Create `src/app/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import IngestPanel from '@/components/IngestPanel';
import { ragClient } from '@/lib/api/rag-client';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const [health, setHealth] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const status = await ragClient.health();
        setHealth(status);
      } catch (err) {
        setHealth({ status: 'unhealthy', error: String(err) });
      } finally {
        setIsLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Status Banner */}
      {!isLoading && (
        <div
          className={`px-4 py-3 flex items-center gap-2 ${
            health?.status === 'healthy'
              ? 'bg-green-50 text-green-800 border-b border-green-200'
              : 'bg-red-50 text-red-800 border-b border-red-200'
          }`}
        >
          {health?.status === 'healthy' ? (
            <CheckCircle2 className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span className="text-sm font-medium">
            {health?.status === 'healthy'
              ? 'API is connected and operational'
              : 'API is not responding. Make sure the server is running.'}
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 p-4 h-screen lg:h-auto">
        {/* Chat Area */}
        <div className="lg:col-span-3">
          <ChatInterface />
        </div>

        {/* Sidebar */}
        <div className="hidden lg:block space-y-4">
          {health?.status === 'healthy' && <IngestPanel />}
        </div>
      </div>
    </div>
  );
}
```

---

## Configuration

### Update `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Allow CORS for API calls
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/health',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/health`,
        },
        {
          source: '/api/chat',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/chat`,
        },
        {
          source: '/api/ingest',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/ingest`,
        },
      ],
    };
  },

  // Image optimization
  images: {
    remotePatterns: [],
  },
};

module.exports = nextConfig;
```

---

## Deployment to Vercel

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Next.js RAG frontend"
git remote add origin https://github.com/your-username/studentpath-rag.git
git push -u origin main
```

### 2. Deploy to Vercel

```bash
npm install -g vercel
vercel
```

Or use Vercel Dashboard:
1. Go to https://vercel.com
2. Click "Import Project"
3. Select repository
4. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://rag-api-service.onrender.com
   ```
5. Click Deploy

### 3. Update CORS Settings

Update your Python API's `.env` on Render:
```
ALLOWED_ORIGINS=["https://studentpath-rag.vercel.app"]
```

---

## Complete Architecture

```
┌─────────────────────────────────────────────┐
│  Next.js Frontend (Vercel)                   │
│  - ChatInterface                             │
│  - IngestPanel                               │
│  - MessageBubble                             │
└──────────────────┬──────────────────────────┘
                   │ HTTPS
                   ↓
┌─────────────────────────────────────────────┐
│  RAG API (Render)                            │
│  - FastAPI app.main                          │
│  - /health, /chat, /ingest endpoints         │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ↓           ↓           ↓
    OpenAI      Pinecone    pdfplumber
    (Embeddings) (VectorDB)  (PDF Parse)
```

---

## Security Best Practices

1. **Never expose API keys in frontend**
   - Keep `OPENAI_API_KEY` and `PINECONE_API_KEY` server-side only
   - Use `NEXT_PUBLIC_` prefix only for non-sensitive config

2. **Rate limiting** (on Python backend)
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/chat")
   @limiter.limit("10/minute")
   async def chat(request: ChatRequest):
       ...
   ```

3. **CORS** (Already configured on Python backend)
   ```python
   allow_origins=["https://studentpath-rag.vercel.app"]
   ```

4. **Request validation** (Already in place with Pydantic)

---

## Troubleshooting

### Frontend can't connect to API
1. Check `NEXT_PUBLIC_API_URL` in `.env.local`
2. Verify API is running: `curl https://rag-api-service.onrender.com/health`
3. Check CORS settings in Python backend

### CORS errors
- Update `ALLOWED_ORIGINS` in Python `.env` on Render
- Restart Render service

### Slow responses
- Check if Pinecone index is healthy
- Verify OpenAI API quotas
- Check Render instance size

---

## What's Next

✅ Frontend can chat with RAG backend
✅ Upload new syllabi
✅ View sources and confidence scores

🔄 Consider adding:
- [ ] User authentication (NextAuth.js)
- [ ] PDF preview before upload
- [ ] Export chat history
- [ ] Dark mode toggle
- [ ] Feedback/rating system
- [ ] Analytics dashboard
