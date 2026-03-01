$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python is not installed or not on PATH."
}

python -m pip install --user --upgrade shellsensei

Write-Host "ShellSensei installed for current user."
Write-Host "Run: shellsensei --help"
