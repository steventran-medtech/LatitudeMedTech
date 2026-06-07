# Athena Silent Launcher
# Starts the FastAPI backend and Vite frontend as hidden processes,
# waits until both are ready, then opens Chrome to localhost:3000.
# Writes .athena_ready flag only AFTER Chrome process is confirmed running.

. "C:\Users\huann\LatitudeMedTech\Athena\ui\athena_lib.ps1"

$VENV_PY  = "$ATHENA\voice\venv\Scripts\python.exe"
$SERVER   = "$ATHENA\ui\backend\server.py"
$FRONT    = "$ATHENA\ui\frontend"
$flagFile  = "$ATHENA\ui\.athena_ready"
$errFile   = "$ATHENA\ui\.athena_error"
$abortFile = "$ATHENA\ui\.athena_abort"

# Remove stale flag/error from any previous run
foreach ($f in @($flagFile, $errFile, $abortFile)) { if (Test-Path $f) { Remove-Item $f -Force } }

# ── Duplicate-instance guard ────────────────────────────────────────────────
# If Athena is already up, don't silently kill its backend and spawn a second
# window. Warn the user and let them decide. The splash (started by the .vbs
# before us) is released via the ready flag on every exit path so it never hangs.
if (Test-AthenaRunning) {
    $choice = Show-DuplicateWarning
    if ($choice -ne 'Yes') {
        $shown = Show-ExistingAthena
        if (-not $shown) {
            # Chrome was not running (closed or crashed) — reopen it to the existing backend.
            $chrome = @(
                "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
                "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
                "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
            ) | Where-Object { Test-Path $_ } | Select-Object -First 1
            if ($chrome) {
                Start-Process $chrome -ArgumentList @(
                    "--start-maximized",
                    "--user-data-dir=$CHROME_PROFILE",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--hide-crash-restore-bubble",
                    "http://localhost:3000"
                )
            } else {
                Start-Process "http://localhost:3000"
            }
        }
        New-Item -Path $abortFile -ItemType File -Force | Out-Null   # tell splash to close immediately
        exit 0
    }
    # User chose to restart: stop the existing instance cleanly first.
    & "$ATHENA\ui\stop_athena.ps1"
}

# ── Recover an orphaned session ────────────────────────────────────────────
# A leftover stamp means the previous run never reached stop_athena.ps1 (backend
# crash, hard taskkill, power loss). Flush it to the log as crash-terminated before
# starting fresh, using the stamp's last-write time as the best end estimate.
if (Test-Path $SESSION_STATE) {
    try {
        $prev = Get-Content $SESSION_STATE -Raw -Encoding utf8 | ConvertFrom-Json
        $lastAlive = (Get-Item $SESSION_STATE).LastWriteTime
        $rec = [ordered]@{ ended_at = $lastAlive.ToString("o"); end_reason = "crash_or_no_clean_stop" }
        foreach ($p in $prev.PSObject.Properties) { $rec[$p.Name] = $p.Value }
        if ($prev.started_at) {
            $rec["duration_secs"] = [math]::Round(($lastAlive - [datetime]$prev.started_at).TotalSeconds)
        }
        ($rec | ConvertTo-Json -Compress) | Out-File $SESSION_LOG -Append -Encoding utf8
    } catch { }
    Remove-Item $SESSION_STATE -Force -ErrorAction SilentlyContinue
}

# ── Stamp the start of this overall Athena session (for QA/debug duration log) ──
$sessionStart = Get-Date
$session = [ordered]@{
    started_at    = $sessionStart.ToString("o")
    host          = $env:COMPUTERNAME
    user          = $env:USERNAME
    backend_up    = $false
    frontend_up   = $false
    models_ready  = $false
    model_load_s  = $null
    chrome_pid    = $null
    launch_ok     = $false
}
$session | ConvertTo-Json -Compress | Out-File $SESSION_STATE -Encoding utf8

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

# Voice models preload asynchronously in a background thread (voice_bridge.py
# _preload_models). Chrome opens as soon as backend + frontend are ready;
# the voice WS status event carries models_ready so the UI reflects loading state.
# Removing the blocking model-wait (DI-019-K CO-008): startup time under 10s on warm start.
$session.backend_up   = $true
$session.frontend_up  = $frontendUp
$session.models_ready = $false   # updated async by voice_bridge; not tracked here
$session.model_load_s = $null

# ── Signal the splash BEFORE opening Chrome ───────────────────────────────
# Writing the flag now lets the splash finish its 95→100% countdown and
# close cleanly. Chrome is opened only after the splash is gone so the two
# windows never appear on screen at the same time.
$session.launch_ok    = $true
$session.ready_at     = (Get-Date).ToString("o")
$session.startup_secs = [math]::Round(((Get-Date) - $sessionStart).TotalSeconds, 1)
$session | ConvertTo-Json -Compress | Out-File $SESSION_STATE -Encoding utf8
New-Item -Path $flagFile -ItemType File -Force | Out-Null

# Splash detects the flag, animates from cap (~97%) to 100%, and closes in ~1s.
# 2.5s sleep gives the splash ~1.5s of margin before Chrome opens (DI-019-G: < 3s gap).
Start-Sleep -Milliseconds 2500

# ── Open Chrome ────────────────────────────────────────────────────────────
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    # Isolated profile => its own browser process tree, every member of which
    # carries --user-data-dir=$CHROME_PROFILE in its command line. stop_athena.ps1
    # closes exactly that instance by matching on this path — the user's main
    # Chrome (default profile) is never touched.
    $chromeArgs = @(
        "--start-maximized",
        "--user-data-dir=$CHROME_PROFILE",
        "--no-first-run",
        "--no-default-browser-check",
        # We force-kill this instance on exit, which Chrome reads as a crash on the next
        # launch. This flag suppresses the "Restore pages?" bubble; stop_athena.ps1 also
        # rewrites the profile's exit_type to clean as a second line of defence.
        "--hide-crash-restore-bubble",
        "http://localhost:3000"
    )
    Start-Process $chrome -ArgumentList $chromeArgs
} else {
    Start-Process "http://localhost:3000"
}

# ── Wait for our isolated Chrome window, then record its main PID ───────────
# WMI is reliable here (normal console); we do the command-line match now so
# stop can simply taskkill the PID tree without WMI in its detached context.
if (Test-Path $CHROME_PID_FILE) { Remove-Item $CHROME_PID_FILE -Force -ErrorAction SilentlyContinue }
$maxWait = 20   # seconds
$elapsed = 0
while ($elapsed -lt $maxWait) {
    $mine = Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$CHROME_PROFILE*" -and $_.CommandLine -notlike "*--type=*" }
    if ($mine) {
        $chromePid = ($mine | Select-Object -First 1).ProcessId
        $chromePid | Out-File $CHROME_PID_FILE -Encoding ascii
        $session.chrome_pid = $chromePid
        $session | ConvertTo-Json -Compress | Out-File $SESSION_STATE -Encoding utf8
        break
    }
    Start-Sleep -Milliseconds 400
    $elapsed += 0.4
}
