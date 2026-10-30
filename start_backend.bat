@echo off
title SmartTraffic AI - FastAPI Backend Server (:8000)
echo ================================================================
echo Starting FastAPI Backend Server on http://127.0.0.1:8000
echo Swagger API Documentation: http://127.0.0.1:8000/docs
echo WebSocket Streaming Channel: ws://127.0.0.1:8000/ws/traffic
echo ================================================================
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause

