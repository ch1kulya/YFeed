$LockFile = "dependencies.lock"
$Requirements = "requirements.txt"

Write-Host "Checking if Python is installed..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python."
    Read-Host -Prompt "Press any key to continue . . ."
    exit 1
}

try {
    python -m venv --help > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw "venv module is not available." }
} catch {
    Write-Host "venv module is not available."
    Read-Host -Prompt "Press any key to continue . . ."
    exit 1
}

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

& .\venv\Scripts\Activate.ps1

try {
    python -m pip --version > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw "pip not found." }
} catch {
    Write-Host "Installing pip..."
    python -m ensurepip > $null 2>&1
    python -m pip install --upgrade pip --disable-pip-version-check > $null 2>&1
}

if (-not (Test-Path $LockFile)) {
    Write-Host "Lock file not found. Installing dependencies..."
    python -m pip install --disable-pip-version-check -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies."
        Read-Host -Prompt "Press any key to continue . . ."
        exit 1
    }
    Copy-Item $Requirements $LockFile -Force
} else {
    $reqContent = Get-Content $Requirements -Raw
    $lockContent = Get-Content $LockFile -Raw
    if ($reqContent -ne $lockContent) {
        Write-Host "Requirements have changed. Updating dependencies..."
        python -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to update dependencies."
            Read-Host -Prompt "Press any key to continue . . ."
            exit 1
        }
        Copy-Item $Requirements $LockFile -Force
    } else {
        Write-Host "Python dependencies are up to date."
    }
}

python src\main.py
Read-Host -Prompt "Press any key to continue . . ."
exit 1
