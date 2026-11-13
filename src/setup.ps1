param([string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    if ($PythonPath) {
        & $PythonPath -m venv .venv
    } else {
        py -3.12 -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 or supply -PythonPath pointing to it.' }
}
& $projectPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; see messages above.' }
& $projectPython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Software checks failed.' }
Write-Host 'Setup finished. Run launch.ps1. Read README before connecting electrodes.'
