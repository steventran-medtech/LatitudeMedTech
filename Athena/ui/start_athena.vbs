' Athena launcher — shows branded splash, starts all processes silently.
Set oShell = CreateObject("WScript.Shell")

' 1. Show branded splash immediately (polls localhost until ready, then closes itself)
oShell.Run "mshta.exe """ & "C:\Users\huann\LatitudeMedTech\Athena\ui\start_splash.hta""", 1, False

' 2. Run startup script silently in background (starts backend + frontend + Chrome)
oShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File " & _
    Chr(34) & "C:\Users\huann\LatitudeMedTech\Athena\ui\start_athena.ps1" & Chr(34), _
    0, False
