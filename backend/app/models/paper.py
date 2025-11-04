from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId


class Question(BaseModel):
    question_text: str
    blooms_level: str  # Remember, Understand, Apply, Analyze, Evaluate, Create
    question_type: str  # Reasoning, Analytical, Calculation, Diagrammatic
    marks: int
    answer_key: str
    unit: Optional[str] = None


class Paper(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    teacher_id: str
    subject: str
    department: str
    section: Optional[str] = None
    year: Optional[int] = None
    exam_date: Optional[datetime] = None
    total_marks: int
    generation_prompt: str
    questions: List[Question] = []
    blooms_distribution: Dict[str, int] = {}
    question_paper_pdf: Optional[str] = None  # GridFS file ID
    answer_key_pdf: Optional[str] = None  # GridFS file ID
    status: str = "draft"  # draft, approved, published
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
