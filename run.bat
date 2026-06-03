@echo off
cd /d "%~dp0"
echo Starting College RAG Chatbot...

echo Starting Backend...
start cmd /k "venv\Scripts\activate.bat && python main.py"

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both backend and frontend are starting in separate windows!
