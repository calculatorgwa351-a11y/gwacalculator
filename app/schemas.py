from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    school_id: str
    name: str
    password: str
    department: Optional[str] = None
    course: Optional[str] = None

class UserUpdate(BaseModel):
    school_id: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
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

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    course: Optional[str] = None
    password: Optional[str] = None

class GradeCreate(BaseModel):
    subject: str
    units: float = 3.0
    grade: float
    year: int = 1
    semester: int = 1

class GradeUpdate(BaseModel):
    subject: Optional[str] = None
    units: Optional[float] = None
    grade: Optional[float] = None
    year: Optional[int] = None
    semester: Optional[int] = None

class GradesBulkCreate(BaseModel):
    items: List[GradeCreate]

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

class PostUpdate(BaseModel):
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
    parent_id: Optional[int] = None
