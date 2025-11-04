"""
Advanced Paper Generation Service
Generates structured question papers with MCQ, Short, Medium, and Long questions
Supports previous/creative/new question ratios
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from app.core.config import settings
from app.core.database import get_database


class AdvancedPaperGenerator:
    """Generate comprehensive question papers with multiple question types"""
    
    def __init__(self):
        self.llm = None
        self.db = None
    
    def _ensure_llm(self):
        """Initialize LLM"""
        if self.llm is None:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        return self.llm
    
    async def initialize(self):
        """Initialize database connection"""
        self.db = get_database()
    
    async def generate_paper(self, request_data: Dict) -> Dict:
        """
        Generate a complete question paper based on specifications
        
        Args:
            request_data: Dictionary containing:
                - subject, department, exam_type
                - mcq_count, mcq_marks, short_count, short_marks, etc.
                - previous_percent, creative_percent, new_percent
                - prompt (optional topic focus)
        
        Returns:
            Dictionary with paper_metadata, questions, and summary
        """
        self._ensure_llm()
        
        # Extract parameters
        subject = request_data.get("subject")
        department = request_data.get("department")
        exam_type = request_data.get("exam_type", "Final")
        teacher_id = request_data.get("teacher_id")
        
        # Question categories
        mcq_count = request_data.get("mcq_count", 0)
        mcq_marks = request_data.get("mcq_marks", 1)
        short_count = request_data.get("short_count", 0)
        short_marks = request_data.get("short_marks", 2)
        medium_count = request_data.get("medium_count", 0)
        medium_marks = request_data.get("medium_marks", 5)
        long_count = request_data.get("long_count", 0)
        long_marks = request_data.get("long_marks", 10)
        
        # Source ratios
        previous_percent = request_data.get("previous_percent", 30)
        creative_percent = request_data.get("creative_percent", 40)
        new_percent = request_data.get("new_percent", 30)
        
        # Optional prompt
        optional_prompt = request_data.get("prompt", "")
        
        # Calculate total marks
        total_marks = (
            mcq_count * mcq_marks +
            short_count * short_marks +
            medium_count * medium_marks +
            long_count * long_marks
        )
        
        print(f"\n{'='*60}")
        print(f"📝 ADVANCED PAPER GENERATION")
        print(f"{'='*60}")
        print(f"Subject: {subject}")
        print(f"Department: {department}")
        print(f"Exam Type: {exam_type}")
        print(f"Total Marks: {total_marks}")
        print(f"\n📊 Question Distribution:")
        print(f"  MCQ: {mcq_count} × {mcq_marks} marks = {mcq_count * mcq_marks} marks")
        print(f"  Short: {short_count} × {short_marks} marks = {short_count * short_marks} marks")
        print(f"  Medium: {medium_count} × {medium_marks} marks = {medium_count * medium_marks} marks")
        print(f"  Long: {long_count} × {long_marks} marks = {long_count * long_marks} marks")
        print(f"\n🎯 Source Distribution:")
        print(f"  Previous: {previous_percent}%")
        print(f"  Creative: {creative_percent}%")
        print(f"  New: {new_percent}%")
        print(f"{'='*60}\n")
        
        # Gather context from resources
        context = await self._gather_context(teacher_id, subject, department)
        
        # Gather previous year questions
        previous_questions = await self._gather_previous_questions(subject, department)
        
        # Generate questions using LLM
        questions = await self._generate_questions_with_llm(
            subject=subject,
            department=department,
            exam_type=exam_type,
            mcq_count=mcq_count,
            mcq_marks=mcq_marks,
            short_count=short_count,
            short_marks=short_marks,
            medium_count=medium_count,
            medium_marks=medium_marks,
            long_count=long_count,
            long_marks=long_marks,
            previous_percent=previous_percent,
            creative_percent=creative_percent,
            new_percent=new_percent,
            optional_prompt=optional_prompt,
            context=context,
            previous_questions=previous_questions
        )
        
        # Build response
        paper_data = {
            "paper_metadata": {
                "subject": subject,
                "department": department,
                "exam_type": exam_type,
                "total_marks": total_marks,
                "generated_on": datetime.utcnow().strftime("%Y-%m-%d"),
                "section": request_data.get("section"),
                "year": request_data.get("year")
            },
            "questions": questions,
            "summary": {
                "total_questions": len(questions),
                "total_marks": total_marks,
                "question_distribution": {
                    "MCQ": mcq_count,
                    "Short": short_count,
                    "Medium": medium_count,
                    "Long": long_count
                },
                "source_distribution": self._calculate_source_distribution(questions)
            }
        }
        
        return paper_data
    
    async def _gather_context(self, teacher_id: str, subject: str, department: str) -> str:
        """Gather context from uploaded resources"""
        resources = await self.db.resources.find({
            "teacher_id": teacher_id,
            "processed": True,
            "$or": [
                {"subject": {"$regex": subject, "$options": "i"}},
                {"department": {"$regex": department, "$options": "i"}}
            ]
        }).to_list(length=100)
        
        print(f"📚 Found {len(resources)} resources for context")
        
        # Build context from resources
        context_parts = []
        for r in resources[:10]:  # Limit to top 10 resources
            text = r.get("extracted_text", "")
            if text:
                context_parts.append(text[:5000])  # Limit each resource to 5000 chars
        
        context = "\n\n".join(context_parts)
        print(f"✅ Built context: {len(context)} characters")
        
        return context
    
    async def _gather_previous_questions(self, subject: str, department: str) -> List[Dict]:
        """Gather previous year questions from approved papers"""
        papers = await self.db.papers.find({
            "subject": {"$regex": subject, "$options": "i"},
            "department": {"$regex": department, "$options": "i"},
            "status": "approved"
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        print(f"📄 Found {len(papers)} previous papers")
        
        previous_questions = []
        for paper in papers:
            questions = paper.get("questions", [])
            for q in questions:
                previous_questions.append({
                    "question_text": q.get("question_text"),
                    "question_type": q.get("question_type"),
                    "marks": q.get("marks"),
                    "blooms_level": q.get("blooms_level")
                })
        
        print(f"✅ Extracted {len(previous_questions)} previous questions")
        
        return previous_questions
    
    async def _generate_questions_with_llm(
        self,
        subject: str,
        department: str,
        exam_type: str,
        mcq_count: int,
        mcq_marks: int,
        short_count: int,
        short_marks: int,
        medium_count: int,
        medium_marks: int,
        long_count: int,
        long_marks: int,
        previous_percent: int,
        creative_percent: int,
        new_percent: int,
        optional_prompt: str,
        context: str,
        previous_questions: List[Dict]
    ) -> List[Dict]:
        """Generate questions using LLM"""
        
        # Build prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("human", """You are an expert academic question paper generator.

