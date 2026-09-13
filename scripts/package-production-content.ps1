param(
    [string]$OutputDir = "deploy-content"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$dbPath = Join-Path $repoRoot "db.sqlite3"
$mediaPath = Join-Path $repoRoot "media"

if (-not (Test-Path $dbPath)) {
    throw "Local SQLite database was not found at $dbPath"
}

if (-not (Test-Path $mediaPath)) {
    throw "Media folder was not found at $mediaPath"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$packageRoot = Join-Path $repoRoot $OutputDir
$staging = Join-Path $packageRoot "ytr-content-$timestamp"
$archive = Join-Path $packageRoot "ytr-content-$timestamp.zip"

New-Item -ItemType Directory -Force -Path $staging | Out-Null
Copy-Item -LiteralPath $dbPath -Destination (Join-Path $staging "db.sqlite3") -Force
Copy-Item -LiteralPath $mediaPath -Destination (Join-Path $staging "media") -Recurse -Force

$restoreScript = @'
#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: ./restore-production-content.sh <container-id-or-name>"
  exit 1
fi

container="$1"
docker cp db.sqlite3 "$container":/app/data/db.sqlite3
docker cp media/. "$container":/app/media/
docker exec "$container" chown -R app:app /app/data /app/media
echo "Content restored. Restart the application in Coolify so SQLite reopens cleanly."
'@

$restoreScript | Set-Content -Path (Join-Path $staging "restore-production-content.sh") -Encoding ascii

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $archive -Force
Remove-Item -LiteralPath $staging -Recurse -Force

Write-Host "Created $archive"
Write-Host "Upload this zip to the Coolify host, unzip it, then run:"
Write-Host "  ./restore-production-content.sh <container-id-or-name>"
