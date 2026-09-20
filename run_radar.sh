#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
if [ ! -d .venv ]; then "$PYTHON" -m venv .venv; fi
. .venv/bin/activate
python -m pip install -r requirements.txt
exec python -m streamlit run app.py
