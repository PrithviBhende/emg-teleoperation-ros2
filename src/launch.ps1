$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Run setup.ps1 first (Python 3.12 recommended).'
}
& $projectPython (Join-Path $PSScriptRoot 'main.py')
