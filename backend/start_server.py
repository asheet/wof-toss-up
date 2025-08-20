#!/usr/bin/env python3
"""
Simple server starter for the Wheel of Fortune Toss-up backend
"""

import uvicorn
import os

if __name__ == "__main__":
    # Change to the directory containing main.py
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("🚀 Starting Wheel of Fortune backend server...")
    print("📡 Server will be available at: http://localhost:8001")
    print("🔗 Frontend should connect to: ws://localhost:8001/ws")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )