$ErrorActionPreference = 'Stop'
$Root = Resolve-Path "$PSScriptRoot/.."
Set-Location "$Root/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
