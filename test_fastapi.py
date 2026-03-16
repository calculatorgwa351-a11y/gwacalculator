#!/usr/bin/env python3
"""
Simple FastAPI test to verify the framework works
"""

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "FastAPI is working!"}
    
    print("✅ FastAPI app created successfully")
    print("🚀 FastAPI framework is ready to use!")
    
except ImportError as e:
    print(f"❌ FastAPI not available: {e}")
    print("📦 Install with: pip install fastapi uvicorn")
