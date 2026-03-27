$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonCandidates = @(
  (Join-Path $root ".venv314\Scripts\python.exe"),
  (Join-Path $root ".venv\Scripts\python.exe"),
  "python"
)

$python = $pythonCandidates | Where-Object { $_ -eq "python" -or (Test-Path $_) } | Select-Object -First 1

Push-Location $root
try {
  & $python (Join-Path $root "scripts\migrate_sqlite_to_supabase.py") @args
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
