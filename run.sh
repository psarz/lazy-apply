#!/bin/bash
source venv/bin/activate 2>/dev/null || true
echo "Starting AutoApply Local..."
streamlit run app.py --server.headless=false
