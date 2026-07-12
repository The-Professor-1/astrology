# Run Django migrations against your Neon PostgreSQL database.
# Usage (from project root):
#   1. Set env vars in Vercel / Neon dashboard, OR copy them into astrology/variables.env
#   2. powershell -ExecutionPolicy Bypass -File scripts/migrate_neon.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$envFile = Join-Path $root "astrology\variables.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim("'").Trim('"')
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

$required = @('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST')
foreach ($key in $required) {
    if (-not (Get-Item "env:$key" -ErrorAction SilentlyContinue)) {
        Write-Error "Missing $key. Set it in astrology/variables.env or your shell environment."
    }
}

Write-Host "Checking migration status..."
python manage.py showmigrations calculator
Write-Host ""
Write-Host "Applying migrations..."
python manage.py migrate
Write-Host ""
Write-Host "Done."
