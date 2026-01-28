# Next.js RAG Integration with Student Authentication

Guide to integrate your updated RAG API with your Next.js application using student authentication cookies.

## Overview

Your RAG API now expects:
- **Admin Ingest:** Bearer token authorization
- **Student Chat:** Student data in `x-student-data` header (from your cookie)
- **Auto-filtering:** By department, year, and semester (from student profile)

---

## 1. Create RAG Client with Auth

Create `lib/api/rag-client.ts`:

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_RAG_API_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_RAG_API_TIMEOUT || '30000');

interface StudentData {
  student_id: number;
  first_name: string;
  last_name: string;
  email: string;
  token: string;
  isAuthenticated: boolean;
  isAdmin: boolean;
  college_id?: number;
  college_name?: string;
  program?: string;
  current_year?: string;
  current_semester?: string;
}

interface ChatRequest {
  question: string;
}

interface ChatResponse {
  answer: string;
  sources: Array<{
    chunk: string;
    metadata: Record<string, string>;
  }>;
  confidence: 'high' | 'medium' | 'low';
}

interface IngestRequest {
  pdf_url: string;
  dept: string;
  year: string;
}

interface IngestResponse {
  success: boolean;
  message: string;
  chunks_processed: number;
  vectors_stored: number;
}

class RAGClient {
  private client: AxiosInstance;
  private adminToken?: string;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          throw new Error('Unauthorized. Please login again.');
        }
        if (error.response?.status === 403) {
          throw new Error('Access denied. Admin token invalid.');
        }
        if (error.response?.status === 422) {
          throw new Error(`Validation Error: ${JSON.stringify(error.response.data)}`);
        }
        if (error.code === 'ECONNABORTED') {
          throw new Error('Request timeout. Check if API is running.');
        }
        throw error;
      }
    );
  }

  /**
   * Student Chat - Automatically uses student data from cookie
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const studentCookie = Cookies.get('student_data');
    
    if (!studentCookie) {
      throw new Error('Student data not found in cookies. Please login.');
    }

    try {
      const studentData = JSON.parse(studentCookie) as StudentData;

      const { data } = await this.client.post<ChatResponse>(
        '/chat',
        request,
        {
          headers: {
            'x-student-data': JSON.stringify(studentData),
          },
        }
      );

      return data;
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('Invalid student cookie data');
      }
      throw error;
    }
  }

  /**
   * Admin Ingest - Requires admin Bearer token
   */
  async adminIngest(
    request: IngestRequest,
    adminToken: string
  ): Promise<IngestResponse> {
    const { data } = await this.client.post<IngestResponse>(
      '/ingest',
      request,
      {
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
      }
    );

    return data;
  }

  /**
   * Set admin token for session
   */
  setAdminToken(token: string): void {
    this.adminToken = token;
  }

  /**
   * Health check
   */
  async health(): Promise<any> {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export const ragClient = new RAGClient();
export type { StudentData, ChatRequest, ChatResponse, IngestRequest, IngestResponse };
```

---

## 2. Create State Management

Create `lib/store/chat-store.ts`:

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

  // Actions
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  clearMessages: () => set({ messages: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),
}));
```

---

## 3. Chat Component

Create `components/ChatInterface.tsx`:

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2 } from 'lucide-react';
import { ragClient } from '@/lib/api/rag-client';
import { useChatStore, Message } from '@/lib/store/chat-store';
import MessageBubble from './MessageBubble';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