## Objective:
Generate a complete, well-balanced question paper in structured JSON format based on the provided metadata.

### 📘 Context Information:
Subject: {subject}
Department: {department}
Exam Type: {exam_type}

### Available Resources:
{context}

### Previous Year Questions (for reference):
{previous_questions}

### 🧾 Question Requirements:
- Multiple Choice Questions (MCQ): {mcq_count} questions, {mcq_marks} marks each
- Short Answer Questions: {short_count} questions, {short_marks} marks each
- Medium Answer Questions: {medium_count} questions, {medium_marks} marks each
- Long/Essay Questions: {long_count} questions, {long_marks} marks each

### Question Source Ratios:
- Previous Year: {previous_percent}% (use or modify previous questions)
- Creative (Modified Existing): {creative_percent}% (modify previous questions creatively)
- New (AI-Generated): {new_percent}% (create completely new questions)

### Optional Topic Focus:
{optional_prompt}

### 🧮 Output Requirements:
Return ONLY a valid JSON array of questions in this exact format:

[
  {{
    "type": "MCQ",
    "question_text": "What is the time complexity of binary search?",
    "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
    "correct_answer": "B",
    "answer_key": "O(log n) - Binary search divides the search space in half each time",
    "explanation": "Binary search works by repeatedly dividing the search interval in half, resulting in logarithmic time complexity.",
    "marks": {mcq_marks},
    "difficulty": "Remember",
    "source": "previous",
    "blooms_level": "Remember"
  }},
  {{
    "type": "Short",
    "question_text": "Explain the difference between stack and queue.",
    "answer_key": "Stack follows LIFO (Last In First Out) principle where the last element added is the first to be removed. Queue follows FIFO (First In First Out) principle where the first element added is the first to be removed.",
    "explanation": "Stack: Used in function calls, undo operations. Queue: Used in scheduling, BFS algorithm.",
    "marks": {short_marks},
    "difficulty": "Understand",
    "source": "creative",
    "blooms_level": "Understand"
  }},
  {{
    "type": "Medium",
    "question_text": "Implement a function to reverse a linked list. Explain your approach.",
    "answer_key": "Use three pointers: prev, current, next. Iterate through the list, reversing links. Time: O(n), Space: O(1).",
    "explanation": "The iterative approach is more efficient than recursive as it uses constant space.",
    "marks": {medium_marks},
    "difficulty": "Apply",
    "source": "new",
    "blooms_level": "Apply"
  }},
  {{
    "type": "Long",
    "question_text": "Compare and contrast different sorting algorithms. Discuss time complexity, space complexity, and use cases for each.",
    "answer_key": "Bubble Sort: O(n²), simple but slow. Merge Sort: O(n log n), stable, uses extra space. Quick Sort: O(n log n) average, in-place. Heap Sort: O(n log n), in-place. Use cases depend on data size, memory constraints, and stability requirements.",
    "explanation": "Each algorithm has trade-offs between time, space, and stability. Choose based on specific requirements.",
    "marks": {long_marks},
    "difficulty": "Analyze",
    "source": "new",
    "blooms_level": "Analyze"
  }}
]

