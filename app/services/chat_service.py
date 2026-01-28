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
        
        Retrieves relevant chunks from syllabus using vector similarity search,
        then generates answer using GPT with retrieved context.
        
        Args:
            question: Student's question about the syllabus
            dept: Department (e.g., "Computer")
            year: Academic year (e.g., "2024")
            semester: Optional semester filter
        
        Returns:
            Dict with answer, sources, and confidence
        """
        # 1. Embed the question
        query_embedding = self.embedding_service.create_embedding(question)
        
        # 2. Build filter - ONLY use dept and year (these are always present in metadata)
        # Don't filter by semester as it may not be in all stored vectors
        filter_dict = {
            "dept": dept,
            "year": year
        }
        
        # Note: semester is optional and may not be in all stored metadata
        # Only add if we want strict semester filtering
        # if semester:
        #     filter_dict["semester"] = semester
        
        print(f"[CHAT_SERVICE] Querying with filter: {filter_dict}")
        print(f"[CHAT_SERVICE] Question: {question}")
        
        # 3. Query Pinecone with increased top_k for better context
        # Changed from top_k=3 to top_k=50 for comprehensive results
        # This retrieves most chunks to provide rich context for better answers
        matches = self.pinecone_service.query(
            vector=query_embedding,
            filter_dict=filter_dict,
            top_k=50  # Increased to 50 to get most chunks from syllabus
        )
        
        print(f"[CHAT_SERVICE] Found {len(matches)} matching chunks")
        
        if not matches:
            print(f"[CHAT_SERVICE] No matches found for dept={dept}, year={year}")
            return {
                "answer": "I couldn't find relevant information in your syllabus. Please rephrase your question or contact your department.",
                "sources": [],
                "confidence": "low"
            }
        
        # 4. Build context from matches
        context_parts = []
        sources = []
        
        for i, match in enumerate(matches):
            text = match["metadata"].get("text", "")
            score = match["score"]
            context_parts.append(text)
            sources.append({
                "score": round(score, 3),
                "dept": match["metadata"].get("dept", ""),
                "year": match["metadata"].get("year", ""),
                "section": match["metadata"].get("section", ""),
                "chunk_index": i + 1
            })
            print(f"[CHAT_SERVICE] Match {i+1}: score={score:.3f}, section={match['metadata'].get('section', '')}")
        
        context = "\n\n".join(context_parts)
        
        # 5. Build prompt
        system_prompt = """You are an academic assistant helping students understand their syllabus.

STRICT RULES:
- Answer ONLY from the provided context
- If the answer is not in the context, say: "This information is not available in your syllabus"
- Be concise and direct
- Use bullet points for lists
- Quote exact text when mentioning policies or rules
- If multiple sources mention the same thing, synthesize them into a clear answer"""

        user_prompt = f"""Context from syllabus (from {len(matches)} relevant sections):
{context}

Student question:
{question}

Answer:"""

        # 6. Call GPT
        print(f"[CHAT_SERVICE] Calling GPT-4 with {len(context_parts)} chunks of context")
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
        print(f"[CHAT_SERVICE] Generated answer: {answer[:100]}...")
        
        # 7. Determine confidence based on match scores
        avg_score = sum(m["score"] for m in matches) / len(matches)
        confidence = "high" if avg_score > 0.8 else "medium" if avg_score > 0.6 else "low"
        
        print(f"[CHAT_SERVICE] Average match score: {avg_score:.3f}, Confidence: {confidence}")
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }
