from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId


class Resource(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    teacher_id: str
    filename: str
    file_type: str  # "pdf", "docx", "pptx", "image"
    gridfs_id: Optional[str] = None  # GridFS file ID
    file_path: Optional[str] = None  # Legacy: local file path (deprecated)
    file_size: int
    extracted_text: Optional[str] = None
    topics: List[str] = []
    subject: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None  # Academic year
    section: Optional[str] = None  # Section/class
    uploaded_by: Optional[str] = None  # Teacher name
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
