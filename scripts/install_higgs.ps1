$ErrorActionPreference = "Stop"

if (-not $env:HIGGS_REPO_URL) {
  Write-Error "HIGGS_REPO_URL is not set. Example: setx HIGGS_REPO_URL https://github.com/YOUR_ORG/higgs-audio.git"
}

$HiggsDir = $env:HIGGS_DIR
if (-not $HiggsDir) { $HiggsDir = "third_party/higgs-audio" }
$HiggsVenv = $env:HIGGS_VENV_DIR
if (-not $HiggsVenv) { $HiggsVenv = ".venv-higgs" }

if (-not (Test-Path $HiggsDir)) {
  git clone $env:HIGGS_REPO_URL $HiggsDir
} else {
  Write-Host "Higgs repo already exists at $HiggsDir"
}

Set-Location $HiggsDir

if ((Test-Path "pyproject.toml") -or (Test-Path "setup.py")) {
  if (-not (Test-Path $HiggsVenv)) {
    python -m venv $HiggsVenv
  }
  & "$HiggsVenv\Scripts\Activate.ps1"
  pip install --upgrade pip
  if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
  }
  pip install -e .
  Write-Host "Installed Higgs in editable mode."
} else {
  Write-Error "No Python packaging files found. Follow Higgs repo build instructions."
}

Write-Host "Done. Ensure the Higgs CLI is available in PATH (see repo docs)."
