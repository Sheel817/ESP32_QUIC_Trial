# One user-approved hotspot restart (off, then on with the saved configuration via enable_existing_hotspot.ps1).
# Usage: powershell -File hotspot_restart.ps1 -OutFile <path.jsonl>. Records state, no SSID or passphrase.
param([string]$OutFile)
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial'
function Log($o) { ($o | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding utf8 }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$cp = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
$tm = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($cp)
Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'BEFORE'; state = $tm.TetheringOperationalState.ToString(); clients = $tm.ClientCount }
$op = $tm.StopTetheringAsync()
$m = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
$rt = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
$t = $m.MakeGenericMethod($rt).Invoke($null, @($op))
if (-not $t.Wait(30000)) { Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'STOP_TIMEOUT' }; throw 'stop timeout' }
Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'STOPPED'; status = $t.Result.Status.ToString(); state = $tm.TetheringOperationalState.ToString() }
Start-Sleep -Seconds 10
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'tools\run_recorder\enable_existing_hotspot.ps1') 2>&1 | Out-String
Start-Sleep -Seconds 5
Log @{ utc = [DateTime]::UtcNow.ToString('o'); event = 'AFTER'; enable_pass = ($out -match '"state":\s*"On"'); state = $tm.TetheringOperationalState.ToString();
       ip_192_168_137_1 = [bool](Get-NetIPAddress -IPAddress 192.168.137.1 -ErrorAction SilentlyContinue) }
