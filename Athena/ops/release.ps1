<#
.SYNOPSIS
    Cut a new Athena version: stamp VERSION.json, sync package.json, and tag git.

.DESCRIPTION
    Single source of truth for the running version is Athena/VERSION.json. This
    script bumps it to the version you name, stamps today's date, mirrors the
    number into the frontend package.json, and (unless -NoTag) creates an
    annotated git tag v<version>.

    It does NOT write your changelog for you. Before running this, move your
    "[Unreleased]" notes in CHANGELOG.md under a new "## [<version>] - <date>"
    heading. The script reminds you and refuses to tag if that section is missing.

.PARAMETER Version
    The new semantic version, e.g. 0.6.0 (no leading "v").

.PARAMETER Channel
    Release channel: alpha | beta | rc | stable. Defaults to the current channel.

.PARAMETER Codename
    Optional release codename (defaults to the current one).

.PARAMETER NoTag
    Skip creating the git tag (just update the files).

.EXAMPLE
    ./ops/release.ps1 -Version 0.6.0
    ./ops/release.ps1 -Version 1.0.0 -Channel stable -Codename "La Jolla"
#>
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$Channel,
    [string]$Codename,
    [switch]$NoTag
)

$ErrorActionPreference = "Stop"

# Athena root = parent of this script's folder (ops/ -> Athena/)
$Athena      = Split-Path -Parent $PSScriptRoot
$VersionFile = Join-Path $Athena "VERSION.json"
$Changelog   = Join-Path $Athena "CHANGELOG.md"
$Pkg         = Join-Path $Athena "ui\frontend\package.json"

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must be MAJOR.MINOR.PATCH (e.g. 0.6.0). Got: '$Version'"
}

# ── Load + update VERSION.json ────────────────────────────────────────────────
$info = Get-Content $VersionFile -Raw | ConvertFrom-Json
$today = Get-Date -Format "yyyy-MM-dd"

$info.version  = $Version
$info.released = $today
if ($Channel)  { $info.channel  = $Channel }
if ($Codename) { $info.codename = $Codename }

# ── Guard: changelog must already document this version ───────────────────────
$clText = Get-Content $Changelog -Raw
if ($clText -notmatch "(?m)^##\s*\[$([regex]::Escape($Version))\]") {
    Write-Warning "CHANGELOG.md has no '## [$Version]' section yet."
    Write-Warning "Move your [Unreleased] notes under a new '## [$Version] - $today' heading first."
    if (-not $NoTag) { throw "Refusing to tag a version that isn't in the changelog. Re-run with -NoTag to override." }
}

# ── Write VERSION.json (pretty) ───────────────────────────────────────────────
($info | ConvertTo-Json -Depth 5) | Out-File $VersionFile -Encoding utf8
Write-Host "Stamped VERSION.json -> v$Version ($($info.channel)) $today" -ForegroundColor Green

# ── Mirror into frontend package.json ─────────────────────────────────────────
if (Test-Path $Pkg) {
    $pkgJson = Get-Content $Pkg -Raw | ConvertFrom-Json
    $pkgJson.version = $Version
    ($pkgJson | ConvertTo-Json -Depth 10) | Out-File $Pkg -Encoding utf8
    Write-Host "Synced ui/frontend/package.json -> v$Version" -ForegroundColor Green
}

# ── Tag git ───────────────────────────────────────────────────────────────────
if (-not $NoTag) {
    Push-Location $Athena
    try {
        git tag -a "v$Version" -m "Athena v$Version"
        Write-Host "Created git tag v$Version" -ForegroundColor Green
        Write-Host "Next: commit VERSION.json + CHANGELOG.md + package.json, then 'git push --tags'." -ForegroundColor Cyan
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Skipped git tag (-NoTag). Remember to tag when ready: git tag -a v$Version -m 'Athena v$Version'" -ForegroundColor Yellow
}
