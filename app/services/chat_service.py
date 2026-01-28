from openai import OpenAI
from typing import List, Dict
from app.config import Settings
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService

class ChatService:
    """RAG-based chat service"""
    
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        pinecone_service: PineconeService
    ):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service
        self.model = settings.chat_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
    
    def answer_question(
        self,
        question: str,
        dept: str,
        year: str,
        semester: str = None
    ) -> Dict:
        """
        Answer student question using RAG
        
        Returns:
            Dict with answer, sources, and confidence
        """
        # 1. Embed the question
        query_embedding = self.embedding_service.create_embedding(question)
        
        # 2. Build filter
        filter_dict = {
            "dept": dept,
            "year": year
        }
        if semester:
            filter_dict["semester"] = semester
        
        # 3. Query Pinecone
        matches = self.pinecone_service.query(
            vector=query_embedding,
            filter_dict=filter_dict,
            top_k=3
        )
        
        if not matches:
            return {
                "answer": "I couldn't find relevant information in your syllabus. Please rephrase your question or contact your department.",
                "sources": [],
                "confidence": "low"
            }
        
        # 4. Build context from matches
        context_parts = []
        sources = []
        
        for match in matches:
            context_parts.append(match["metadata"].get("text", ""))
            sources.append({
                "score": round(match["score"], 3),
                "dept": match["metadata"]["dept"],
                "year": match["metadata"]["year"]
            })
        
        context = "\n\n".join(context_parts)
        
        # 5. Build prompt
        system_prompt = """You are an academic assistant helping students understand their syllabus.

STRICT RULES:
- Answer ONLY from the provided context
- If the answer is not in the context, say: "This information is not available in your syllabus"
- Be concise and direct
- Use bullet points for lists
- Quote exact text when mentioning policies or rules"""

        user_prompt = f"""Context from syllabus:
{context}

Student question:
{question}

Answer:"""

        # 6. Call GPT
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        answer = response.choices[0].message.content
        
        # 7. Determine confidence
        avg_score = sum(m["score"] for m in matches) / len(matches)
        confidence = "high" if avg_score > 0.8 else "medium" if avg_score > 0.6 else "low"
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }
