#!/bin/bash

set -e

echo "🚀 Starting Databricks Assessment Tool..."

# Set default port
PORT=${BACKEND_PORT:-8002}

echo "📦 Installing Python dependencies..."
cd backend
pip install -q --no-cache-dir -r requirements.txt

echo "🎨 Building frontend..."
cd ../frontend
npm install --silent --no-audit
npm run build

echo "🚀 Starting application on port ${PORT}..."
cd ../backend
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}
