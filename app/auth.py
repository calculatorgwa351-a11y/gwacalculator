from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from app.database import get_db
from app.models import User, Admin

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Session persistence - use memory sessions as fallback
sessions = {}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user_from_token(token: str, db: Session):
    payload = verify_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current user from JWT token in cookie"""
    token = request.cookies.get("access_token")
    if token:
        user = get_current_user_from_token(token, db)
        if user:
            return user
    
    # Fallback to session-based auth
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        user_id = sessions[session_id]
        return db.query(User).filter(User.id == user_id).first()
    
    return None

def create_session(user_id: int) -> str:
    """Create a session for fallback auth"""
    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = user_id
    return session_id

def is_admin(user: User, db: Session) -> bool:
    if not user:
        return False
    return db.query(Admin).filter(Admin.user_id == user.id).first() is not None
