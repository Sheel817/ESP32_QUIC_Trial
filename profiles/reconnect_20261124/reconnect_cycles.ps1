# Controlled reconnect test (RECONNECT profile, normal network, no Clumsy, Wi-Fi stays up). Image must already be flashed.
# Usage: powershell -ExecutionPolicy Bypass -File reconnect_cycles.ps1 -Proto quic|tcp_tls -OutDir <dir> [-Port COM6]
#        [-Cycles 20] [-RunSec 60] [-DownSec 10] [-ReconnectTimeoutSec 180]
# Order: pre-checks -> server -> hotspot watchdog -> serial capture with ONE host reset -> wait for the first CONNECT ->
#   per cycle: connection runs RunSec s -> kill server -> wait DownSec s -> restart server (READY) -> wait for the board's
#   next RECONNECT line. All host times are UTC; the analysis (analyze_cycles.py) pairs them with the serial log.
# Exit code 0 = all cycles done (individual reconnect failures are data, recorded as timeouts); 2 = aborted.
param([ValidateSet('tcp_tls','quic')][string]$Proto, [string]$OutDir, [string]$Port = 'COM6', [int]$Cycles = 20,
      [int]$RunSec = 60, [int]$DownSec = 10, [int]$ReconnectTimeoutSec = 180)
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial'
$prof = Join-Path $root 'profiles\reconnect_20261124'
$idfPy = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe'
$srvPy = Join-Path $root '.quic-venv\Scripts\python.exe'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$srvPort = if ($Proto -eq 'tcp_tls') { 14568 } else { 14567 }
$server = if ($Proto -eq 'tcp_tls') { 'tcp_tls_server.py' } else { 'quic_server.py' }
$serial = Join-Path $OutDir 'serial_raw.log'
function Utc { [DateTime]::UtcNow.ToString('o') }
function Note($o) { ($o | ConvertTo-Json -Compress) | Add-Content -Path (Join-Path $OutDir 'cycles.jsonl') -Encoding utf8 }
function CountLines($pat) {
    if (-not (Test-Path $serial)) { return 0 }
    return @(Select-String -Path $serial -Pattern $pat -ErrorAction SilentlyContinue).Count
}
function StartServer($n) {
    $o = Join-Path $OutDir ("server{0:D2}_stdout.log" -f $n); $e = Join-Path $OutDir ("server{0:D2}_stderr.log" -f $n)
    $startUtc = Utc
    $p = Start-Process -FilePath $srvPy -ArgumentList '-u', $server -WorkingDirectory $root -RedirectStandardOutput $o -RedirectStandardError $e -WindowStyle Hidden -PassThru
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and -not (Select-String -Path $o -Pattern '^READY' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 100 }
    $readyUtc = Utc
    if (-not (Select-String -Path $o -Pattern '^READY' -Quiet -ErrorAction SilentlyContinue)) { return @{ ok = $false; proc = $p; start_utc = $startUtc } }
    return @{ ok = $true; proc = $p; start_utc = $startUtc; ready_utc = $readyUtc; stdout = $o }
}
function CopyServerCsv($n) {
    $o = Join-Path $OutDir ("server{0:D2}_stdout.log" -f $n)
    $l = Select-String -Path $o -Pattern '^CSV log: (.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($l) { Copy-Item $l.Matches[0].Groups[1].Value (Join-Path $OutDir ("server{0:D2}_sensor.csv" -f $n)) -ErrorAction SilentlyContinue }
}
function Abort($why, $srvProc, $capProc) {
    Note @{ utc = Utc; event = 'ABORT'; reason = $why }
    if ($srvProc) { Stop-Process -Id $srvProc.Id -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType File -Force (Join-Path $OutDir 'serial_raw.stop') | Out-Null
    if ($capProc) { $capProc.WaitForExit(15000) | Out-Null }
    Write-Output "ABORT: $why"; exit 2
}

# ---- pre-checks (same as run_long.ps1)
$hs = 'unknown'; $band = 'unknown'
try {
    $cp = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    $tm = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($cp)
    $hs = $tm.TetheringOperationalState.ToString()
    $band = $tm.GetCurrentAccessPointConfiguration().Band.ToString()
} catch { $hs = 'query_failed: ' + $_.Exception.Message }
$bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$pre = [ordered]@{
    checked_utc = Utc; proto = $Proto; cycles = $Cycles; run_s = $RunSec; down_s = $DownSec; reconnect_timeout_s = $ReconnectTimeoutSec
    hotspot_state = $hs; hotspot_band = $band
    hotspot_ip_192_168_137_1 = [bool](Get-NetIPAddress -IPAddress 192.168.137.1 -ErrorAction SilentlyContinue)
    clumsy_or_windivert_processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'clumsy|windivert' }).Count
    serial_port = $Port
    com_present = [bool](Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match "\($Port\)" })
    com_serial_monitor_processes = @(Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -match "--port ${Port}\b|idf\.py.*-p ${Port}\b|esptool.*-p ${Port}\b" -or ($Port -eq 'COM6' -and $_.CommandLine -match 'capture_long' -and $_.CommandLine -notmatch '--port')) -and $_.ProcessId -ne $PID }).Count
    server_port_busy_before = [bool]$(if ($Proto -eq 'tcp_tls') { Get-NetTCPConnection -LocalPort $srvPort -State Listen -ErrorAction SilentlyContinue } else { Get-NetUDPEndpoint -LocalPort $srvPort -ErrorAction SilentlyContinue })
    laptop_on_ac = if ($bat) { $bat.BatteryStatus -eq 2 } else { $true }
    battery_percent = if ($bat) { $bat.EstimatedChargeRemaining } else { $null }
    sleep_after_ac = ((powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Select-String 'Current AC') -join ' ').Trim()
    disk_free_gb = [math]::Round((Get-PSDrive C).Free / 1GB)
    pktmon = $false
}
$pre | ConvertTo-Json | Set-Content -Path (Join-Path $OutDir 'prechecks.json') -Encoding utf8
$bad = @()
if ($hs -ne 'On' -or -not $pre.hotspot_ip_192_168_137_1) { $bad += 'hotspot not on' }
if ($pre.clumsy_or_windivert_processes -gt 0) { $bad += 'clumsy running' }
if (-not $pre.com_present) { $bad += "$Port missing" }
if ($pre.com_serial_monitor_processes -gt 0) { $bad += "serial monitor running on $Port" }
if ($pre.server_port_busy_before) { $bad += "port $srvPort already in use" }
if (-not $pre.laptop_on_ac) { $bad += 'not on AC' }
if ($bad) { Note @{ utc = Utc; event = 'PRECHECK_FAILED'; reasons = $bad }; Write-Output ('PRECHECK_FAILED: ' + ($bad -join ', ')); exit 2 }
Note @{ utc = Utc; event = 'PRECHECK_OK' }

