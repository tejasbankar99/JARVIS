# JARVIS — Install & Run Script (PowerShell)
# Run this once to set up JARVIS:  .\setup.ps1

Write-Host "`n  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   J.A.R.V.I.S — Setup Initializing   ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "  [CHECK] Python: $pythonVersion" -ForegroundColor White

# Create virtual environment
Write-Host "`n  [1/4] Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if (-not (Test-Path ".venv")) {
    Write-Host "  [ERROR] Failed to create venv. Is Python 3.10+ installed?" -ForegroundColor Red
    exit 1
}

# Activate venv
Write-Host "  [2/4] Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "  [3/4] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "  [4/4] Installing JARVIS dependencies..." -ForegroundColor Yellow
Write-Host "        (This may take a few minutes)" -ForegroundColor Gray

# Install dependencies (includes PyAudioWPatch for modern Windows Python support)
pip install -r requirements.txt

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "`n  [SETUP] Created .env from template." -ForegroundColor Green
    Write-Host "  *** ACTION REQUIRED: Edit .env and add your GROQ_API_KEY (Free: console.groq.com) or other AI key ***" -ForegroundColor Cyan
} else {
    Write-Host "`n  [OK] .env already exists." -ForegroundColor Green
}

# Create output directories
New-Item -ItemType Directory -Force -Path "screenshots" | Out-Null
New-Item -ItemType Directory -Force -Path "code_output" | Out-Null

Write-Host "`n  ══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Setup complete! To run JARVIS:" -ForegroundColor Green
Write-Host ""
Write-Host "    Double click START_JARVIS.bat     # One-click start" -ForegroundColor White
Write-Host "    Double click START_LISTENER.bat   # Always-on wake-word listener" -ForegroundColor White
Write-Host "    python main.py                    # Full GUI" -ForegroundColor White
Write-Host "    python main.py --cli              # Text-only CLI" -ForegroundColor White
Write-Host "  ══════════════════════════════════════`n" -ForegroundColor Cyan
