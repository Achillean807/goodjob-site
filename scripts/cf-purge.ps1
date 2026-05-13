# cf-purge.ps1 - Goodjob Site Cloudflare cache purge helper
#
# Purpose: After deploy, purge frequently-changing HTML / sitemap so CF edge picks up the new content immediately.
# Uses dedicated token: CLOUDFLARE_PURGE_TOKEN_GOODJOB (zone:weddingwishlove.com, Cache Purge:Purge)
#
# Usage:
#   pwsh scripts/cf-purge.ps1                  # purge default list (sitemap + homepage + support pages)
#   pwsh scripts/cf-purge.ps1 -Files "https://goodjob.weddingwishlove.com/sitemap.xml"
#   pwsh scripts/cf-purge.ps1 -All             # purge_everything = true (use with care)

[CmdletBinding()]
param(
    [string[]]$Files,
    [switch]$All
)

$ErrorActionPreference = 'Stop'

# --- Load credentials from ~/.claude/.cf-env ---
$envFile = Join-Path $HOME ".claude/.cf-env"
if (-not (Test-Path $envFile)) {
    Write-Error "Credentials file not found: $envFile. Set CLOUDFLARE_PURGE_TOKEN_GOODJOB / CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE first."
    exit 1
}

$creds = @{}
Get-Content $envFile | Where-Object { $_ -match '^[A-Z_][A-Z0-9_]*=' } | ForEach-Object {
    $kv = $_ -split '=', 2
    $creds[$kv[0]] = $kv[1]
}

$token = $creds['CLOUDFLARE_PURGE_TOKEN_GOODJOB']
$zoneId = $creds['CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE']

if (-not $token -or -not $zoneId) {
    Write-Error "CLOUDFLARE_PURGE_TOKEN_GOODJOB or CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE not set."
    exit 1
}

# --- Build payload ---
$defaultFiles = @(
    "https://goodjob.weddingwishlove.com/",
    "https://goodjob.weddingwishlove.com/sitemap.xml",
    "https://goodjob.weddingwishlove.com/robots.txt",
    "https://goodjob.weddingwishlove.com/llms.txt",
    "https://goodjob.weddingwishlove.com/teabar.html",
    "https://goodjob.weddingwishlove.com/workflow.html",
    "https://goodjob.weddingwishlove.com/sort-hat/",
    "https://goodjob.weddingwishlove.com/muse-2026.html",
    "https://goodjob.weddingwishlove.com/wedding-packages/",
    "https://goodjob.weddingwishlove.com/wedding-packages/outdoor.html"
)

if ($All) {
    $payload = @{ purge_everything = $true } | ConvertTo-Json -Compress
    Write-Host "[cf-purge] purge_everything = true (full zone wipe)" -ForegroundColor Yellow
} else {
    $targetFiles = if ($Files -and $Files.Count -gt 0) { $Files } else { $defaultFiles }
    # Force array notation even when single URL (ConvertTo-Json scalars single-element arrays otherwise)
    $payload = @{ files = @($targetFiles) } | ConvertTo-Json -Compress
    Write-Host "[cf-purge] purging $($targetFiles.Count) URL(s):" -ForegroundColor Cyan
    $targetFiles | ForEach-Object { Write-Host "   - $_" }
}

# --- Call CF API ---
$url = "https://api.cloudflare.com/client/v4/zones/$zoneId/purge_cache"
$headers = @{
    'Authorization' = "Bearer $token"
    'Content-Type'  = 'application/json'
    'User-Agent'    = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 cf-purge.ps1'
}

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $payload
    if ($response.success) {
        Write-Host "[cf-purge] OK (job id: $($response.result.id))" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "[cf-purge] FAILED:" -ForegroundColor Red
        $response.errors | ForEach-Object { Write-Host "   - [$($_.code)] $($_.message)" -ForegroundColor Red }
        exit 1
    }
} catch {
    Write-Host "[cf-purge] HTTP error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}
