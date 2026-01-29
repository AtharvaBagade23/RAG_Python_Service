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
        Answer student question using RAG with strict quality controls.
        
        Retrieves relevant chunks from syllabus using vector similarity search,
        then generates answer using GPT with strict prompt engineering.
        
        Now with improved filtering using automatic metadata extraction:
        - Semester filtering (when available)
        - Course code/name tracking
        - Unit-level relevance scoring
        
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
        
        # 2. Build filter - Use dept and year (always present)
        # Also include semester if provided and available in metadata
        filter_dict = {
            "dept": dept,
            "year": year
        }
        
        # Only add semester to filter if provided (metadata now has it automatically extracted)
        if semester:
            filter_dict["semester"] = semester
        
        print(f"[CHAT_SERVICE] Querying with filter: {filter_dict}")
        print(f"[CHAT_SERVICE] Question: {question}")
        
        # 3. Query Pinecone with strong retrieval (8 relevant chunks)
        matches = self.pinecone_service.query(
            vector=query_embedding,
            filter_dict=filter_dict,
            top_k=8  # 5-8 strong chunks work best in RAG
        )
        
        print(f"[CHAT_SERVICE] Found {len(matches)} matching chunks before filtering")
        
        # ✅ Apply similarity threshold (remove weak/irrelevant matches)
        MIN_SCORE_THRESHOLD = 0.35
        filtered_matches = [m for m in matches if m["score"] >= MIN_SCORE_THRESHOLD]
        
        print(f"[CHAT_SERVICE] After threshold filter ({MIN_SCORE_THRESHOLD}): {len(filtered_matches)} chunks")
        
        if not filtered_matches:
            print(f"[CHAT_SERVICE] No matches above threshold for dept={dept}, year={year}")
            return {
                "answer": "This topic is not covered in your syllabus for the selected department and year.",
                "sources": [],
                "confidence": "low"
            }
        
        # 4. Build context from filtered matches
        context_parts = []
        sources = []
        
        for i, match in enumerate(filtered_matches):
            text = match["metadata"].get("text", "")
            score = match["score"]
            context_parts.append(text)
            
            # ✅ Enhanced source info with new metadata fields
            source_info = {
                "score": round(score, 3),
                "dept": match["metadata"].get("dept", ""),
                "year": match["metadata"].get("year", ""),
                "section": match["metadata"].get("section", ""),
                "chunk_index": i + 1
            }
            
            # Add optional enhanced metadata (auto-extracted)
            if match["metadata"].get("semester"):
                source_info["semester"] = match["metadata"]["semester"]
            if match["metadata"].get("course_code"):
                source_info["course_code"] = match["metadata"]["course_code"]
            if match["metadata"].get("course_name"):
                source_info["course_name"] = match["metadata"]["course_name"]
            if match["metadata"].get("unit"):
                source_info["unit"] = match["metadata"]["unit"]
            
            sources.append(source_info)
            
            # Log detailed source info
            course_info = f"{match['metadata'].get('course_code', '')} - {match['metadata'].get('course_name', '')}"
            unit_info = match["metadata"].get("unit", "")
            sem_info = match["metadata"].get("semester", "")
            print(f"[CHAT_SERVICE] Match {i+1}: score={score:.3f}, course={course_info}, unit={unit_info}, sem={sem_info}")
        
        context = "\n\n".join(context_parts)
        
        # ✅ Strict system prompt (prevents hallucinations)
        system_prompt = f"""You are a STRICT academic syllabus assistant.

You must follow these rules EXACTLY:

1. Answer ONLY using the syllabus context provided.
2. Do NOT use outside knowledge, assumptions, or general explanations.
3. If the syllabus does NOT explicitly mention the topic, reply EXACTLY with:
   "This topic is not covered in your syllabus for the selected department and year."
4. Do NOT explain concepts unless they appear in the syllabus text.
5. Prefer DIRECT syllabus wording over paraphrasing.
6. If multiple syllabus sections mention the topic, combine them concisely.
7. If relevance is weak or unclear, do NOT attempt an answer.

Context constraints:
- Department: {dept}
- Academic Year: {year}
- Semester: {semester or "Not specified"}

Output rules:
- Be concise
- Use bullet points only if syllabus lists items
- No introductions, no opinions"""

        # ✅ Improved user prompt (allows model to ignore noise)
        user_prompt = f"""Below are syllabus excerpts retrieved by semantic similarity.
Some excerpts may be weakly related or irrelevant.

Use ONLY excerpts that clearly answer the question.
If none clearly answer it, say the topic is not covered.

Syllabus excerpts:
{context}

Student question:
{question}"""

        # 5. Call GPT with strict prompts
        print(f"[CHAT_SERVICE] Calling GPT-4 with {len(context_parts)} filtered chunks of context")
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
        
        # 6. Calculate confidence based on TOP score (industry standard)
        top_score = max(m["score"] for m in filtered_matches)
        
        if top_score >= 0.6:
            confidence = "high"
        elif top_score >= 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        print(f"[CHAT_SERVICE] Top match score: {top_score:.3f}, Confidence: {confidence}")
        
        # 7. Limit sources to top 3 (clean UX)
        sources = sorted(sources, key=lambda x: x["score"], reverse=True)[:3]
        print(f"[CHAT_SERVICE] Returning {len(sources)} sources (max 3)")
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }
