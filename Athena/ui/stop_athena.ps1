# Athena stop — targeted shutdown by port + command line, then verify.
# Avoids blanket "kill every python.exe" which can hit unrelated processes
# and which silently failed in practice.

. "C:\Users\huann\LatitudeMedTech\Athena\ui\athena_lib.ps1"

$flagFile = "$ATHENA\ui\.athena_ready"
if (Test-Path $flagFile) { Remove-Item $flagFile -Force -ErrorAction SilentlyContinue }

# 1. Kill whatever holds the service ports.
$port8000 = Stop-Port 8000
$port3000 = Stop-Port 3000
Stop-Port 8002 | Out-Null   # Kokoro TTS sidecar — orphaned if server died without clean stop

# 2. Belt-and-braces: kill any Athena backend/frontend identified by command
#    line, in case they crashed without holding the port. Scoped to this repo
#    path so unrelated python/node keep running.
try {
    Get-CimInstance Win32_Process -ErrorAction Stop |
        Where-Object {
            $_.CommandLine -and (
                $_.CommandLine -like "*ui\backend\server.py*" -or
                ($_.CommandLine -like "*vite*" -and $_.CommandLine -like "*Athena*")
            )
        } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop }
            catch { Write-Host "[athena] could not kill PID $($_.ProcessId): $_" }
        }
} catch { Write-Host "[athena] process scan failed: $_" }

# 3. Close the isolated Chrome app window via the main PID recorded at launch.
#    taskkill /T kills the whole process tree (window + renderers/gpu/utility),
#    and works in the detached/no-window context where WMI command-line queries
#    are unreliable. Scoped to that one instance — the user's main Chrome is safe.
if (Test-Path $CHROME_PID_FILE) {
    $chromePid = (Get-Content $CHROME_PID_FILE -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($chromePid) { taskkill /PID $chromePid /T /F *> $null }
    Remove-Item $CHROME_PID_FILE -Force -ErrorAction SilentlyContinue
}

# 3a. Now that Chrome is force-killed, rewrite its isolated profile's exit_type so the
#     next launch doesn't show "Restore pages? Chrome didn't shut down correctly".
Set-ChromeProfileClean

# 4. Report.
$b = if ($port8000 -and -not (Get-PortPids 8000)) { "stopped" } else { "STILL RUNNING" }
$f = if ($port3000 -and -not (Get-PortPids 3000)) { "stopped" } else { "STILL RUNNING" }
Write-Host "Backend (8000): $b"
Write-Host "Frontend (3000): $f"

# 5. Log the overall Athena session (start->stop) for QA/debug. Reads the launch
#    stamp written by start_athena.ps1, computes wall-clock duration, and appends
#    one JSON line to logs\athena_sessions.jsonl alongside shutdown metadata.
$endedAt = Get-Date
$record = [ordered]@{
    ended_at        = $endedAt.ToString("o")
    end_reason      = "clean_stop"
    backend_stop    = $b
    frontend_stop   = $f
}
if (Test-Path $SESSION_STATE) {
    try {
        $s = Get-Content $SESSION_STATE -Raw -Encoding utf8 | ConvertFrom-Json
        foreach ($p in $s.PSObject.Properties) { $record[$p.Name] = $p.Value }
        if ($s.started_at) {
            $record["duration_secs"] = [math]::Round(($endedAt - [datetime]$s.started_at).TotalSeconds)
        }
    } catch { $record["session_state_error"] = "$_" }
    Remove-Item $SESSION_STATE -Force -ErrorAction SilentlyContinue
} else {
    $record["note"] = "no session state found (start stamp missing)"
}
try { ($record | ConvertTo-Json -Compress) | Out-File $SESSION_LOG -Append -Encoding utf8 }
catch { Write-Host "[athena] could not write session log: $_" }

if ($b -ne "stopped" -or $f -ne "stopped") { exit 1 }
