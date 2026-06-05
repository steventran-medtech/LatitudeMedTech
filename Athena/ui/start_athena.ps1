# Athena Silent Launcher
# Starts the FastAPI backend and Vite frontend as hidden processes,
# waits until both are ready, then opens Chrome to localhost:3000.
# Writes .athena_ready flag only AFTER Chrome process is confirmed running.

$ATHENA  = "C:\Users\huann\LatitudeMedTech\Athena"
$VENV_PY = "$ATHENA\voice\venv\Scripts\python.exe"
$SERVER  = "$ATHENA\ui\backend\server.py"
$FRONT   = "$ATHENA\ui\frontend"
$flagFile = "$ATHENA\ui\.athena_ready"

function Wait-Http($url, $maxSeconds = 35) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $maxSeconds) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop | Out-Null
            return $true
        } catch { Start-Sleep -Milliseconds 700 }
    }
    return $false
}

# Remove stale flag from any previous run
if (Test-Path $flagFile) { Remove-Item $flagFile -Force }

# Kill leftover processes from a previous crashed run
@("python","node") | ForEach-Object {
    Stop-Process -Name $_ -Force -ErrorAction SilentlyContinue
}

# ── Start backend (hidden) ─────────────────────────────────────────────────
$backendInfo = New-Object System.Diagnostics.ProcessStartInfo
$backendInfo.FileName         = $VENV_PY
$backendInfo.Arguments        = "`"$SERVER`""
$backendInfo.WorkingDirectory = "$ATHENA\ui\backend"
$backendInfo.CreateNoWindow   = $true
$backendInfo.WindowStyle      = [System.Diagnostics.ProcessWindowStyle]::Hidden
$backendInfo.UseShellExecute  = $false
[System.Diagnostics.Process]::Start($backendInfo) | Out-Null

# ── Start frontend (hidden) ────────────────────────────────────────────────
$viteCmd = "$FRONT\node_modules\.bin\vite.cmd"
$frontInfo = New-Object System.Diagnostics.ProcessStartInfo
$frontInfo.FileName         = "cmd.exe"
$frontInfo.Arguments        = "/c `"$viteCmd`""
$frontInfo.WorkingDirectory = $FRONT
$frontInfo.CreateNoWindow   = $true
$frontInfo.WindowStyle      = [System.Diagnostics.ProcessWindowStyle]::Hidden
$frontInfo.UseShellExecute  = $false
$frontInfo.EnvironmentVariables["BROWSER"] = "none"
[System.Diagnostics.Process]::Start($frontInfo) | Out-Null

# ── Wait for both services ─────────────────────────────────────────────────
Wait-Http "http://127.0.0.1:8000/" 35 | Out-Null
Wait-Http "http://localhost:3000"   20 | Out-Null

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
$chromePid = $null
$maxWait   = 20   # seconds
$elapsed   = 0
while ($elapsed -lt $maxWait) {
    $procs = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) {
        $chromePid = $procs[0].Id
        break
    }
    Start-Sleep -Milliseconds 400
    $elapsed += 0.4
}

# Give Chrome's window one more second to render its first frame,
# then signal the splash — no more, no less.
Start-Sleep -Seconds 1

# Write flag: HTA sees this and closes within 500ms
New-Item -Path $flagFile -ItemType File -Force | Out-Null
