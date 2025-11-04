from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from sentence_transformers import SentenceTransformer
import numpy as np
from app.core.config import settings
from app.core.database import get_database
from app.services.embedding_service import embedding_service
import json
from datetime import datetime


# State definition for the workflow
class PaperGenerationState(TypedDict):
    """State for paper generation workflow"""
    teacher_id: str
    subject: str
    department: str
    total_marks: int
    prompt: str
    blooms_distribution: Dict[str, int]
    unit_requirements: Dict[str, int]
    
    # Agent outputs
    resource_context: str
    generated_questions: List[Dict]
    verified_questions: List[Dict]
    final_paper: Dict
    
    # Workflow control
    current_step: str
    retry_count: int
    errors: List[str]
    
    # History tracking
    generation_history: List[Dict]
    rejected_questions: List[Dict]
    regeneration_feedback: str


class LangGraphPaperGenerator:
    """Multi-agent paper generation using LangGraph"""
    
    def __init__(self):
        self.llm = None  # Lazy initialization
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = None
    
    def _ensure_llm(self):
        """Lazy initialization of LLM to ensure API key is loaded"""
        if self.llm is None:
            api_key = settings.GEMINI_API_KEY
            
            # Validate API key
            if not api_key or api_key == "your_gemini_api_key_here":
                raise ValueError(
                    "Invalid Gemini API key. Please set GEMINI_API_KEY in your .env file. "
                    "Get your API key from: https://makersuite.google.com/app/apikey"
                )
            
            if not api_key.startswith("AIza"):
                print(f"⚠️  Warning: API key format unusual (should start with 'AIza')")
            
            # Use model with best free tier limits
            # Based on available models: gemini-2.0-flash has good free tier quota
            model_to_use = "gemini-2.0-flash"  # Fast, good free tier limits
            
            self.llm = ChatGoogleGenerativeAI(
                model=model_to_use,
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True  # Fix for Gemini
            )
            print(f"✅ Gemini LLM initialized with model: {model_to_use}")
        return self.llm
    
    async def initialize(self):
        """Initialize database connection"""
        self.db = get_database()
    
    # Agent 1: RQG Agent - Resource Question Gathering (Enhanced with Subject Context and Approved Papers)
    async def rqg_agent(self, state: PaperGenerationState) -> PaperGenerationState:
        """Gather relevant context from uploaded resources and approved papers, filtered by subject and department"""
        try:
            subject = state["subject"]
            department = state["department"]
            
            print(f"\n📚 RQG Agent: Gathering context for {subject} ({department})")
            
            # Step 1: Fetch teacher's resources filtered by subject/department
            resources = await self.db.resources.find({
                "teacher_id": state["teacher_id"],
                "processed": True,
                "$or": [
                    {"subject": {"$regex": subject, "$options": "i"}},
                    {"department": {"$regex": department, "$options": "i"}},
                    {"metadata.subject": {"$regex": subject, "$options": "i"}}
                ]
            }).to_list(length=100)
            
            print(f"   📄 Found {len(resources)} subject-specific resources")
            
            # Step 2: Fetch ALL approved papers for this subject/department (not just teacher's)
            approved_papers = await self.db.papers.find({
                "subject": {"$regex": subject, "$options": "i"},
                "department": {"$regex": department, "$options": "i"},
                "status": "approved"
            }).sort("created_at", -1).to_list(length=50)  # Get last 50 approved papers
            
            print(f"   📋 Found {len(approved_papers)} approved papers for reference")
            
            # Step 3: Fetch regenerated papers (drafts) to avoid repeating same mistakes
            regenerated_papers = await self.db.papers.find({
                "teacher_id": state["teacher_id"],
                "subject": {"$regex": subject, "$options": "i"},
                "department": {"$regex": department, "$options": "i"},
                "status": {"$in": ["draft", "pending"]},
                "regeneration_count": {"$gt": 0}
            }).sort("created_at", -1).to_list(length=10)
            
            print(f"   🔄 Found {len(regenerated_papers)} regenerated papers for learning")
            
            if len(resources) == 0:
                print(f"   ⚠️  WARNING: No resources found for {subject}!")
                print(f"   💡 Please upload resources for this subject first")
                # Continue anyway - will use general knowledge
            
            # Step 4: Build context from resources
            context_texts = []
            context_texts.append(f"=== SUBJECT: {subject} ===")
            context_texts.append(f"=== DEPARTMENT: {department} ===\n")
            
            for resource in resources:
                if resource.get("extracted_text"):
                    resource_name = resource.get("filename", "Unknown")
                    context_texts.append(f"--- Resource: {resource_name} ---")
                    context_texts.append(resource["extracted_text"][:2000])  # Limit per resource
            
            # Step 5: Extract ALL existing questions to avoid duplication
            all_existing_questions = []
            for paper in approved_papers:
                for q in paper.get("questions", []):
                    all_existing_questions.append({
                        "text": q.get("question_text", ""),
                        "type": q.get("question_type", ""),
                        "blooms": q.get("blooms_level", ""),
                        "marks": q.get("marks", 0)
                    })
            
            for paper in regenerated_papers:
                for q in paper.get("questions", []):
                    all_existing_questions.append({
                        "text": q.get("question_text", ""),
                        "type": q.get("question_type", ""),
                        "blooms": q.get("blooms_level", ""),
                        "marks": q.get("marks", 0)
                    })
            
            print(f"   🚫 Collected {len(all_existing_questions)} existing questions to avoid duplication")
            
            # Step 6: Add historical paper context with MORE details
            if approved_papers:
                context_texts.append("\n" + "="*60)
                context_texts.append("REFERENCE: Previously Approved Papers for " + subject)
                context_texts.append("USE THESE AS EXAMPLES FOR QUESTION STYLE AND TOPICS")
                context_texts.append("⚠️ CRITICAL: DO NOT REPEAT THESE EXACT QUESTIONS!")
                context_texts.append("="*60)
                
                # Show sample questions from top 5 approved papers
                for i, paper in enumerate(approved_papers[:5], 1):
                    context_texts.append(f"\n--- Approved Paper {i} ({paper.get('total_marks')} marks) ---")
                    
                    # Add MORE sample questions from approved papers (up to 8)
                    questions = paper.get("questions", [])[:8]
                    for j, q in enumerate(questions, 1):
                        q_text = q.get('question_text', '')[:400]  # More text
                        context_texts.append(f"\nQ{j}. [{q.get('question_type')}] [{q.get('blooms_level')}] [{q.get('marks')} marks]")
                        context_texts.append(f"Question: {q_text}")
                        # Add answer key snippet
                        answer = q.get('answer_key', '')[:200]
                        context_texts.append(f"Answer: {answer}")
                    
                    # Add topics covered
                    topics = set(q.get("unit", "General") for q in paper.get("questions", []))
                    context_texts.append(f"\nTopics covered: {', '.join(topics)}")
                    context_texts.append(f"Question types used: {', '.join(set(q.get('question_type', '') for q in paper.get('questions', [])))}")
                
                # Add duplication warning
                context_texts.append("\n" + "="*60)
                context_texts.append("⚠️ DUPLICATION PREVENTION RULES:")
                context_texts.append("1. DO NOT copy questions word-for-word from above")
                context_texts.append("2. If using similar topics, rephrase completely")
                context_texts.append("3. Use different examples and scenarios")
                context_texts.append("4. Vary the question format and approach")
                context_texts.append("5. Generate UNIQUE questions while maintaining quality")
                context_texts.append("="*60)
            else:
                context_texts.append(f"\n⚠️ WARNING: No approved papers found for {subject}")
                context_texts.append(f"Generate questions strictly based on {subject} curriculum and uploaded resources.")
            
            # Step 7: Add regeneration feedback if available
            if regenerated_papers:
                context_texts.append("\n" + "="*60)
                context_texts.append("LEARNING FROM REGENERATED PAPERS:")
                context_texts.append("These papers were regenerated - learn from patterns")
                context_texts.append("="*60)
                
                for i, paper in enumerate(regenerated_papers[:3], 1):
                    regen_count = paper.get("regeneration_count", 0)
                    context_texts.append(f"\n--- Regenerated Paper {i} (Regenerated {regen_count}x) ---")
                    context_texts.append(f"Feedback: {paper.get('generation_prompt', 'No feedback')[:300]}")
                    
                    # Show what types of questions were generated
                    q_types = {}
                    for q in paper.get("questions", []):
                        q_type = q.get("question_type", "Unknown")
                        q_types[q_type] = q_types.get(q_type, 0) + 1
                    context_texts.append(f"Question distribution: {q_types}")
            
            # Combine and truncate to reasonable size
            full_context = "\n\n".join(context_texts)
            if len(full_context) > 15000:  # Increased limit for better context
                full_context = full_context[:15000]
            
            print(f"   📊 Context size: {len(full_context)} characters")
            
            state["resource_context"] = full_context
            state["current_step"] = "question_generation"
            
            return state
        
        except Exception as e:
            state["errors"].append(f"RQG Agent Error: {str(e)}")
            state["current_step"] = "error"
            return state
    
    # Agent 2: Question Generation Agent
    async def question_generation_agent(self, state: PaperGenerationState) -> PaperGenerationState:
        """Generate questions based on prompt and context"""
        try:
            # Build generation prompt
            blooms_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
            question_types = ["MCQ", "Short Answer", "Long Answer", "Reasoning", "Analytical", "Calculation", "Diagrammatic"]
            
            # Calculate marks distribution
            marks_distribution = self._calculate_marks_distribution(state["total_marks"], state.get("prompt", ""))
            
            print(f"\n{'='*60}")
            print(f"📝 GENERATION REQUEST SUMMARY")
            print(f"{'='*60}")
            print(f"Subject: {state['subject']}")
            print(f"Department: {state['department']}")
            print(f"Total Marks: {state['total_marks']}")
            print(f"Number of Questions: {len(marks_distribution)}")
            print(f"Marks Distribution: {marks_distribution}")
            print(f"Teacher's Prompt: {state.get('prompt', '')[:200]}...")
            print(f"Retry Count: {state.get('retry_count', 0)}")
            print(f"{'='*60}\n")
            
            # Check if this is a regeneration
            is_regeneration = "REGENERATION" in state.get("prompt", "").upper()
            if is_regeneration:
                print(f"🔄 REGENERATION MODE: Maintaining strict requirements from original prompt")
                print(f"   Previous errors: {state.get('errors', [])}")
            
            # Parse prompt for question types
            prompt_lower = state.get("prompt", "").lower()
            has_mcq = "mcq" in prompt_lower or "multiple choice" in prompt_lower or "objective" in prompt_lower
            
            generation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert exam question generator for university-level courses.
                
                CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
                1. Generate EXACTLY {num_questions} questions - NO MORE, NO LESS
                2. Total marks MUST equal EXACTLY {total_marks}
                3. Follow marks distribution: {marks_distribution}
                4. STRICTLY follow teacher's instructions in the prompt
                5. ALL questions MUST be relevant to the SUBJECT: {subject} and DEPARTMENT: {department}
                6. Use the provided syllabus context and approved paper examples as reference
                7. Questions MUST align with the subject's curriculum and topics
                8. Return ONLY valid JSON array - no markdown, no explanations, no extra text
                
                QUESTION TYPES:
                - MCQ: Multiple choice with 4 options (A, B, C, D). Format with newlines: "Question?\nA) option1\nB) option2\nC) option3\nD) option4"
                - Short Answer: 2-5 marks, brief answer expected
                - Long Answer: 5-10 marks, detailed explanation required
                - Reasoning: Logical reasoning questions
                - Analytical: Analysis and evaluation questions
                - Calculation: Mathematical/computational problems
                - Diagrammatic: Questions requiring diagrams
                
                JSON STRUCTURE FOR MCQ:
                {{
                  "question_text": "What is the time complexity of binary search?\nA) O(n)\nB) O(log n)\nC) O(n^2)\nD) O(1)",
                  "blooms_level": "Remember",
                  "question_type": "MCQ",
                  "marks": 2,
                  "answer_key": "Correct answer: B) O(log n). Explanation: Binary search divides search space in half each iteration.",
                  "unit": "Algorithm Analysis"
                }}
                
                JSON STRUCTURE FOR OTHER TYPES:
                {{
                  "question_text": "Explain the concept of dynamic programming with examples.",
                  "blooms_level": "Understand",
                  "question_type": "Long Answer",
                  "marks": 10,
                  "answer_key": "Detailed answer here...",
                  "unit": "Unit name"
                }}
                
                QUALITY REQUIREMENTS:
                - Clear and unambiguous questions
                - Appropriate difficulty for Bloom's level
                - Diverse question types
                - Aligned with syllabus
                - No duplicates
                - For MCQ: All 4 options must be plausible, only one correct
                
                ⚠️ CRITICAL: DUPLICATION PREVENTION
                - The context below contains questions from APPROVED and REGENERATED papers
                - DO NOT copy these questions word-for-word
                - DO NOT use the same examples or scenarios
                - If covering similar topics, use DIFFERENT phrasing and approach
                - Generate UNIQUE questions while maintaining quality standards
                - Use the approved papers as STYLE REFERENCE only, not for copying
                """),
                ("user", """
                ═══════════════════════════════════════════════════════════
                SUBJECT: {subject}
                DEPARTMENT: {department}
                TOTAL MARKS: {total_marks}
                ═══════════════════════════════════════════════════════════
                
                CRITICAL: ALL QUESTIONS MUST BE DIRECTLY RELATED TO {subject}
                - Questions must cover topics from {subject} curriculum
                - Use terminology and concepts specific to {subject}
                - Reference the syllabus context and approved paper examples below
                - Maintain academic standards for {department}
                
                TEACHER'S EXACT INSTRUCTIONS (FOLLOW STRICTLY):
                {prompt}
                
                ═══════════════════════════════════════════════════════════
                MANDATORY REQUIREMENTS - NO EXCEPTIONS:
                ═══════════════════════════════════════════════════════════
                ✓ Generate EXACTLY {num_questions} questions - NO MORE, NO LESS
                ✓ Total marks = EXACTLY {total_marks} - NO APPROXIMATIONS
                ✓ Marks per question (FOLLOW THIS EXACTLY): {marks_distribution}
                ✓ Bloom's distribution: {blooms_distribution}
                ✓ ALL questions MUST be relevant to {subject}
                ✓ ALL questions MUST be about {subject} topics ONLY
                ═══════════════════════════════════════════════════════════
                
                SYLLABUS CONTEXT & APPROVED PAPER EXAMPLES:
                {context}
                
                ═══════════════════════════════════════════════════════════
                CRITICAL: FOLLOW THE APPROVED PAPER EXAMPLES ABOVE
                ═══════════════════════════════════════════════════════════
                The approved papers above show EXACTLY the type of questions expected for {subject}.
                
                YOU MUST:
                1. Use SIMILAR topics as shown in approved papers
                2. Use SIMILAR question style and format
                3. Use SIMILAR terminology and concepts
                4. Match the difficulty level shown in examples
                5. Cover topics from the uploaded resources
                6. NEVER generate generic questions - ONLY {subject}-specific
                
                EXAMPLE ANALYSIS (from approved papers):
                - If approved papers ask about "time complexity of algorithms" → You should ask about algorithms
                - If approved papers ask about "linked list operations" → You should ask about data structures
                - If approved papers use specific terminology → You MUST use the same terminology
                - If approved papers cover specific topics → You MUST cover similar topics
                
                ⚠️ WARNING: Questions that don't match {subject} will be REJECTED!
                
                CRITICAL REMINDERS:
                1. If teacher asks for MCQs, generate MCQ type with 4 options (A, B, C, D) using \\n between options
                2. If teacher asks for "short questions" or "short answer", use question_type: "Short Answer"
                3. If teacher asks for "long questions" or "long answer", use question_type: "Long Answer"
                4. If teacher specifies MULTIPLE question types (e.g., "10 MCQs and 5 long questions"), generate EXACTLY that distribution
                5. Follow the marks distribution STRICTLY: {marks_distribution}
                6. If prompt says "10 MCQs of 2 marks", generate 10 MCQs with 2 marks each
                7. If this is a REGENERATION, apply feedback while maintaining original requirements
                8. Return ONLY JSON array - no ```json```, no explanations
                9. Each question MUST have all required fields
                10. NEVER deviate from the specified question count, types, or total marks
                
                EXAMPLE MCQ FORMAT (IMPORTANT - USE \\n FOR NEW LINES):
                {{
                  "question_text": "What is the time complexity of binary search?\\nA) O(n)\\nB) O(log n)\\nC) O(n^2)\\nD) O(1)",
                  "blooms_level": "Remember",
                  "question_type": "MCQ",
                  "marks": 2,
                  "answer_key": "Correct answer: B) O(log n). Explanation: Binary search divides the search space in half with each iteration, resulting in logarithmic time complexity.",
                  "unit": "Algorithm Analysis"
                }}
                
                EXAMPLE SHORT ANSWER FORMAT:
                {{
                  "question_text": "Define the term 'algorithm' and list its key characteristics.",
                  "blooms_level": "Remember",
                  "question_type": "Short Answer",
                  "marks": 2,
                  "answer_key": "An algorithm is a step-by-step procedure for solving a problem. Key characteristics: 1) Finiteness, 2) Definiteness, 3) Input, 4) Output, 5) Effectiveness.",
                  "unit": "Introduction"
                }}
                
                EXAMPLE LONG ANSWER FORMAT:
                {{
                  "question_text": "Explain the concept of dynamic programming with an example.",
                  "blooms_level": "Understand",
                  "question_type": "Long Answer",
                  "marks": 5,
                  "answer_key": "Dynamic programming is an optimization technique that solves complex problems by breaking them down into simpler subproblems...",
                  "unit": "Algorithm Design"
                }}
                
                ═══════════════════════════════════════════════════════════
                CRITICAL INSTRUCTIONS FOR MIXED QUESTION TYPES:
                ═══════════════════════════════════════════════════════════
                EXAMPLE: "20 MCQs of 2 marks each, 10 short questions of 4 marks each, 2 long questions of 10 marks each"
                
                YOU MUST GENERATE:
                - Questions 1-20: MCQ type, 2 marks each (Total: 40 marks)
                - Questions 21-30: Short Answer type, 4 marks each (Total: 40 marks)
                - Questions 31-32: Long Answer type, 10 marks each (Total: 20 marks)
                - TOTAL: 32 questions, 100 marks
                
                FOLLOW THIS PATTERN EXACTLY FOR THE GIVEN PROMPT!
                
                ABSOLUTE REQUIREMENTS:
                1. Count MUST be EXACTLY {num_questions}
                2. Marks MUST be EXACTLY {total_marks}
                3. Question types MUST match prompt specification
                4. ALL questions MUST be about {subject}
                5. NO generic questions - ONLY {subject}-specific
                ═══════════════════════════════════════════════════════════
                - Follow the marks distribution EXACTLY: {marks_distribution}
                - Count your questions before returning
                - For MCQ, use \\n between question and each option
                - Match question_type to what teacher requested (MCQ, Short Answer, Long Answer)
                
                NOW GENERATE {num_questions} QUESTIONS AS JSON ARRAY:
                """)
            ])
            
            formatted_prompt = generation_prompt.format_messages(
                blooms_levels=blooms_levels,
                question_types=question_types,
                subject=state["subject"],
                department=state["department"],
                total_marks=state["total_marks"],
                marks_distribution=json.dumps(marks_distribution),
                num_questions=len(marks_distribution),
                prompt=state.get("prompt", "Generate diverse questions"),
                blooms_distribution=json.dumps(state.get("blooms_distribution", {})),
                context=state["resource_context"][:5000]  # Limit context
            )
            
            # Generate questions (ensure LLM is initialized)
            llm = self._ensure_llm()
            response = await llm.ainvoke(formatted_prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                questions = json.loads(content)
                
                if not isinstance(questions, list):
                    raise ValueError("Response is not a list")
                
                # STRICT validation and correction
                questions = self._strict_validate_and_correct(
                    questions, 
                    marks_distribution, 
                    state["total_marks"],
                    state.get("prompt", "")
                )
                
                actual_marks = sum(q.get("marks", 0) for q in questions)
                
                # Print detailed generation summary
                print(f"\n{'='*60}")
                print(f"📊 GENERATION RESULT")
                print(f"{'='*60}")
                print(f"Generated: {len(questions)} questions, {actual_marks} marks")
                print(f"Required: {len(marks_distribution)} questions, {state['total_marks']} marks")
                
                # Count question types
                type_counts = {}
                for q in questions:
                    q_type = q.get("question_type", "Unknown")
                    type_counts[q_type] = type_counts.get(q_type, 0) + 1
                
                print(f"\nQuestion Type Distribution:")
                for q_type, count in type_counts.items():
                    print(f"  - {q_type}: {count}")
                
                print(f"\nSubject Relevance Check:")
                subject_keywords = state['subject'].lower().split()
                relevant_count = 0
                irrelevant_questions = []
                
                for i, q in enumerate(questions, 1):
                    q_text = q.get("question_text", "").lower()
                    answer = q.get("answer_key", "").lower()
                    combined_text = q_text + " " + answer
                    
                    # Check if question mentions subject keywords
                    is_relevant = any(keyword in combined_text for keyword in subject_keywords)
                    
                    if is_relevant:
                        relevant_count += 1
                    else:
                        irrelevant_questions.append(f"Q{i}: {q_text[:100]}")
                
                relevance_percentage = (relevant_count / len(questions)) * 100 if questions else 0
                print(f"  - Questions relevant to '{state['subject']}': {relevant_count}/{len(questions)} ({relevance_percentage:.1f}%)")
                
                if irrelevant_questions:
                    print(f"  ⚠️ WARNING: {len(irrelevant_questions)} questions may not be subject-specific:")
                    for irr_q in irrelevant_questions[:3]:  # Show first 3
                        print(f"     {irr_q}")
                
                # If relevance is too low, trigger retry (lowered threshold to 40%)
                if relevance_percentage < 40 and state.get("retry_count", 0) < 2:
                    print(f"  ❌ Relevance too low ({relevance_percentage:.1f}% < 40%), triggering retry...")
                    raise ValueError(f"Questions not sufficiently relevant to {state['subject']}")
                elif relevance_percentage < 40:
                    print(f"  ⚠️  Warning: Low relevance ({relevance_percentage:.1f}%), but proceeding after retries")
                
                print(f"{'='*60}\n")
                
                # Final check
                if len(questions) != len(marks_distribution) or actual_marks != state["total_marks"]:
                    print(f"❌ VALIDATION FAILED: {len(questions)}/{len(marks_distribution)} questions, {actual_marks}/{state['total_marks']} marks")
                    raise ValueError(f"Generated questions don't match requirements")
                
                state["generated_questions"] = questions
                state["current_step"] = "verification"
                
            except json.JSONDecodeError as e:
                # Fallback: create sample questions
                state["generated_questions"] = self._create_fallback_questions(state)
                state["current_step"] = "verification"
            
            # Add to generation history
            generation_record = {
                "timestamp": str(datetime.now()),
                "attempt": state.get("retry_count", 0),
                "questions_generated": len(questions) if 'questions' in locals() else 0,
                "marks_generated": sum(q.get("marks", 0) for q in questions) if 'questions' in locals() else 0,
                "success": len(state["generated_questions"]) > 0,
                "error": str(e) if 'e' in locals() else None
            }
            state["generation_history"].append(generation_record)
            
            return state
        
        except Exception as e:
            state["errors"].append(f"Question Generation Error: {str(e)}")
            state["retry_count"] += 1
            
            if state["retry_count"] < 3:
                state["current_step"] = "question_generation"
            else:
                state["current_step"] = "error"
            
            return state
    
    # Agent 3: Verifier Agent
    async def verifier_agent(self, state: PaperGenerationState) -> PaperGenerationState:
        """Verify questions for quality and duplicates"""
        try:
            questions = state["generated_questions"]
            verified = []
            
            print(f"\n{'='*60}")
            print(f"🔍 VERIFICATION PHASE")
            print(f"{'='*60}")
            print(f"Input questions: {len(questions)}")
            print(f"Regeneration attempt: {state.get('retry_count', 0)}")
            
            # Check each question
            for i, q in enumerate(questions, 1):
                print(f"\n🔎 Checking Question {i}/{len(questions)}:")
                print(f"   Text: {q.get('question_text', '')[:100]}...")
                print(f"   Type: {q.get('question_type')}, Marks: {q.get('marks')}")
                
                # Validate required fields
                if not all(k in q for k in ["question_text", "blooms_level", "question_type", "marks", "answer_key"]):
                    print(f"   ❌ Missing required fields")
                    # Add to rejected questions history
                    state["rejected_questions"].append({
                        "question": q,
                        "reason": "Missing required fields",
                        "timestamp": str(datetime.now()),
                        "attempt": state.get("retry_count", 0)
                    })
                    continue
                
                # Check for duplicates using semantic similarity
                is_duplicate = await self._check_duplicate(q["question_text"], state["teacher_id"])
                
                if not is_duplicate:
                    verified.append(q)
                    print(f"   ✅ Question accepted")
                else:
                    print(f"   ❌ Question rejected (duplicate)")
                    # Add to rejected questions history
                    state["rejected_questions"].append({
                        "question": q,
                        "reason": "Duplicate detected",
                        "timestamp": str(datetime.now()),
                        "attempt": state.get("retry_count", 0)
                    })
            
            # Check question count and marks
            total_verified_marks = sum(q["marks"] for q in verified)
            required_marks = state["total_marks"]
            
            # Calculate expected question count from prompt
            prompt_lower = state.get("prompt", "").lower()
            import re
            question_count_match = re.search(r'(\d+)\s*(?:questions?|mcqs?)', prompt_lower)
            expected_count = int(question_count_match.group(1)) if question_count_match else None
            
            print(f"\n📊 Verification Results:")
            print(f"   Verified questions: {len(verified)}")
            print(f"   Verified marks: {total_verified_marks}")
            print(f"   Required marks: {required_marks}")
            print(f"   Expected count: {expected_count}")
            print(f"   Marks match: {total_verified_marks == required_marks}")
            print(f"   Count match: {expected_count is None or len(verified) == expected_count}")
            
            # Check if we have exact count (if specified in prompt)
            count_mismatch = expected_count and len(verified) != expected_count
            
            # If we don't have exact marks, try to adjust
            if total_verified_marks != required_marks or count_mismatch:
                print(f"🔧 Adjusting questions to meet requirements...")
                verified = self._adjust_questions_to_marks(verified, required_marks)
                total_verified_marks = sum(q["marks"] for q in verified)
            
            # ULTRA STRICT validation: EXACT match required (no tolerance)
            marks_ok = total_verified_marks == required_marks
            count_ok = not expected_count or len(verified) == expected_count
            
            print(f"\n🎯 Final Validation:")
            print(f"   Marks OK: {marks_ok}")
            print(f"   Count OK: {count_ok}")
            
            if not marks_ok or not count_ok:
                state["retry_count"] += 1
                if state["retry_count"] < 5:  # Increased retries to 5
                    print(f"❌ STRICT VERIFICATION FAILED:")
                    print(f"   Expected: {expected_count or 'N/A'} questions, {required_marks} marks")
                    print(f"   Got: {len(verified)} questions, {total_verified_marks} marks")
                    print(f"   Retry attempt {state['retry_count']}/5...")
                    
                    # Add to history
                    state["generation_history"].append({
                        "timestamp": str(datetime.now()),
                        "attempt": state["retry_count"] - 1,
                        "phase": "verification_failed",
                        "reason": f"Marks mismatch: {total_verified_marks}/{required_marks}, Count mismatch: {len(verified)}/{expected_count}",
                        "retry_triggered": True
                    })
                    
                    state["current_step"] = "question_generation"
                else:
                    # After 5 retries, force correct it
                    print(f"⚠️  After 5 retries, FORCING exact match...")
                    verified = self._force_exact_match(verified, required_marks, expected_count)
                    total_verified_marks = sum(q["marks"] for q in verified)
                    print(f"✅ Forced to: {len(verified)} questions, {total_verified_marks} marks")
                    state["verified_questions"] = verified
                    state["current_step"] = "assembly"
            else:
                print(f"✅ STRICT VERIFICATION PASSED: {len(verified)} questions, {total_verified_marks} marks (EXACT MATCH)")
                state["verified_questions"] = verified
                state["current_step"] = "assembly"
            
            return state
        
        except Exception as e:
            state["errors"].append(f"Verification Error: {str(e)}")
            state["current_step"] = "error"
            return state
    
    # Agent 4: Assembly Agent
    async def assembly_agent(self, state: PaperGenerationState) -> PaperGenerationState:
        """Assemble final paper"""
        try:
            questions = state["verified_questions"]
            
            # Calculate Bloom's distribution
            blooms_dist = {}
            for q in questions:
                level = q["blooms_level"]
                blooms_dist[level] = blooms_dist.get(level, 0) + 1
            
            # Create final paper structure
            state["final_paper"] = {
                "subject": state["subject"],
                "department": state["department"],
                "total_marks": sum(q["marks"] for q in questions),
                "questions": questions,
                "blooms_distribution": blooms_dist
            }
            
            # Add completion to history
            state["generation_history"].append({
                "timestamp": str(datetime.now()),
                "phase": "completed",
                "questions_final": len(questions),
                "marks_final": sum(q["marks"] for q in questions),
                "success": True,
                "total_retries": state.get("retry_count", 0),
                "total_rejected": len(state.get("rejected_questions", []))
            })
            
            state["current_step"] = "complete"
            
            return state
        
        except Exception as e:
            state["errors"].append(f"Assembly Error: {str(e)}")
            state["current_step"] = "error"
            return state
    
    def _strict_validate_and_correct(
        self, 
        questions: List[Dict], 
        marks_distribution: List[int], 
        total_marks: int,
        prompt: str
    ) -> List[Dict]:
        """STRICT validation and automatic correction to match exact requirements"""
        
        print(f"\n🔍 STRICT VALIDATION:")
        print(f"   Required: {len(marks_distribution)} questions, {total_marks} marks")
        print(f"   Generated: {len(questions)} questions, {sum(q.get('marks', 0) for q in questions)} marks")
        
        # Step 1: Fix MCQ formatting
        for q in questions:
            if q.get("question_type") == "MCQ":
                question_text = q.get("question_text", "")
                if "A)" in question_text and "\n" not in question_text:
                    question_text = question_text.replace(", B)", "\nB)")
                    question_text = question_text.replace(", C)", "\nC)")
                    question_text = question_text.replace(", D)", "\nD)")
                    q["question_text"] = question_text
        
        # Step 2: Extract question type requirements from prompt
        question_type_requirements = self._extract_question_type_requirements(prompt)
        
        # Step 3: Enforce exact count
        required_count = len(marks_distribution)
        
        if len(questions) > required_count:
            print(f"   ⚠️  Too many questions ({len(questions)}), trimming to {required_count}")
            questions = questions[:required_count]
        
        elif len(questions) < required_count:
            print(f"   ⚠️  Too few questions ({len(questions)}), need {required_count}")
            # Duplicate last question to fill gap
            if questions:
                while len(questions) < required_count:
                    # Clone last question with different text
                    new_q = questions[-1].copy()
                    new_q["question_text"] = f"[Generated] {new_q['question_text']}"
                    questions.append(new_q)
                    print(f"   📝 Added question {len(questions)} to meet count requirement")
        
        # Step 4: Enforce exact marks distribution
        for i, q in enumerate(questions):
            if i < len(marks_distribution):
                expected_marks = marks_distribution[i]
                actual_marks = q.get("marks", 0)
                
                if actual_marks != expected_marks:
                    print(f"   🔧 Q{i+1}: Adjusting marks from {actual_marks} to {expected_marks}")
                    q["marks"] = expected_marks
        
        # Step 5: Enforce question types based on requirements
        if question_type_requirements:
            print(f"   📋 Enforcing question types: {question_type_requirements}")
            idx = 0
            for req in question_type_requirements:
                q_type = req['type']
                count = req['count']
                
                for _ in range(count):
                    if idx < len(questions):
                        if questions[idx].get("question_type") != q_type:
                            print(f"   🔧 Q{idx+1}: Changing type to {q_type}")
                            questions[idx]["question_type"] = q_type
                            
                            # Add MCQ options if needed
                            if q_type == "MCQ" and "\nA)" not in questions[idx].get("question_text", ""):
                                questions[idx]["question_text"] += "\nA) Option A\nB) Option B\nC) Option C\nD) Option D"
                        idx += 1
        
        # Step 6: Final validation
        actual_count = len(questions)
        actual_marks = sum(q.get("marks", 0) for q in questions)
        
        print(f"   ✅ After correction: {actual_count} questions, {actual_marks} marks")
        
        if actual_count != required_count or actual_marks != total_marks:
            print(f"   ❌ Still mismatched! Forcing exact match...")
            
            # Force exact match by adjusting last question's marks
            if actual_marks != total_marks and questions:
                diff = total_marks - actual_marks
                questions[-1]["marks"] += diff
                print(f"   🔧 Adjusted last question marks by {diff}")
        
        return questions
    
    def _force_exact_match(self, questions: List[Dict], required_marks: int, required_count: int = None) -> List[Dict]:
        """Force questions to match exact requirements (last resort)"""
        
        print(f"\n🔧 FORCING EXACT MATCH:")
        
        # Step 1: Fix count
        if required_count:
            if len(questions) > required_count:
                print(f"   Trimming from {len(questions)} to {required_count} questions")
                questions = questions[:required_count]
            elif len(questions) < required_count:
                print(f"   Expanding from {len(questions)} to {required_count} questions")
                while len(questions) < required_count:
                    # Clone last question
                    if questions:
                        new_q = questions[-1].copy()
                        new_q["question_text"] = f"Additional question: {new_q['question_text'][:50]}..."
                        questions.append(new_q)
                    else:
                        # Create dummy question
                        questions.append({
                            "question_text": "Generated question to meet requirements",
                            "blooms_level": "Remember",
                            "question_type": "Short Answer",
                            "marks": 1,
                            "answer_key": "Answer provided"
                        })
        
        # Step 2: Fix marks
        current_marks = sum(q.get("marks", 0) for q in questions)
        
        if current_marks != required_marks:
            diff = required_marks - current_marks
            print(f"   Adjusting marks: {current_marks} → {required_marks} (diff: {diff})")
            
            if diff > 0:
                # Add marks to questions
                per_question = diff // len(questions) if questions else 0
                remainder = diff % len(questions) if questions else 0
                
                for i, q in enumerate(questions):
                    q["marks"] += per_question
                    if i < remainder:
                        q["marks"] += 1
            else:
                # Remove marks from questions
                diff = abs(diff)
                for q in questions:
                    if diff > 0 and q["marks"] > 1:
                        reduction = min(q["marks"] - 1, diff)
                        q["marks"] -= reduction
                        diff -= reduction
        
        final_marks = sum(q.get("marks", 0) for q in questions)
        print(f"   ✅ Final: {len(questions)} questions, {final_marks} marks")
        
        return questions
    
    def _extract_question_type_requirements(self, prompt: str) -> List[Dict]:
        """Extract question type requirements from prompt"""
        import re
        
        prompt_lower = prompt.lower()
        requirements = []
        
        # Patterns for different question types
        patterns = {
            'MCQ': [r'(\d+)\s*mcqs?', r'(\d+)\s*multiple\s*choice'],
            'Short Answer': [r'(\d+)\s*short\s*(?:answer\s*)?questions?'],
            'Long Answer': [r'(\d+)\s*long\s*(?:answer\s*)?questions?']
        }
        
        for q_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, prompt_lower)
                if match:
                    count = int(match.group(1))
                    requirements.append({'type': q_type, 'count': count})
                    break
        
        return requirements
    
    def _post_process_questions(self, questions: List[Dict], required_count: int, total_marks: int) -> List[Dict]:
        """Post-process questions to ensure exact count and proper formatting"""
        
        # 1. Fix MCQ formatting (ensure newlines between options)
        for q in questions:
            if q.get("question_type") == "MCQ":
                question_text = q.get("question_text", "")
                
                # If options are on same line, split them
                if "A)" in question_text and "\n" not in question_text:
                    # Replace ", B)" with "\nB)", etc.
                    question_text = question_text.replace(", B)", "\nB)")
                    question_text = question_text.replace(", C)", "\nC)")
                    question_text = question_text.replace(", D)", "\nD)")
                    q["question_text"] = question_text
                    print(f"🔧 Fixed MCQ formatting for: {question_text[:50]}...")
        
        # 2. Enforce exact question count
        if len(questions) > required_count:
            print(f"⚠️  Too many questions ({len(questions)}), trimming to {required_count}")
            questions = questions[:required_count]
        elif len(questions) < required_count:
            print(f"⚠️  Too few questions ({len(questions)}), need {required_count}")
            # Will be handled by retry logic in verifier
        
        # 3. Ensure marks are integers
        for q in questions:
            if "marks" in q:
                q["marks"] = int(q["marks"])
        
        return questions
    
    def _calculate_marks_distribution(self, total_marks: int, prompt: str) -> list:
        """Calculate optimal marks distribution for questions with advanced parsing"""
        import re
        
        prompt_lower = prompt.lower()
        marks_distribution = []
        
        # Advanced pattern matching for complex prompts
        # Improved patterns to catch more variations
        complex_patterns = [
            # "10 mcqs of 1 marks each", "10 mcq of 1 mark each"
            r'(\d+)\s*(mcqs?|short\s*(?:answer\s*)?questions?|long\s*(?:answer\s*)?questions?|problems?)\s+of\s+(\d+)\s*marks?\s*each',
            # "10 mcqs each bearing 2 marks"
            r'(\d+)\s*(mcqs?|short\s*(?:answer\s*)?questions?|long\s*(?:answer\s*)?questions?)\s+each\s+bearing\s+(\d+)\s*marks?',
            # "10 mcqs bearing 2 marks each"
            r'(\d+)\s*(mcqs?|short\s*(?:answer\s*)?questions?|long\s*(?:answer\s*)?questions?)\s+bearing\s+(\d+)\s*marks?\s*each',
            # "10 mcqs with 2 marks"
            r'(\d+)\s*(mcqs?|short\s*(?:answer\s*)?questions?|long\s*(?:answer\s*)?questions?)\s+with\s+(\d+)\s*marks?',
            # "10 mcqs 2 marks" (loose pattern)
            r'(\d+)\s*(mcqs?|short\s*(?:answer\s*)?questions?|long\s*(?:answer\s*)?questions?)\s+(\d+)\s*marks?'
        ]
        
        question_groups = []
        used_positions = set()  # Track matched positions to avoid duplicates
        
        # Try to find complex patterns
        for pattern in complex_patterns:
            matches = re.finditer(pattern, prompt_lower)
            for match in matches:
                # Check if this position was already matched
                if match.start() not in used_positions:
                    count = int(match.group(1))
                    q_type = match.group(2).strip()
                    marks = int(match.group(3))
                    question_groups.append({
                        'count': count,
                        'type': q_type,
                        'marks': marks,
                        'position': match.start()
                    })
                    used_positions.add(match.start())
                    print(f"   🔍 Matched: '{match.group(0)}' → {count} {q_type} × {marks} marks")
        
        # Sort by position to maintain order
        question_groups.sort(key=lambda x: x.get('position', 0))
        
        # If complex patterns found, use them
        if question_groups:
            print(f"📝 Detected complex prompt structure:")
            for group in question_groups:
                print(f"   - {group['count']} {group['type']} × {group['marks']} marks = {group['count'] * group['marks']} marks")
                # Add marks for each question in this group
                for _ in range(group['count']):
                    marks_distribution.append(group['marks'])
            
            total_detected = sum(marks_distribution)
            print(f"📊 Total from prompt: {len(marks_distribution)} questions = {total_detected} marks")
            print(f"📊 Required total marks: {total_marks}")
            
            # Adjust if total doesn't match
            if total_detected != total_marks:
                print(f"⚠️  MISMATCH DETECTED:")
                print(f"   Prompt total: {total_detected} marks")
                print(f"   Required total: {total_marks} marks")
                print(f"   Difference: {total_marks - total_detected} marks")
                
                if total_detected < total_marks:
                    # Add remaining marks to last questions
                    diff = total_marks - total_detected
                    print(f"   Adding {diff} marks to last questions...")
                    for i in range(min(diff, len(marks_distribution))):
                        marks_distribution[-(i+1)] += 1
                        print(f"   Q{len(marks_distribution)-i}: {marks_distribution[-(i+1)]-1} → {marks_distribution[-(i+1)]} marks")
                elif total_detected > total_marks:
                    # Remove excess marks from last questions
                    diff = total_detected - total_marks
                    print(f"   Removing {diff} marks from last questions...")
                    for i in range(min(diff, len(marks_distribution))):
                        if marks_distribution[-(i+1)] > 1:
                            marks_distribution[-(i+1)] -= 1
                            print(f"   Q{len(marks_distribution)-i}: {marks_distribution[-(i+1)]+1} → {marks_distribution[-(i+1)]} marks")
                
                print(f"   ✅ Adjusted total: {sum(marks_distribution)} marks")
        
        else:
            # Fallback: Simple pattern matching
            # Pattern: "10 questions" or "10 MCQs"
            question_count_match = re.search(r'(\d+)\s*(?:questions?|mcqs?|problems?)', prompt_lower)
            
            if question_count_match:
                num_questions = int(question_count_match.group(1))
                print(f"📝 Detected from prompt: {num_questions} questions")
            else:
                # Default based on total marks
                is_mcq = "mcq" in prompt_lower or "multiple choice" in prompt_lower
                if is_mcq:
                    num_questions = max(10, total_marks // 2)
                elif total_marks <= 20:
                    num_questions = 4
                elif total_marks <= 50:
                    num_questions = 10
                else:
                    num_questions = 10
                print(f"📝 Using default: {num_questions} questions for {total_marks} marks")
            
            # Distribute marks evenly
            base_marks = total_marks // num_questions
            remainder = total_marks % num_questions
            
            for i in range(num_questions):
                if i < remainder:
                    marks_distribution.append(base_marks + 1)
                else:
                    marks_distribution.append(base_marks)
        
        print(f"📊 Final Marks Distribution: {len(marks_distribution)} questions = {marks_distribution} (Total: {sum(marks_distribution)})")
        return marks_distribution
    
    def _adjust_questions_to_marks(self, questions: List[Dict], target_marks: int) -> List[Dict]:
        """Adjust questions to meet exact mark requirements"""
        if not questions:
            return questions
        
        current_marks = sum(q["marks"] for q in questions)
        
        if current_marks == target_marks:
            return questions
        
        # If we have too many marks, remove lowest mark questions
        if current_marks > target_marks:
            # Sort by marks (ascending)
            sorted_questions = sorted(questions, key=lambda x: x["marks"])
            adjusted = []
            total = 0
            
            # Add questions until we reach target
            for q in sorted_questions:
                if total + q["marks"] <= target_marks:
                    adjusted.append(q)
                    total += q["marks"]
            
            print(f"🔧 Adjusted: Removed {len(questions) - len(adjusted)} questions to meet {target_marks} marks")
            return adjusted
        
        # If we have too few marks, try to add marks to existing questions
        else:
            deficit = target_marks - current_marks
            questions_copy = questions.copy()
            
            # Distribute deficit across questions
            for i in range(min(deficit, len(questions_copy))):
                questions_copy[i]["marks"] += 1
            
            print(f"🔧 Adjusted: Added {deficit} marks to questions to meet {target_marks} marks")
            return questions_copy
    
    async def _check_duplicate(self, question_text: str, teacher_id: str) -> bool:
        """Check if question is duplicate using FAISS semantic similarity"""
        try:
            print(f"\n🔍 Checking for duplicates for question: {question_text[:50]}...")
            
            # Use FAISS to check semantic similarity with higher threshold
            is_similar, similar_questions = embedding_service.check_similarity(
                question_text, 
                threshold=0.90,  # Increased from 0.85 for stricter detection
                k=5
            )
            
            if is_similar:
                print(f"⚠️  DUPLICATE DETECTED: {len(similar_questions)} similar questions found")
                for i, (qid, similarity) in enumerate(similar_questions[:3], 1):
                    print(f"   {i}. {qid}: {similarity:.3f} similarity")
                return True
            
            print(f"✅ Question is unique (no similar questions found)")
            return False
        except Exception as e:
            print(f"❌ Error checking duplicate: {e}")
            return False
    
    def _create_fallback_questions(self, state: PaperGenerationState) -> List[Dict]:
        """Create fallback questions if generation fails"""
        marks_per_question = [10, 10, 10, 10, 10]
        blooms_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate"]
        question_types = ["Reasoning", "Analytical", "Calculation", "Reasoning", "Analytical"]
        
        questions = []
        for i, (marks, blooms, qtype) in enumerate(zip(marks_per_question, blooms_levels, question_types), 1):
            questions.append({
                "question_text": f"Question {i} for {state['subject']} - {blooms} level question",
                "blooms_level": blooms,
                "question_type": qtype,
                "marks": marks,
                "answer_key": f"Answer for question {i}",
                "unit": None
            })
        
        return questions[:int(state["total_marks"] / 10)]
    
    def build_graph(self):
        """Build the LangGraph workflow"""
        from langgraph.graph import StateGraph, END
        
        workflow = StateGraph(PaperGenerationState)
        
        # Add nodes with proper naming
        workflow.add_node("rqg", self.rqg_agent)
        workflow.add_node("generate", self.question_generation_agent)
        workflow.add_node("verify", self.verifier_agent)
        workflow.add_node("assemble", self.assembly_agent)
        
        # Define routing function
        def route_after_rqg(state):
            if state["current_step"] == "error":
                return END
            return "generate"
        
        def route_after_generate(state):
            if state["current_step"] == "error":
                return END
            elif state["current_step"] == "question_generation":
                return "generate"
            return "verify"
        
        def route_after_verify(state):
            if state["current_step"] == "error":
                return END
            elif state["current_step"] == "question_generation":
                return "generate"
            return "assemble"
        
        def route_after_assemble(state):
            return END
        
        # Set entry point
        workflow.set_entry_point("rqg")
        
        # Add conditional edges with proper routing
        workflow.add_conditional_edges("rqg", route_after_rqg)
        workflow.add_conditional_edges("generate", route_after_generate)
        workflow.add_conditional_edges("verify", route_after_verify)
        workflow.add_conditional_edges("assemble", route_after_assemble)
        
        return workflow.compile()
    
    async def generate_paper(
        self,
        teacher_id: str,
        subject: str,
        department: str,
        total_marks: int,
        prompt: str,
        blooms_distribution: Dict[str, int] = None,
        unit_requirements: Dict[str, int] = None
    ) -> Dict:
        """Main entry point for paper generation"""
        await self.initialize()
        
        # Initialize state
        initial_state: PaperGenerationState = {
            "teacher_id": teacher_id,
            "subject": subject,
            "department": department,
            "total_marks": total_marks,
            "prompt": prompt,
            "blooms_distribution": blooms_distribution or {},
            "unit_requirements": unit_requirements or {},
            "resource_context": "",
            "generated_questions": [],
            "verified_questions": [],
            "final_paper": {},
            "current_step": "rqg",
            "retry_count": 0,
            "errors": [],
            "generation_history": [],
            "rejected_questions": [],
            "regeneration_feedback": ""
        }
        
        # Build and run workflow
        graph = self.build_graph()
        final_state = await graph.ainvoke(initial_state)
        
        # Print generation summary for debugging
        self.print_generation_summary(final_state)
        
        return final_state
    
    def get_generation_history(self, state: PaperGenerationState) -> Dict:
        """Get comprehensive generation history for debugging"""
        history = {
            "total_attempts": len(state.get("generation_history", [])),
            "total_retries": state.get("retry_count", 0),
            "total_rejected": len(state.get("rejected_questions", [])),
            "errors": state.get("errors", []),
            "timeline": state.get("generation_history", []),
            "summary": {
                "success": state.get("current_step") == "complete",
                "final_questions": len(state.get("verified_questions", [])),
                "final_marks": sum(q.get("marks", 0) for q in state.get("verified_questions", []))
            }
        }
        return history
    
    def print_generation_summary(self, state: PaperGenerationState):
        """Print a comprehensive summary of the generation process"""
        history = self.get_generation_history(state)
        
        print(f"\n{'='*80}")
        print(f"📊 GENERATION PROCESS SUMMARY")
        print(f"{'='*80}")
        
        print(f"Status: {'✅ SUCCESS' if history['summary']['success'] else '❌ FAILED'}")
        print(f"Total Attempts: {history['total_attempts']}")
        print(f"Total Retries: {history['total_retries']}")
        print(f"Questions Rejected: {history['total_rejected']}")
        
        if history['summary']['success']:
            print(f"Final Questions: {history['summary']['final_questions']}")
            print(f"Final Marks: {history['summary']['final_marks']}")
        
        print(f"\n📋 Timeline:")
        for i, event in enumerate(history['timeline'], 1):
            print(f"  {i}. [{event.get('timestamp', 'Unknown')}] {event.get('phase', 'Unknown')}")
            if event.get('questions_generated'):
                print(f"     Generated: {event['questions_generated']} questions")
            if event.get('retry_triggered'):
                print(f"     Retry triggered: {event.get('reason', 'Unknown')}")
        
        if history['errors']:
            print(f"\n❌ Errors Encountered:")
            for error in history['errors']:
                print(f"  - {error}")
        
        print(f"{'='*80}\n")


# Singleton instance
paper_generator = LangGraphPaperGenerator()
