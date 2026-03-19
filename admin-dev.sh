#!/bin/bash

# Port 3001 for Admin Panel
# Port 8000 for Bot API

echo "🚀 Starting SpeedLoad Admin Panel Setup..."

if [ ! -d "admin/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd admin && npm install
    cd ..
fi

echo "🔑 Creating .env from .env.example..."
if [ ! -f "admin/.env" ]; then
    cp admin/.env.example admin/.env
fi

echo "⚡ Launching Admin Panel on http://localhost:3001"
cd admin && npm run dev
