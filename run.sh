#!/bin/bash
set -e

echo "=== Installing Python deps ==="
pip install -r backend/requirements.txt --quiet

echo "=== Building frontend ==="
cd frontend
npm install --silent
npm run build
cd ..

echo "=== Starting server ==="
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
