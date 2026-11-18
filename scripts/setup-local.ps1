param([switch]$UseDocker)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$version = & python -c 'import sys; print(sys.version_info >= (3,14))'
if ($LASTEXITCODE -ne 0 -or $version -ne 'True') { throw 'Instale Python 3.14 e disponibilize python no PATH.' }
if (-not (Test-Path -LiteralPath 'backend/.venv/Scripts/python.exe')) {
    & python -m venv backend/.venv
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python.' }
}
$python = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
& $python -m pip install -r backend/requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Instalação das dependências falhou.' }
if (-not (Test-Path -LiteralPath 'backend/.env')) { & $python scripts/prepare_env.py }
if ($UseDocker) {
    & docker compose --env-file backend/.env -f infra/local/compose.yml up -d --wait
    if ($LASTEXITCODE -ne 0) { throw 'Os serviços locais não ficaram prontos. Verifique Docker e as portas 5432/3310.' }
}
Set-Location -LiteralPath (Join-Path $projectRoot 'backend')
& $python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Banco indisponível. Confira backend/.env e inicie PostgreSQL 18.' }
& $python manage.py bootstrap_gati
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar os cadastros estruturais.' }
& $python manage.py collectstatic --noinput
Write-Host 'Preparado. Crie seu usuário com backend/.venv/Scripts/python.exe backend/manage.py bootstrap_gati --admin (a partir da raiz).'
