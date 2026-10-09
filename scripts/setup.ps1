$ErrorActionPreference = 'Stop'
$Root = Resolve-Path "$PSScriptRoot/.."

Write-Host "[VAJRA AI] Installing backend dependencies"
python -m pip install --upgrade pip
pip install -r "$Root/backend/requirements.txt" -r "$Root/backend/requirements-dev.txt"

Write-Host "[VAJRA AI] Installing dashboard dependencies"
Set-Location "$Root/dashboard"
npm install

Write-Host "[VAJRA AI] Installing mobile dependencies"
Set-Location "$Root/mobile"
npm install

Write-Host "Setup complete."
