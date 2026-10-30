"""
Convenience Runner Script
Launches the FastAPI Backend (which serves the APIs and streaming WebSocket).
"""

import os
import sys
import uvicorn

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("================================================================")
    print("Starting FastAPI Backend Server on http://127.0.0.1:8000")
    print("Interactive API Documentation: http://127.0.0.1:8000/docs")
    print("Frontend is expected at: http://127.0.0.1:5500")
    print("================================================================")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

