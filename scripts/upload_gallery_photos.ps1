param(
    [switch]$Execute,
    [switch]$Sync
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot 'photos\Selection_processed'
$envFile = Join-Path $repoRoot '.env'
$localRclone = Join-Path $repoRoot '.tools\rclone\rclone-v1.73.2-windows-amd64\rclone.exe'
$destination = 'r2:photos/photos/Selection_processed'

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Missing processed photos: $source"
}
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
    throw "Missing local credentials file: $envFile"
}

$settings = @{}
foreach ($line in Get-Content -LiteralPath $envFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        $settings[$matches[1]] = $matches[2].Trim().Trim('"', "'")
    }
}

foreach ($key in @('CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_ACCESS_KEY_IDS3', 'CLOUDFLARE_SECRET_ACCESS_KEY_S3')) {
    if (-not $settings[$key]) {
        throw "Missing $key in .env"
    }
}

$installedRclone = Get-Command rclone -ErrorAction SilentlyContinue
if ($installedRclone) {
    $rclone = $installedRclone.Source
} elseif (Test-Path -LiteralPath $localRclone -PathType Leaf) {
    $rclone = $localRclone
} else {
    throw 'rclone.exe was not found. Install rclone or place it under .tools/rclone/.'
}

# Environment configuration avoids writing the R2 secret to an rclone config file.
$env:RCLONE_CONFIG_R2_TYPE = 's3'
$env:RCLONE_CONFIG_R2_PROVIDER = 'Cloudflare'
$env:RCLONE_CONFIG_R2_ACCESS_KEY_ID = $settings['CLOUDFLARE_ACCESS_KEY_IDS3']
$env:RCLONE_CONFIG_R2_SECRET_ACCESS_KEY = $settings['CLOUDFLARE_SECRET_ACCESS_KEY_S3']
$env:RCLONE_CONFIG_R2_ENDPOINT = "https://$($settings['CLOUDFLARE_ACCOUNT_ID']).r2.cloudflarestorage.com"
$env:RCLONE_CONFIG_R2_REGION = 'auto'

$operation = if ($Sync) { 'sync' } else { 'copy' }
$arguments = @($operation, $source, $destination, '--exclude', 'archive/**', '--stats', '10s')
if (-not $Execute) {
    $arguments += '--dry-run'
    Write-Host "Previewing $operation; no R2 objects will change."
} else {
    Write-Host "Running $operation from processed photos to $destination"
}

& $rclone @arguments
if ($LASTEXITCODE -ne 0) {
    throw "rclone exited with code $LASTEXITCODE"
}

if ($Execute) {
    Write-Host 'Checking that every local processed photo exists in R2 with the same size.'
    & $rclone check $source $destination --one-way --size-only --exclude 'archive/**'
    if ($LASTEXITCODE -ne 0) {
        throw "R2 verification failed with code $LASTEXITCODE"
    }
}
