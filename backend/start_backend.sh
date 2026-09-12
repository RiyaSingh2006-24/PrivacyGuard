#!/bin/bash

cd "$(dirname "$0")"

source venv/bin/activate

echo "======================================"
echo " PrivacyGuard Security Engine"
echo " Local API: http://127.0.0.1:8000"
echo "======================================"

exec uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000