# ---- server 0, watchdog, capture (one reset)
$s = StartServer 0
if (-not $s.ok) { Abort 'server 0 did not report READY' $s.proc $null }
Note @{ utc = Utc; event = 'SERVER_READY'; n = 0; pid = $s.proc.Id; start_utc = $s.start_utc; ready_utc = $s.ready_utc }
$estSec = 300 + $Cycles * ($RunSec + $DownSec + 120)
$watch = Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $prof 'hotspot_watch.ps1'),
    '-OutFile', (Join-Path $OutDir 'hotspot_watch.jsonl'), '-Seconds', ($estSec + 600) -WindowStyle Hidden -PassThru
Note @{ utc = Utc; event = 'WATCHDOG_STARTED'; pid = $watch.Id; seconds = $estSec + 600 }
$cap = Start-Process $idfPy -ArgumentList '-I', (Join-Path $prof 'capture_long.py'), (Join-Path $OutDir 'serial_raw'), '--seconds', ($estSec * 2), '--reset', '--port', $Port `
    -RedirectStandardOutput (Join-Path $OutDir 'capture_stdout.txt') -RedirectStandardError (Join-Path $OutDir 'capture_stderr.txt') -WindowStyle Hidden -PassThru
Note @{ utc = Utc; event = 'CAPTURE_START'; pid = $cap.Id }

$reconPat = ' RECONNECT n=\d+ session='
$deadline = (Get-Date).AddSeconds(150)
while ((Get-Date) -lt $deadline -and (CountLines ' CONNECT session=0 initial=1') -eq 0) { Start-Sleep -Milliseconds 250 }
if ((CountLines ' CONNECT session=0 initial=1') -eq 0) { Abort 'first connection (CONNECT session=0) not seen within 150 s' $s.proc $cap }
Note @{ utc = Utc; event = 'FIRST_CONNECT_SEEN' }
$consecutiveTimeouts = 0

for ($i = 1; $i -le $Cycles; $i++) {
    Start-Sleep -Seconds $RunSec
    $before = CountLines $reconPat
    $killUtc = Utc
    Stop-Process -Id $s.proc.Id -Force -ErrorAction SilentlyContinue
    Note @{ utc = Utc; event = 'SERVER_KILLED'; cycle = $i; kill_utc = $killUtc; reconnects_before = $before }
    CopyServerCsv ($i - 1)
    Start-Sleep -Seconds $DownSec
    $s = StartServer $i
    if (-not $s.ok) { Abort "server $i did not report READY" $s.proc $cap }
    Note @{ utc = Utc; event = 'SERVER_READY'; n = $i; cycle = $i; pid = $s.proc.Id; start_utc = $s.start_utc; ready_utc = $s.ready_utc }
    $deadline = (Get-Date).AddSeconds($ReconnectTimeoutSec)
    while ((Get-Date) -lt $deadline -and (CountLines $reconPat) -le $before) { Start-Sleep -Milliseconds 250 }
    if ((CountLines $reconPat) -gt $before) {
        $consecutiveTimeouts = 0
        Note @{ utc = Utc; event = 'RECONNECT_SEEN'; cycle = $i }
    } else {
        $consecutiveTimeouts++
        Note @{ utc = Utc; event = 'RECONNECT_TIMEOUT'; cycle = $i; timeout_s = $ReconnectTimeoutSec }
        if ($consecutiveTimeouts -ge 2) { Abort "no reconnect in two consecutive cycles (last cycle $i)" $s.proc $cap }
    }
}

# ---- end: let the last connection run RunSec, stop capture and server
Start-Sleep -Seconds $RunSec
New-Item -ItemType File -Force (Join-Path $OutDir 'serial_raw.stop') | Out-Null
$cap.WaitForExit(15000) | Out-Null
Stop-Process -Id $s.proc.Id -Force -ErrorAction SilentlyContinue
CopyServerCsv $Cycles
Stop-Process -Id $watch.Id -Force -ErrorAction SilentlyContinue
Note @{ utc = Utc; event = 'TEST_END'; cycles = $Cycles }
Write-Output 'TEST_END'; exit 0