export default function ChatInterface() {
  const { messages, isLoading, error, addMessage, setLoading, setError } = useChatStore();
  const [question, setQuestion] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check authentication on mount
  useEffect(() => {
    const studentCookie = Cookies.get('student_data');
    if (!studentCookie) {
      router.push('/login');
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

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
            <p className="text-sm text-gray-600">Ask about your syllabus</p>
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

---

## 4. Admin Ingest Panel

Create `components/AdminIngestPanel.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { ragClient } from '@/lib/api/rag-client';

interface AdminIngestPanelProps {
  adminToken: string;
}

export default function AdminIngestPanel({ adminToken }: AdminIngestPanelProps) {
  const [pdfUrl, setPdfUrl] = useState('');
  const [dept, setDept] = useState('Computer Science');
  const [year, setYear] = useState('2024');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pdfUrl || !dept || !year) {
      setMessage('❌ Please fill all fields');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      ragClient.setAdminToken(adminToken);
      
      const response = await ragClient.adminIngest({
        pdf_url: pdfUrl,
        dept,
        year,
      });

      setMessage(`✅ Success! Created ${response.chunks_processed} chunks.`);
      setPdfUrl('');
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
    <div className="bg-white rounded-lg shadow-md p-6 border border-amber-200">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Upload className="w-5 h-5" />
        Admin: Upload Syllabus
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            PDF URL (Cloudinary)
          </label>
          <input
            type="url"
            value={pdfUrl}
            onChange={(e) => setPdfUrl(e.target.value)}
            placeholder="https://cloudinary.com/..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            disabled={isLoading}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <input
              type="text"
              value={dept}
              onChange={(e) => setDept(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              disabled={isLoading}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload Syllabus
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

## 5. Setup Environment

Create `.env.local`:

```
# RAG API Configuration
NEXT_PUBLIC_RAG_API_URL=http://localhost:8000
# For production: https://rag-api-service.onrender.com
NEXT_PUBLIC_RAG_API_TIMEOUT=30000

# Admin Token (from your Python .env API_SECRET_KEY)
NEXT_PUBLIC_ADMIN_TOKEN=rag_studentpath_admin_2026
```

---

## 6. Create Student Page

Create `app/student/page.tsx`:

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import ChatInterface from '@/components/ChatInterface';
import { StudentData } from '@/lib/api/rag-client';

export default function StudentPage() {
  const router = useRouter();
  const [studentData, setStudentData] = Cookies.useState<StudentData | null>(null);

  useEffect(() => {
    const studentCookie = Cookies.get('student_data');
    if (!studentCookie) {
      router.push('/login');
      return;
    }

    try {
      const data = JSON.parse(studentCookie) as StudentData;
      if (!data.isAuthenticated) {
        router.push('/login');
        return;
      }
      setStudentData(data);
    } catch {
      router.push('/login');
    }
  }, [router]);

  if (!studentData) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div>
      {/* Student Info Bar */}
      <div className="bg-blue-600 text-white p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">
              {studentData.first_name} {studentData.last_name}
            </h2>
            <p className="text-sm opacity-90">
              {studentData.program} • Year {studentData.current_year} • Semester {studentData.current_semester}
            </p>
          </div>
          <button
            onClick={() => {
              Cookies.remove('student_data');
              router.push('/login');
            }}
            className="px-4 py-2 bg-white text-blue-600 rounded hover:bg-blue-50"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Chat Interface */}
      <ChatInterface />
    </div>
  );
}
```

---

## 7. Create Admin Page

Create `app/admin/page.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AdminIngestPanel from '@/components/AdminIngestPanel';

export default function AdminPage() {
  const router = useRouter();
  const adminToken = process.env.NEXT_PUBLIC_ADMIN_TOKEN;

  useEffect(() => {
    // Add your admin authentication here
    // For now, we'll use environment variable
    if (!adminToken) {
      router.push('/');
    }
  }, [adminToken, router]);

  if (!adminToken) {
    return <div className="flex items-center justify-center h-screen">Unauthorized</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">Manage syllabi for all departments and years</p>
        </div>

        <AdminIngestPanel adminToken={adminToken} />

        {/* Instructions */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Instructions</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>Upload PDF to Cloudinary and get the URL</li>
            <li>Enter department name (e.g., "Computer Science")</li>
            <li>Enter academic year (e.g., "2024")</li>
            <li>Click "Upload Syllabus"</li>
            <li>System will chunk, embed, and store in vector DB</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
```

---

## 8. Install Dependencies

```bash
npm install axios js-cookie zustand
npm install -D @types/js-cookie
```

---

## 9. How It Works

### Student Flow:
```
1. Student logs in → student_data cookie set
2. Student navigates to /student
3. Cookie checked and parsed
4. Student asks question
5. Question sent with x-student-data header
6. API auto-filters by dept/year/semester
7. RAG returns personalized answer
```

### Admin Flow:
```
1. Admin goes to /admin
2. Enters: PDF URL, Dept, Year
3. Clicks "Upload"
4. Bearer token sent in Authorization header
5. API validates token
6. PDF chunked, embedded, stored
```

---

## 10. Testing

### Test Student Chat:
```bash
curl -X POST http://localhost:8000/chat \
  -H "x-student-data: {\"student_id\":25,\"token\":\"894m0QCWDu57ASOLRXGy\",\"isAuthenticated\":true,\"program\":\"Computer Science\",\"current_year\":\"2024\",\"current_semester\":\"1\"}" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the marking scheme?"}'
```

### Test Admin Ingest:
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer rag_studentpath_admin_2026" \
  -H "Content-Type: application/json" \
  -d '{"pdf_url":"https://example.com/syllabus.pdf","dept":"Computer Science","year":"2024"}'
```

---

## Deployment Checklist

- [ ] Update `NEXT_PUBLIC_RAG_API_URL` to Render URL
- [ ] Set `NEXT_PUBLIC_ADMIN_TOKEN` from Python `.env`
- [ ] Test student login and chat
- [ ] Test admin panel with real PDF
- [ ] Deploy to Vercel
- [ ] Update CORS on Render to include Vercel domain

---

## Security Notes

1. **Admin Token:** Change in both Python and Next.js `.env`
2. **Student Cookie:** Never expose in public code
3. **Student Data:** Validated by Python API
4. **CORS:** Only allow your Vercel domain on Render
5. **HTTPS Only:** Required for production

Done! Your RAG API is now integrated with student authentication. 🎉
