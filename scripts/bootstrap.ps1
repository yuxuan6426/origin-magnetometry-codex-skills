param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$version = & $Python -c 'import sys; print(".".join(map(str,sys.version_info[:3])))'
if ($LASTEXITCODE -ne 0 -or $version -ne '3.13.9') {
    throw 'The validated Windows baseline uses Python 3.13.9. Pass -Python with that interpreter.'
}
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    }
    $taskPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
    & $taskPython -m pip install -r requirements-win64.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed.' }
    & $taskPython -m pip install --no-deps -e ./third_party/origin-mcp
    if ($LASTEXITCODE -ne 0) { throw 'Fixed MCP snapshot installation failed.' }
    & $taskPython scripts/doctor.py
    if ($LASTEXITCODE -ne 0) { throw 'Read-only doctor failed.' }
} finally { Pop-Location }
