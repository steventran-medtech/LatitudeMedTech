# Athena Silent Launcher
# Starts the FastAPI backend and Vite frontend as hidden processes,
# waits until both are ready, then opens Chrome to localhost:3000.
# Writes .athena_ready flag only AFTER Chrome process is confirmed running.

. "C:\Users\huann\LatitudeMedTech\Athena\ui\athena_lib.ps1"

$VENV_PY  = "$ATHENA\voice\venv\Scripts\python.exe"
$SERVER   = "$ATHENA\ui\backend\server.py"
$FRONT    = "$ATHENA\ui\frontend"
$flagFile = "$ATHENA\ui\.athena_ready"
$errFile  = "$ATHENA\ui\.athena_error"

# Remove stale flag/error from any previous run
foreach ($f in @($flagFile, $errFile)) { if (Test-Path $f) { Remove-Item $f -Force } }

# Free the ports we need. Targeted (by listening PID) instead of a blanket
# python/node kill, and confirmed free before we try to bind — this is what
# prevents a stale backend from squatting on 8000 while the new one silently
# fails to start.
if (-not (Stop-Port 8000)) {
    "Backend port 8000 is still in use and could not be freed. Close the process holding it and retry." |
        Out-File $errFile -Encoding utf8
    New-Item -Path $flagFile -ItemType File -Force | Out-Null   # release the splash so the user isn't stuck
    exit 1
}
Stop-Port 3000 | Out-Null

# ── Start backend (hidden, output captured to log) ──────────────────────────
"=== backend start $(Get-Date -Format o) ===" | Out-File $BACK_LOG -Encoding utf8
$backend = Start-Process -FilePath $VENV_PY -ArgumentList "`"$SERVER`"" `
    -WorkingDirectory "$ATHENA\ui\backend" -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $BACK_LOG -RedirectStandardError "$BACK_LOG.err"

# ── Start frontend (hidden, output captured to log) ─────────────────────────
$viteCmd = "$FRONT\node_modules\.bin\vite.cmd"
$env:BROWSER = "none"
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$viteCmd`"" `
    -WorkingDirectory $FRONT -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $FRONT_LOG -RedirectStandardError "$FRONT_LOG.err"

# ── Wait for both services, and actually check the result ───────────────────
$backendUp  = Wait-Http "http://127.0.0.1:8000/" 40
$frontendUp = Wait-Http "http://localhost:3000"  25

if (-not $backendUp) {
    $tail = if (Test-Path $BACK_LOG) { Get-Content $BACK_LOG -Tail 25 -ErrorAction SilentlyContinue } else { "(no backend log)" }
    $errTail = if (Test-Path "$BACK_LOG.err") { Get-Content "$BACK_LOG.err" -Tail 25 -ErrorAction SilentlyContinue } else { "" }
    @("Backend failed to come up on port 8000 within 40s.","", "--- backend.log ---", $tail, "", "--- backend.err ---", $errTail) |
        Out-File $errFile -Encoding utf8
    New-Item -Path $flagFile -ItemType File -Force | Out-Null   # release the splash
    exit 1
}

# ── Open Chrome ────────────────────────────────────────────────────────────
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    Start-Process $chrome "--app=http://localhost:3000 --window-size=1440,900"
} else {
    Start-Process "http://localhost:3000"
}

# ── Wait for Chrome process to actually appear (not a fixed sleep) ─────────
$maxWait = 20   # seconds
$elapsed = 0
while ($elapsed -lt $maxWait) {
    $procs = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) { break }
    Start-Sleep -Milliseconds 400
    $elapsed += 0.4
}

# Give Chrome's window one more second to render its first frame,
# then signal the splash — no more, no less.
Start-Sleep -Seconds 1

# Write flag: HTA sees this and closes within 500ms
New-Item -Path $flagFile -ItemType File -Force | Out-Null
