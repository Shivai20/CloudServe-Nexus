#!/bin/bash
# CloudServe FDE Capstone Evaluator Setup Script (macOS/Linux)

echo "🚀 Setting up CloudServe Support Pipeline Environment..."

# 1. Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# 2. Create Virtual Environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating fresh virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment (.venv) already exists."
fi

# 3. Activate Virtual Environment & Install Requirements
echo "⚙️ Installing/Updating dependencies from requirements.txt..."
./.venv/bin/python3 -m pip install --upgrade pip --quiet
./.venv/bin/python3 -m pip install -r requirements.txt

echo -e "\n✅ Environment successfully configured!"
echo -e "\nTo activate the environment and run the pipeline, run:"
echo -e "  source .venv/bin/activate"
echo -e "  python -m pytest tests/ -v"
echo -e "  uvicorn src.api:app --reload\n"
