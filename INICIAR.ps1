$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Execute scripts/setup-local.ps1 antes de iniciar.' }
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'backend')
& $python manage.py check
if ($LASTEXITCODE -ne 0) { throw 'Configuração inválida; consulte README.md.' }
Write-Host 'GATI local: http://127.0.0.1:8765 — Ctrl+C encerra a aplicação.'
& $python manage.py runserver 127.0.0.1:8765 --noreload
