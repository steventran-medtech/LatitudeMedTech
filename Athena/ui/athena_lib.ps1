# Athena shared launcher helpers.
# Dot-sourced by start_athena.ps1 and stop_athena.ps1.

$ATHENA   = "C:\Users\huann\LatitudeMedTech\Athena"
$LOG_DIR  = "$ATHENA\ui\logs"
$BACK_LOG = "$LOG_DIR\backend.log"
$FRONT_LOG= "$LOG_DIR\frontend.log"

if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }

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
