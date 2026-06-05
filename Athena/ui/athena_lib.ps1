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

# Is an Athena instance already up? True if our backend answers on 8000 OR our
# isolated Chrome instance (matched by profile dir / pid file) is still alive.
# This is what start_athena.ps1 checks to avoid silently restarting a live
# session and spawning a duplicate window.
function Test-AthenaRunning {
    # Backend listening on 8000?
    if (@(Get-PortPids 8000).Count -gt 0) { return $true }
    # Our recorded Chrome main PID still a live chrome.exe?
    if (Test-Path $CHROME_PID_FILE) {
        $savedPid = (Get-Content $CHROME_PID_FILE -ErrorAction SilentlyContinue | Select-Object -First 1) -as [int]
        if ($savedPid) {
            $p = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
            if ($p -and $p.ProcessName -eq 'chrome') { return $true }
        }
    }
    return $false
}

# Best-effort: bring the existing Athena Chrome window to the foreground so the
# user lands on the session they already have instead of a fresh one.
#
# A hidden/background process can't just call SetForegroundWindow — Windows'
# foreground lock silently ignores it. We work around it the standard way:
# attach our input thread to the target window's thread (which lifts the lock
# for the duration), toggle SW_MINIMIZE->SW_RESTORE so a minimized window pops
# back, then SetForegroundWindow + BringWindowToTop, and detach.
function Show-ExistingAthena {
    if (-not (Test-Path $CHROME_PID_FILE)) { return }
    $savedPid = (Get-Content $CHROME_PID_FILE -ErrorAction SilentlyContinue | Select-Object -First 1) -as [int]
    if (-not $savedPid) { return }

    Add-Type -Namespace Win32 -Name Fg -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr hWnd);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool BringWindowToTop(System.IntPtr hWnd);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr hWnd, int nCmdShow);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool IsIconic(System.IntPtr hWnd);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint pid);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
'@ -ErrorAction SilentlyContinue

    # The recorded PID is our instance's main Chrome process and owns the window.
    # MainWindowHandle can read as 0 transiently, so poll briefly. If it never
    # populates (e.g. the saved PID is stale), fall back to the chrome process
    # whose command line carries OUR profile dir — never an arbitrary chrome, so
    # the user's main Chrome window is never grabbed.
    $hwnd = [System.IntPtr]::Zero
    for ($i = 0; $i -lt 20; $i++) {
        try { $hwnd = (Get-Process -Id $savedPid -ErrorAction SilentlyContinue).MainWindowHandle } catch { }
        if ($hwnd -and $hwnd -ne [System.IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 100
    }
    if (-not $hwnd -or $hwnd -eq [System.IntPtr]::Zero) {
        try {
            $minePids = Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -and $_.CommandLine -like "*$CHROME_PROFILE*" -and $_.CommandLine -notlike "*--type=*" } |
                Select-Object -ExpandProperty ProcessId
            foreach ($mp in @($minePids)) {
                $cand = (Get-Process -Id $mp -ErrorAction SilentlyContinue).MainWindowHandle
                if ($cand -and $cand -ne [System.IntPtr]::Zero) { $hwnd = $cand; break }
            }
        } catch { }
    }
    if (-not $hwnd -or $hwnd -eq [System.IntPtr]::Zero) { return }

    try {
        if ([Win32.Fg]::IsIconic($hwnd)) { [Win32.Fg]::ShowWindow($hwnd, 6) | Out-Null }  # SW_MINIMIZE (settle state)
        [Win32.Fg]::ShowWindow($hwnd, 9) | Out-Null                                       # SW_RESTORE

        $fg = [Win32.Fg]::GetForegroundWindow()
        $tgtPid = 0
        $tgtThread = [Win32.Fg]::GetWindowThreadProcessId($hwnd, [ref]$tgtPid)
        $fgPid = 0
        $fgThread = [Win32.Fg]::GetWindowThreadProcessId($fg, [ref]$fgPid)
        $cur = [Win32.Fg]::GetCurrentThreadId()

        [Win32.Fg]::AttachThreadInput($cur, $fgThread, $true)  | Out-Null
        [Win32.Fg]::AttachThreadInput($cur, $tgtThread, $true) | Out-Null
        [Win32.Fg]::BringWindowToTop($hwnd)     | Out-Null
        [Win32.Fg]::SetForegroundWindow($hwnd)  | Out-Null
        [Win32.Fg]::AttachThreadInput($cur, $tgtThread, $false) | Out-Null
        [Win32.Fg]::AttachThreadInput($cur, $fgThread, $false) | Out-Null
    } catch { }
}

# Modal Yes/No warning shown when a second launch is attempted while Athena is
# already running. Returns 'Yes' (restart), 'No' (keep current), or 'Cancel'.
function Show-DuplicateWarning {
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
    $nl  = [Environment]::NewLine
    $msg = "Athena is already running." + $nl + $nl +
           "Starting another copy will close your current session and may open a duplicate window." + $nl + $nl +
           "Restart Athena anyway?" + $nl + $nl +
           "Yes - Close the current session and start fresh." + $nl +
           "No - Keep the current session (bring it to front)."
    $result = [System.Windows.Forms.MessageBox]::Show(
        $msg, "Athena",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning,
        [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
    return $result.ToString()
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
