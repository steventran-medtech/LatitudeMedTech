# Athena shared launcher helpers.
# Dot-sourced by start_athena.ps1 and stop_athena.ps1.

$ATHENA   = "C:\Users\huann\LatitudeMedTech\Athena"
$LOG_DIR  = "$ATHENA\ui\logs"
$BACK_LOG = "$LOG_DIR\backend.log"
$FRONT_LOG= "$LOG_DIR\frontend.log"
# Athena's Chrome app window runs as an isolated instance (its own profile dir)
# so we can close exactly that window on exit — every process of that instance
# carries this path in its command line — without touching the user's main Chrome.
# start_athena.ps1 resolves the instance's main PID (via WMI, in a normal console
# where it's reliable) and writes it here; stop just taskkill /T's that PID tree.
$CHROME_PROFILE  = "$ATHENA\ui\.chrome-profile"
$CHROME_PID_FILE = "$ATHENA\ui\.athena_chrome.pid"

# Overall-session bookkeeping (the whole Athena run, not just a voice exchange).
# start_athena.ps1 stamps $SESSION_STATE at launch; stop_athena.ps1 reads it,
# computes the wall-clock duration, and appends one record to $SESSION_LOG for QA/debug.
$SESSION_STATE = "$ATHENA\ui\.athena_session.json"
$SESSION_LOG   = "$LOG_DIR\athena_sessions.jsonl"

if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }

# Mark the isolated Chrome profile as having exited cleanly. We force-kill Chrome on
# stop (taskkill /T /F), which leaves exit_type="Crashed" in the profile Preferences
# and triggers the "Restore pages? Chrome didn't shut down correctly" bubble on the
# next launch. Rewriting these two keys to a clean state suppresses that prompt without
# touching the user's main Chrome (this only edits the isolated .chrome-profile).
function Set-ChromeProfileClean {
    $prefs = Join-Path $CHROME_PROFILE "Default\Preferences"
    if (-not (Test-Path $prefs)) { return }
    try {
        $json = Get-Content $prefs -Raw -Encoding utf8 | ConvertFrom-Json
        if (-not $json.profile) {
            $json | Add-Member -NotePropertyName profile -NotePropertyValue ([pscustomobject]@{}) -Force
        }
        $json.profile | Add-Member -NotePropertyName exit_type      -NotePropertyValue "Normal" -Force
        $json.profile | Add-Member -NotePropertyName exited_cleanly  -NotePropertyValue $true    -Force
        ($json | ConvertTo-Json -Depth 100 -Compress) | Out-File $prefs -Encoding utf8 -NoNewline
    } catch {
        Write-Host "[athena] could not mark Chrome profile clean: $_"
    }
}

# Return the PIDs (if any) listening on a TCP port.
function Get-PortPids($port) {
    try {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    } catch { @() }
}

# Force-kill whatever is listening on $port, then confirm the port is free.
# Returns $true if the port is free when we finish, $false otherwise.
function Stop-Port($port, $timeoutSec = 8) {
    $procPids = @(Get-PortPids $port)
    foreach ($procId in $procPids) {
        if ($procId -and $procId -ne 0) {
            try { Stop-Process -Id $procId -Force -ErrorAction Stop }
            catch { Write-Host "[athena] could not kill PID $procId on port $port : $_" }
        }
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
        if (-not (Get-PortPids $port)) { return $true }
        Start-Sleep -Milliseconds 300
    }
    return -not (Get-PortPids $port)
}

# Poll an HTTP endpoint until it responds or we time out.
# "Responds" means any HTTP reply, including non-2xx: the Vite dev server answers
# the bare "/" probe with 404, which still proves it's up and listening. Treating
# only a 2xx as success made frontend_up log false negatives. Real not-ready states
# (connection refused / timeout) raise an exception with no .Response, so we retry.
function Wait-Http($url, $maxSeconds = 35) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $maxSeconds) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop | Out-Null
            return $true
        } catch {
            if ($_.Exception.Response) { return $true }   # got an HTTP status (e.g. 404) => server is up
            Start-Sleep -Milliseconds 700
        }
    }
    return $false
}
