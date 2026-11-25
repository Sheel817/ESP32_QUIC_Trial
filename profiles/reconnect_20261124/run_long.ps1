# One long run of the RECONNECT profile (normal network, no Clumsy). The image must already be flashed.
# Usage: powershell -ExecutionPolicy Bypass -File run_long.ps1 -Proto tcp_tls|quic -OutDir <dir> -Seconds 43200 [-NoPktmon] [-Port COMx] [-NoWatchdog]
# Order: pre-checks -> server -> hotspot watchdog -> elevated pktmon (one UAC prompt) -> serial capture with one
# host reset at the start (blocks for -Seconds) -> stop server -> copy server CSV -> run_end.json.
param([ValidateSet('tcp_tls','quic')][string]$Proto, [string]$OutDir, [int]$Seconds = 43200, [switch]$NoPktmon,
      [string]$Port = 'COM6', [switch]$NoWatchdog)  # -NoWatchdog: second board while another run already watches the hotspot
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial'
$prof = Join-Path $root 'profiles\reconnect_20261124'
$idfPy = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe'
$srvPy = Join-Path $root '.quic-venv\Scripts\python.exe'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$srvPort = if ($Proto -eq 'tcp_tls') { 14568 } else { 14567 }
$server = if ($Proto -eq 'tcp_tls') { 'tcp_tls_server.py' } else { 'quic_server.py' }
function Note($o) { ($o | ConvertTo-Json -Compress) | Add-Content -Path (Join-Path $OutDir 'run_events.jsonl') -Encoding utf8 }

# ---- pre-checks
$tm = $null; $hs = 'unknown'; $band = 'unknown'
try {
    $cp = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    $tm = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($cp)
    $hs = $tm.TetheringOperationalState.ToString()
    $band = $tm.GetCurrentAccessPointConfiguration().Band.ToString()
} catch { $hs = 'query_failed: ' + $_.Exception.Message }
$bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$pre = [ordered]@{
    checked_utc = [DateTime]::UtcNow.ToString('o'); proto = $Proto; seconds = $Seconds
    hotspot_state = $hs; hotspot_band = $band
    hotspot_ip_192_168_137_1 = [bool](Get-NetIPAddress -IPAddress 192.168.137.1 -ErrorAction SilentlyContinue)
    clumsy_or_windivert_processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'clumsy|windivert' }).Count
    serial_port = $Port
    com_present = [bool](Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match "\($Port\)" })
    com_serial_monitor_processes = @(Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -match "--port ${Port}\b|idf\.py.*-p ${Port}\b" -or ($Port -eq 'COM6' -and $_.CommandLine -match 'capture_long' -and $_.CommandLine -notmatch '--port')) -and $_.ProcessId -ne $PID }).Count
    server_port_busy_before = [bool]$(if ($Proto -eq 'tcp_tls') { Get-NetTCPConnection -LocalPort $srvPort -State Listen -ErrorAction SilentlyContinue } else { Get-NetUDPEndpoint -LocalPort $srvPort -ErrorAction SilentlyContinue })
    laptop_on_ac = if ($bat) { $bat.BatteryStatus -eq 2 } else { $true }
    battery_percent = if ($bat) { $bat.EstimatedChargeRemaining } else { $null }
    sleep_after_ac = ((powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Select-String 'Current AC') -join ' ').Trim()
    hibernate_after_ac = ((powercfg /query SCHEME_CURRENT SUB_SLEEP HIBERNATEIDLE | Select-String 'Current AC') -join ' ').Trim()
    disk_free_gb = [math]::Round((Get-PSDrive C).Free / 1GB)
    pktmon = -not $NoPktmon
}
$pre | ConvertTo-Json | Set-Content -Path (Join-Path $OutDir 'prechecks.json') -Encoding utf8
$bad = @()
if ($hs -ne 'On' -or -not $pre.hotspot_ip_192_168_137_1) { $bad += 'hotspot not on' }
if ($pre.clumsy_or_windivert_processes -gt 0) { $bad += 'clumsy running' }
if (-not $pre.com_present) { $bad += "$Port missing" }
if ($pre.com_serial_monitor_processes -gt 0) { $bad += "serial monitor running on $Port" }
if ($pre.server_port_busy_before) { $bad += "port $srvPort already in use" }
if (-not $pre.laptop_on_ac) { $bad += 'not on AC' }
if ($bad) { Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'PRECHECK_FAILED'; reasons = $bad }; throw ('pre-check failed: ' + ($bad -join ', ')) }

# ---- server
$sOut = Join-Path $OutDir 'server_stdout.log'; $sErr = Join-Path $OutDir 'server_stderr.log'
$srv = Start-Process -FilePath $srvPy -ArgumentList '-u', $server -WorkingDirectory $root -RedirectStandardOutput $sOut -RedirectStandardError $sErr -WindowStyle Hidden -PassThru
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline -and -not (Select-String -Path $sOut -Pattern '^READY' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 500 }
if (-not (Select-String -Path $sOut -Pattern '^READY' -Quiet -ErrorAction SilentlyContinue)) { Stop-Process -Id $srv.Id -Force; throw 'server did not report READY' }
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'SERVER_READY'; pid = $srv.Id; server = $server }

# ---- hotspot watchdog (runs 10 min longer than the capture)
if (-not $NoWatchdog) {
$watch = Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $prof 'hotspot_watch.ps1'),
    '-OutFile', (Join-Path $OutDir 'hotspot_watch.jsonl'), '-Seconds', ($Seconds + 600) -WindowStyle Hidden -PassThru
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'WATCHDOG_STARTED'; pid = $watch.Id }
} else { Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'WATCHDOG_SKIPPED'; reason = 'other run watches the hotspot' } }

# ---- packet capture (elevated, one UAC prompt; stops itself 5 min after the capture end)
if (-not $NoPktmon) {
    $pk = Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $prof 'pktmon_run.ps1'),
        '-OutDir', "`"$OutDir`"", '-Seconds', ($Seconds + 300), '-Port', $srvPort -WindowStyle Hidden -PassThru
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and -not (Select-String -Path (Join-Path $OutDir 'pktmon_run.log') -Pattern '^\S+ start:' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep -Seconds 1 }
    $started = [bool](Select-String -Path (Join-Path $OutDir 'pktmon_run.log') -Pattern '^\S+ start:' -Quiet -ErrorAction SilentlyContinue)
    Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'PKTMON_STARTED'; ok = $started }
    if (-not $started) { Stop-Process -Id $srv.Id -Force; Stop-Process -Id $watch.Id -Force; throw 'pktmon did not start (UAC declined?)' }
}

# ---- serial capture (one reset at start, blocks for the run)
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'CAPTURE_START' }
& $idfPy -I (Join-Path $prof 'capture_long.py') (Join-Path $OutDir 'serial_raw') --seconds $Seconds --reset --port $Port > (Join-Path $OutDir 'capture_stdout.txt') 2> (Join-Path $OutDir 'capture_stderr.txt')
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'CAPTURE_END'; exit_code = $LASTEXITCODE }

# ---- stop server, copy its CSV
Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'SERVER_STOPPED' }
$csvLine = Select-String -Path $sOut -Pattern '^CSV log: (.+)$' | Select-Object -First 1
if ($csvLine) { Copy-Item $csvLine.Matches[0].Groups[1].Value (Join-Path $OutDir 'server_sensor.csv') }
Note @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'RUN_END'; server_csv = [bool]$csvLine }
