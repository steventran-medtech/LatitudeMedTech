# Athena stop — targeted shutdown by port + command line, then verify.
# Avoids blanket "kill every python.exe" which can hit unrelated processes
# and which silently failed in practice.

. "C:\Users\huann\LatitudeMedTech\Athena\ui\athena_lib.ps1"

$flagFile = "$ATHENA\ui\.athena_ready"
if (Test-Path $flagFile) { Remove-Item $flagFile -Force -ErrorAction SilentlyContinue }

# 1. Kill whatever holds the service ports.
$port8000 = Stop-Port 8000
$port3000 = Stop-Port 3000

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

# 3. Report.
$b = if ($port8000 -and -not (Get-PortPids 8000)) { "stopped" } else { "STILL RUNNING" }
$f = if ($port3000 -and -not (Get-PortPids 3000)) { "stopped" } else { "STILL RUNNING" }
Write-Host "Backend (8000): $b"
Write-Host "Frontend (3000): $f"
if ($b -ne "stopped" -or $f -ne "stopped") { exit 1 }
