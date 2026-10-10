$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\pythonw.exe')) {
    throw 'Run py -3.12 -m venv .venv and install requirements.txt first. See README.md.'
}
Start-Process -FilePath '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
