# Hotspot watchdog for long runs. Usage: powershell -File hotspot_watch.ps1 -OutFile <path.jsonl> -Seconds N
# Every 15 s: if tethering is not On or 192.168.137.1 is missing, record outage start, run the user-approved
# tools/run_recorder/enable_existing_hotspot.ps1 (saved configuration only), record restart time and outage length.
param([string]$OutFile, [int]$Seconds)
$root = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial'
$script = Join-Path $root 'tools\run_recorder\enable_existing_hotspot.ps1'
function Log($o) { ($o | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding utf8 }
function State {
    try {
        $cp = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
        $tm = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($cp)
        $on = ($tm.TetheringOperationalState.ToString() -eq 'On') -and [bool](Get-NetIPAddress -IPAddress 192.168.137.1 -ErrorAction SilentlyContinue)
        return @{ on = $on; clients = $tm.ClientCount; state = $tm.TetheringOperationalState.ToString() }
    } catch { return @{ on = $false; clients = -1; state = 'query_failed: ' + $_.Exception.Message } }
}
$end = (Get-Date).AddSeconds($Seconds); $outageStart = $null
Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'WATCH_START'; seconds = $Seconds }
while ((Get-Date) -lt $end) {
    $s = State
    if (-not $s.on) {
        if (-not $outageStart) { $outageStart = [DateTime]::UtcNow; Log @{ utc = $outageStart.ToString('o'); event = 'HOTSPOT_DOWN'; state = $s.state } }
        try { & powershell -NoProfile -ExecutionPolicy Bypass -File $script *> $null } catch {}
        Start-Sleep -Seconds 5
        $s2 = State
        Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'RESTART_ATTEMPT'; hotspot_on_after = $s2.on }
        if ($s2.on) {
            $n = [DateTime]::UtcNow
            Log @{ utc = $n.ToString('o'); event = 'HOTSPOT_RESTORED'; outage_seconds = [math]::Round(($n - $outageStart).TotalSeconds, 1) }
            $outageStart = $null
        }
    } elseif ($outageStart) {
        $n = [DateTime]::UtcNow
        Log @{ utc = $n.ToString('o'); event = 'HOTSPOT_RESTORED_EXTERNALLY'; outage_seconds = [math]::Round(($n - $outageStart).TotalSeconds, 1) }
        $outageStart = $null
    }
    Start-Sleep -Seconds 15
}
Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'WATCH_END' }
