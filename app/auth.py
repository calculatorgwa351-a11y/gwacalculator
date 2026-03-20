from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from app.database import get_db
from app.models import User, Admin

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', '7d8f9e0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Extended to 1 hour
COOKIE_NAME = "access_token"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a secure JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Error encoding JWT: {e}")
        return None

def verify_token(token: str):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Standard dependency to get the current authenticated user from JWT cookie"""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
        
    payload = verify_token(token)
    if payload is None:
        return None
        
    user_id = payload.get("sub")
    if user_id is None:
        return None
        
    try:
        user_id = int(user_id)
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except (ValueError, TypeError):
        return None

def is_admin(user: User, db: Session) -> bool:
    """Check if a user has administrative privileges"""
    if not user:
        return False
    admin = db.query(Admin).filter(Admin.user_id == user.id).first()
    return admin is not None

def require_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dependency to enforce admin-only access"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not is_admin(user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return user

def require_user(user: User = Depends(get_current_user)):
    """Dependency to enforce authenticated-user-only access"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
