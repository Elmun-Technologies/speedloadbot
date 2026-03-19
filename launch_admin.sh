#!/bin/bash

# Launch script for SpeedLoad Command Center

echo "🚀 SpeedLoad Command Center ishga tushirilmoqda..."

# 1. Backend API ni fonda ishlatish
echo "📡 Backend API (FastAPI) ishga tushmoqda..."
./.venv/bin/python3 -m uvicorn api.main:app --reload --port 8000 &
API_PID=$!

# 2. Frontend Dashboard ni ishlatish
echo "🖥 Frontend Dashboard (Next.js) ishga tushmoqda..."
cd dashboard && npm run dev &
FRONT_PID=$!

echo "✅ SpeedLoad Dashboard tayyor!"
echo "🔗 URL: http://localhost:3000"
echo "🛠 API: http://localhost:8000"

# Ctrl+C bosilganda ikkala jarayonni ham to'xtatish
trap "kill $API_PID $FRONT_PID; exit" INT
wait
