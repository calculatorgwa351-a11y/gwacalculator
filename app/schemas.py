from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    school_id: str
    name: str
    password: str
    department: Optional[str] = None
    course: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    school_id: str
    name: str
    department: Optional[str]
    course: Optional[str]
    
    class Config:
        from_attributes = True

class GradeCreate(BaseModel):
    subject: str
    units: float = 3.0
    grade: float
    year: int = 1
    semester: int = 1

class GradeResponse(BaseModel):
    id: int
    subject: str
    units: float
    grade: float
    year: int
    semester: int
    timestamp: datetime
    failed: bool
    gwa: Optional[float] = None
    
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    content: str
    author: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ReactionCreate(BaseModel):
    type: str

class CommentCreate(BaseModel):
    content: str
