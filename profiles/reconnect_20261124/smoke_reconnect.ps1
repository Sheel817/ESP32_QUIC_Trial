# Reconnect smoke test: capture N s from one host reset; kill the server at -KillAt s, restart it at -RestartAt s.
# Usage: powershell -File smoke_reconnect.ps1 -Proto quic|tcp_tls -OutDir <dir> [-Port COM6] [-Seconds 300] [-KillAt 90] [-RestartAt 120]
param([string]$Proto, [string]$OutDir, [string]$Port = 'COM6', [int]$Seconds = 300, [int]$KillAt = 90, [int]$RestartAt = 120)
$root = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial'; $prof = Join-Path $root 'profiles\reconnect_20261124'
$idfPy = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe'; $srvPy = Join-Path $root '.quic-venv\Scripts\python.exe'
$server = if ($Proto -eq 'tcp_tls') { 'tcp_tls_server.py' } else { 'quic_server.py' }
New-Item -ItemType Directory -Force $OutDir | Out-Null; $OutDir = (Resolve-Path $OutDir).Path
function Note($m) { "$([DateTime]::UtcNow.ToString('o')) $m" | Add-Content (Join-Path $OutDir 'smoke_events.log') -Encoding utf8 }
function StartServer($n) {
    $p = Start-Process $srvPy -ArgumentList '-u', $server -WorkingDirectory $root -RedirectStandardOutput (Join-Path $OutDir "server$n`_stdout.log") -RedirectStandardError (Join-Path $OutDir "server$n`_stderr.log") -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 3; Note "SERVER_STARTED n=$n pid=$($p.Id)"; return $p
}
$s1 = StartServer 1
$cap = Start-Process $idfPy -ArgumentList '-I', (Join-Path $prof 'capture_long.py'), (Join-Path $OutDir 'serial_raw'), '--seconds', $Seconds, '--reset', '--port', $Port -RedirectStandardOutput (Join-Path $OutDir 'capture_stdout.txt') -RedirectStandardError (Join-Path $OutDir 'capture_stderr.txt') -WindowStyle Hidden -PassThru
Note "CAPTURE_STARTED pid=$($cap.Id)"
Start-Sleep -Seconds $KillAt; Stop-Process -Id $s1.Id -Force; Note 'SERVER_KILLED'
Start-Sleep -Seconds ($RestartAt - $KillAt); $s2 = StartServer 2
$cap.WaitForExit(); Note "CAPTURE_ENDED exit=$($cap.ExitCode)"
Stop-Process -Id $s2.Id -Force -ErrorAction SilentlyContinue; Note 'SERVER_STOPPED'
