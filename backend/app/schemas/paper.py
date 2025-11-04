from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class GeneratePaperRequest(BaseModel):
    subject: str
    department: str
    section: Optional[str] = None
    year: Optional[int] = None
    exam_date: Optional[datetime] = None
    exam_type: Optional[str] = "Final"  # Mid, Final, Internal, etc.
    total_marks: int
    prompt: Optional[str] = ""
    
    # Question categories with counts and marks
    mcq_count: Optional[int] = 0
    mcq_marks: Optional[int] = 1
    short_count: Optional[int] = 0
    short_marks: Optional[int] = 2
    medium_count: Optional[int] = 0
    medium_marks: Optional[int] = 5
    long_count: Optional[int] = 0
    long_marks: Optional[int] = 10
    
    # Question source ratios (must sum to 100)
    previous_percent: Optional[int] = 30  # From previous papers
    creative_percent: Optional[int] = 40  # Modified existing
    new_percent: Optional[int] = 30  # AI-generated new
    
    # Legacy support
    blooms_distribution: Optional[Dict[str, int]] = None
    unit_requirements: Optional[Dict[str, int]] = None


class QuestionResponse(BaseModel):
    question_text: str
    blooms_level: str  # Remember, Understand, Apply, Analyze, Evaluate, Create
    question_type: str  # MCQ, Short, Medium, Long
    marks: int
    answer_key: str
    unit: Optional[str] = None
    options: Optional[List[str]] = None  # For MCQ questions
    correct_answer: Optional[str] = None  # For MCQ (A, B, C, D)
    source: Optional[str] = "new"  # previous, creative, new
    difficulty: Optional[str] = None  # Easy, Medium, Hard
    explanation: Optional[str] = None  # Detailed explanation for answer key


class PaperResponse(BaseModel):
    id: str
    subject: str
    department: str
    total_marks: int
    questions: List[QuestionResponse]
    blooms_distribution: Dict[str, int]
    status: str
    created_at: datetime


class ApprovePaperRequest(BaseModel):
    paper_id: str


class RegeneratePaperRequest(BaseModel):
    paper_id: str
    feedback_prompt: Optional[str] = None  # Optional feedback to improve the paper


class EditApprovedPaperRequest(BaseModel):
    feedback_prompt: str  # Edit instructions for the approved paper


class UpdatePaperMetadataRequest(BaseModel):
    subject: Optional[str] = None
    department: Optional[str] = None
    section: Optional[str] = None
    year: Optional[int] = None
    total_marks: Optional[int] = None
