$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Starting Kind Compliance..."
Write-Host ""

# ----------------------------------------
# Check Python 3.12
# ----------------------------------------

Write-Host "[1/6] Checking Python 3.12..."

try {
    py -3.12 --version
}
catch {
    Write-Host "Python 3.12 is required."
    Write-Host "Please install Python 3.12 first."
    exit 1
}


# ----------------------------------------
# Create virtual environment if required
# ----------------------------------------

Write-Host ""
Write-Host "[2/6] Checking virtual environment..."

if (-not (Test-Path ".venv\Scripts\python.exe")) {

    Write-Host "Creating virtual environment..."

    py -3.12 -m venv .venv

}
else {

    Write-Host "Virtual environment already exists."

}


$python = ".\.venv\Scripts\python.exe"


# ----------------------------------------
# Install packages
# ----------------------------------------

Write-Host ""
Write-Host "[3/6] Installing Python packages..."

& $python -m pip install -r requirements.txt


# ----------------------------------------
# Create .env if required
# ----------------------------------------

Write-Host ""
Write-Host "[4/6] Checking environment configuration..."

if (-not (Test-Path ".env")) {

    Copy-Item ".env.example" ".env"

    Write-Host ".env created."

}
else {

    Write-Host ".env already exists."

}


# ----------------------------------------
# Check Docker
# ----------------------------------------

Write-Host ""
Write-Host "[5/6] Starting PostgreSQL..."

docker info *> $null

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "Docker Desktop is not running."
    Write-Host "Please open Docker Desktop and run this script again."

    exit 1
}


docker compose up -d


# ----------------------------------------
# Initialise database
# ----------------------------------------

Write-Host ""
Write-Host "[6/6] Initialising database..."

& $python -m flask --app run.py init-db


# ----------------------------------------
# Start Flask
# ----------------------------------------

Write-Host ""
Write-Host "=========================================="
Write-Host " Kind Compliance is starting"
Write-Host "=========================================="
Write-Host ""
Write-Host "Open:"
Write-Host "http://127.0.0.1:5000"
Write-Host ""
Write-Host "Press CTRL+C to stop the server."
Write-Host ""

& $python -m flask --app run.py run --debug