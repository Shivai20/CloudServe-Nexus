# CloudServe FDE Capstone Evaluator Setup Script (Windows/PowerShell)
Write-Host "🚀 Setting up CloudServe Support Pipeline Environment..." -ForegroundColor Cyan

# 1. Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# 2. Create Virtual Environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating fresh virtual environment (.venv)..."
    python -m venv .venv
} else {
    Write-Host "✅ Virtual environment (.venv) already exists."
}

# 3. Activate Virtual Environment & Install Requirements
Write-Host "⚙️ Installing/Updating dependencies from requirements.txt..."
# We invoke python directly from the venv so we don't have to change the host's active shell
.\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "`n✅ Environment successfully configured!" -ForegroundColor Green
Write-Host "`nTo activate the environment and run the pipeline, run:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python -m pytest tests/ -v"
Write-Host "  uvicorn src.api:app --reload`n"
