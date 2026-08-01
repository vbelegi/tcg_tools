# Backend pytest with coverage gate
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location (Join-Path $Root "backend")
py -3.13 -m pip install -q -e ".[dev]"
py -3.13 -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