### 🧠 Additional Rules:
1. Ensure the total marks match exactly the required paper marks.
2. Verify question diversity — do not repeat or rephrase the same question twice.
3. Maintain academic tone and correctness.
4. For MCQ, provide exactly 4 options (A, B, C, D).
5. For previous year questions, use similar questions from the provided list.
6. For creative questions, modify previous questions significantly.
7. For new questions, create completely original questions.
8. Distribute Bloom's taxonomy levels appropriately:
   - MCQ: Remember, Understand
   - Short: Understand, Apply
   - Medium: Apply, Analyze
   - Long: Analyze, Evaluate, Create
9. Include detailed explanations for all answers.
10. If optional prompt is given, prioritize those topics while ensuring coverage.

Generate the questions now. Return ONLY the JSON array, no other text.""")
        ])
        
        # Format previous questions for prompt
        prev_q_text = "\n".join([
            f"- {q['question_type']}: {q['question_text']} ({q['marks']} marks)"
            for q in previous_questions[:20]  # Limit to 20 examples
        ]) if previous_questions else "No previous questions available"
        
        # Generate
        print("🤖 Generating questions with LLM...")
        
        chain = prompt_template | self.llm
        response = await chain.ainvoke({
            "subject": subject,
            "department": department,
            "exam_type": exam_type,
            "context": context[:10000] if context else "Use general knowledge for this subject",
            "previous_questions": prev_q_text,
            "mcq_count": mcq_count,
            "mcq_marks": mcq_marks,
            "short_count": short_count,
            "short_marks": short_marks,
            "medium_count": medium_count,
            "medium_marks": medium_marks,
            "long_count": long_count,
            "long_marks": long_marks,
            "previous_percent": previous_percent,
            "creative_percent": creative_percent,
            "new_percent": new_percent,
            "optional_prompt": optional_prompt if optional_prompt else "Cover all major topics from the syllabus"
        })
        
        # Parse response
        try:
            response_text = response.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            questions = json.loads(response_text)
            
            print(f"✅ Generated {len(questions)} questions")
            
            return questions
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response: {response_text[:500]}")
            
            # Return fallback questions
            return self._create_fallback_questions(
                mcq_count, mcq_marks,
                short_count, short_marks,
                medium_count, medium_marks,
                long_count, long_marks,
                subject
            )
    
    def _create_fallback_questions(
        self,
        mcq_count: int, mcq_marks: int,
        short_count: int, short_marks: int,
        medium_count: int, medium_marks: int,
        long_count: int, long_marks: int,
        subject: str
    ) -> List[Dict]:
        """Create fallback questions if LLM fails"""
        questions = []
        
        # MCQ questions
        for i in range(mcq_count):
            questions.append({
                "type": "MCQ",
                "question_text": f"Sample MCQ question {i+1} for {subject}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "A",
                "answer_key": "Option A is correct",
                "explanation": "This is a sample explanation",
                "marks": mcq_marks,
                "difficulty": "Remember",
                "source": "new",
                "blooms_level": "Remember"
            })
        
        # Short questions
        for i in range(short_count):
            questions.append({
                "type": "Short",
                "question_text": f"Sample short question {i+1} for {subject}",
                "answer_key": "Sample answer for short question",
                "explanation": "This is a sample explanation",
                "marks": short_marks,
                "difficulty": "Understand",
                "source": "new",
                "blooms_level": "Understand"
            })
        
        # Medium questions
        for i in range(medium_count):
            questions.append({
                "type": "Medium",
                "question_text": f"Sample medium question {i+1} for {subject}",
                "answer_key": "Sample answer for medium question",
                "explanation": "This is a sample explanation",
                "marks": medium_marks,
                "difficulty": "Apply",
                "source": "new",
                "blooms_level": "Apply"
            })
        
        # Long questions
        for i in range(long_count):
            questions.append({
                "type": "Long",
                "question_text": f"Sample long question {i+1} for {subject}",
                "answer_key": "Sample answer for long question",
                "explanation": "This is a sample explanation",
                "marks": long_marks,
                "difficulty": "Analyze",
                "source": "new",
                "blooms_level": "Analyze"
            })
        
        return questions
    
    def _calculate_source_distribution(self, questions: List[Dict]) -> Dict[str, int]:
        """Calculate actual source distribution from generated questions"""
        distribution = {"Previous": 0, "Creative": 0, "New": 0}
        
        for q in questions:
            source = q.get("source", "new")
            if source == "previous":
                distribution["Previous"] += 1
            elif source == "creative":
                distribution["Creative"] += 1
            else:
                distribution["New"] += 1
        
        return distribution

    async def generate_paper_suggestions(self, paper: Dict) -> str:
        """
        Generate suggestions for future papers based on analyzing the current paper
        
        Args:
            paper: Dictionary containing the paper data from MongoDB
            
        Returns:
            String containing AI-generated suggestions
        """
        self._ensure_llm()
        
        # Extract paper details
        subject = paper.get("subject", "")
        questions = paper.get("questions", [])
        department = paper.get("department", "")
        total_marks = paper.get("total_marks", 0)
        
        # Analyze question distribution
        question_types = {}
        blooms_levels = {}
        marks_distribution = []
        
        for q in questions:
            q_type = q.get("question_type", "Unknown")
            blooms = q.get("blooms_level", "Unknown")
            marks = q.get("marks", 0)
            
            question_types[q_type] = question_types.get(q_type, 0) + 1
            blooms_levels[blooms] = blooms_levels.get(blooms, 0) + 1
            marks_distribution.append(marks)
        
        # Create suggestions prompt
        prompt = HumanMessage(content=f"""
        As an expert exam paper analyzer, analyze this paper and provide suggestions for future improvements:

        Subject: {subject}
        Department: {department}
        Total Marks: {total_marks}

        Current Distribution:
        Question Types: {json.dumps(question_types)}
        Bloom's Taxonomy Levels: {json.dumps(blooms_levels)}
        Marks Distribution: {marks_distribution}

        Please provide detailed suggestions covering:
        1. Question Type Balance - Are the question types well distributed?
        2. Cognitive Level Distribution - Is there good coverage across Bloom's levels?
        3. Marks Allocation - Is the marking scheme appropriate?
        4. Topic Coverage - Are key topics adequately covered?
        5. Innovation Opportunities - How can future papers be more engaging?
        6. Time Management Considerations - Is the paper well-timed?

        Format your response in clear sections with bullet points and specific examples where possible.
        Focus on actionable suggestions that would improve the quality of future papers.
        """)
        
        try:
            # Get suggestions from LLM
            result = await self.llm.ainvoke([prompt])
            suggestions = result.content
            
            print(f"\n✨ Generated suggestions for paper")
            return suggestions
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return "Failed to generate suggestions. Please try again later."


# Global instance
advanced_paper_generator = AdvancedPaperGenerator()
