#!/usr/bin/env python3
"""
Mock API server for the GWA Calculator frontend.
This provides fake data to allow the frontend to run without the full backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List, Dict, Any

app = FastAPI(
    title="GWA Calculator Mock API", 
    version="1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USERS = [
    {"id": 1, "username": "admin", "email": "admin@example.com", "is_admin": True},
    {"id": 2, "username": "student1", "email": "student1@example.com", "is_admin": False},
    {"id": 3, "username": "student2", "email": "student2@example.com", "is_admin": False},
]

MOCK_GRADES = [
    {"id": 1, "subject": "Mathematics", "grade": 85.5, "user_id": 2},
    {"id": 2, "subject": "Science", "grade": 92.0, "user_id": 2},
    {"id": 3, "subject": "English", "grade": 78.5, "user_id": 2},
    {"id": 4, "subject": "History", "grade": 88.0, "user_id": 2},
]

MOCK_POSTS = [
    {"id": 1, "title": "Welcome to GWA Calculator", "content": "This is a sample post.", "author_id": 1},
    {"id": 2, "title": "Tips for Improving Grades", "content": "Study regularly and ask questions.", "author_id": 1},
]

@app.get("/")
async def root():
    return {"message": "GWA Calculator Mock API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Authentication endpoints
@app.post("/api/login")
async def login(credentials: Dict[str, str]):
    # Simple mock authentication
    if credentials.get("username") == "admin" and credentials.get("password") == "Strongadminpass123!":
        return {"access_token": "mock_admin_token", "token_type": "bearer", "user": MOCK_USERS[0]}
    elif credentials.get("username", "").startswith("2024") and credentials.get("password") == "password123":
        return {"access_token": "mock_student_token", "token_type": "bearer", "user": MOCK_USERS[1]}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/register")
async def register(user_data: Dict[str, Any]):
    return {"message": "User registered successfully", "user": {"id": 4, **user_data}}

# User endpoints
@app.get("/api/users/me")
async def get_current_user():
    return MOCK_USERS[1]

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    for user in MOCK_USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

# Grade endpoints
@app.get("/api/grades")
async def get_grades():
    return MOCK_GRADES

@app.post("/api/grades")
async def create_grade(grade_data: Dict[str, Any]):
    new_grade = {"id": len(MOCK_GRADES) + 1, **grade_data}
    MOCK_GRADES.append(new_grade)
    return new_grade

@app.put("/api/grades/{grade_id}")
async def update_grade(grade_id: int, grade_data: Dict[str, Any]):
    for i, grade in enumerate(MOCK_GRADES):
        if grade["id"] == grade_id:
            MOCK_GRADES[i].update(grade_data)
            return MOCK_GRADES[i]
    raise HTTPException(status_code=404, detail="Grade not found")

@app.delete("/api/grades/{grade_id}")
async def delete_grade(grade_id: int):
    for i, grade in enumerate(MOCK_GRADES):
        if grade["id"] == grade_id:
            del MOCK_GRADES[i]
            return {"message": "Grade deleted successfully"}
    raise HTTPException(status_code=404, detail="Grade not found")

# Analytics endpoints
@app.get("/api/analytics/gwa/{user_id}")
async def get_gwa(user_id: int):
    user_grades = [g for g in MOCK_GRADES if g["user_id"] == user_id]
    if not user_grades:
        return {"gwa": 0.0, "total_subjects": 0}
    
    total = sum(g["grade"] for g in user_grades)
    gwa = total / len(user_grades)
    return {"gwa": round(gwa, 2), "total_subjects": len(user_grades)}

@app.get("/api/analytics/honors/{user_id}")
async def get_honors_status(user_id: int):
    gwa_data = await get_gwa(user_id)
    gwa = gwa_data["gwa"]
    
    if gwa >= 97.5:
        honors = "Summa Cum Laude"
    elif gwa >= 94.5:
        honors = "Magna Cum Laude"
    elif gwa >= 91.5:
        honors = "Cum Laude"
    else:
        honors = "No honors"
    
    return {"honors": honors, "gwa": gwa}

# Posts endpoints
@app.get("/api/posts")
async def get_posts():
    return MOCK_POSTS

@app.post("/api/posts")
async def create_post(post_data: Dict[str, Any]):
    new_post = {"id": len(MOCK_POSTS) + 1, **post_data}
    MOCK_POSTS.append(new_post)
    return new_post

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
