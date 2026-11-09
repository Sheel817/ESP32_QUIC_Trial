param([string]$OutDir)
$ErrorActionPreference='Stop'
$project='C:\Users\newsh\Desktop\ESP32_QUIC_Trial'
$etl=Join-Path $OutDir 'university_quic.etl'
$transcript=Join-Path $OutDir 'commands_and_output.txt'
Start-Transcript -LiteralPath $transcript | Out-Null
$owned=$false
$filterAdded=$false
function Boundaries {
 $paths=@('logs\UNIVERSITY_BOARD_20261103T170943_serial.log','logs\quic_server_start_20261103T163259.stdout.log','logs\sensor_20261103T143300_220342Z_c7ett8c2.csv')
 $result=@()
 foreach($relative in $paths) { $p=Join-Path $project $relative; $f=Get-Item -LiteralPath $p; $result+=@{path=$p;byte_length=$f.Length;measured_utc=[DateTime]::UtcNow.ToString('o');tail=@(Get-Content -LiteralPath $p -Tail 3)} }
 return $result
}
try {
 $status=(& pktmon status 2>&1 | Out-String); $status | Out-File (Join-Path $OutDir 'status_recheck.txt'); if($LASTEXITCODE -ne 0 -or $status -notmatch 'Packet Monitor is not running') { throw 'Capture already active or status uncertain; no changes made.' }
 $filters=(& pktmon filter list 2>&1 | Out-String); if($LASTEXITCODE -ne 0 -or $filters -notmatch 'None') { throw 'Existing filters found; leaving unchanged.' }
 foreach($args in @(@('start','help'),@('filter','add','help'),@('etl2txt','help'),@('etl2pcap','help'))) { Write-Host ('COMMAND: pktmon '+($args -join ' ')); & pktmon @args }
 Write-Host 'COMMAND: pktmon filter add UNIVERSITY_QUIC_154643 -t UDP -i 192.168.137.11 -p 14567'
 & pktmon filter add UNIVERSITY_QUIC_154643 -t UDP -i 192.168.137.11 -p 14567
 if($LASTEXITCODE -ne 0) { throw 'Filter creation failed' }; $filterAdded=$true
 $ourFilters=(& pktmon filter list | Out-String); $ourFilters | Out-File (Join-Path $OutDir 'filters_capture.txt')
 $pre=Boundaries; $invokeUtc=[DateTime]::UtcNow.ToString('o')
 Write-Host "COMMAND: pktmon start --capture --comp all --pkt-size 0 --file-name $etl --file-size 64 --log-mode circular"
 & pktmon start --capture --comp all --pkt-size 0 --file-name $etl --file-size 64 --log-mode circular
 if($LASTEXITCODE -ne 0) { throw 'Capture start failed' }; $owned=$true
 $started=[DateTime]::UtcNow.ToString('o'); & pktmon status | Out-File (Join-Path $OutDir 'status_during.txt')
 @{invoke_start_utc=$invokeUtc;start_command_completed_utc=$started;boundaries_before=$pre;duration_requested_seconds=60;board_ip='192.168.137.11';board_base_mac='98:a3:16:7e:55:50';condition='Lag OFF, capture running, all effects disabled - operator-reported; not independently changed or verified'} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $OutDir 'capture_start.json')
 Start-Sleep -Seconds 60
 $stopInvoke=[DateTime]::UtcNow.ToString('o');Write-Host 'COMMAND: pktmon stop (only session started by this script)'; & pktmon stop; if($LASTEXITCODE -ne 0){throw 'Capture stop failed'}; $owned=$false
 $stopped=[DateTime]::UtcNow.ToString('o');$post=Boundaries
 @{stop_invoked_utc=$stopInvoke;stop_command_completed_utc=$stopped;boundaries_after=$post} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $OutDir 'capture_end.json')
 & pktmon list --json | Out-File (Join-Path $OutDir 'components_after.json')
 & pktmon etl2txt $etl --out (Join-Path $OutDir 'university_quic.txt') --timestamp --verbose
 & pktmon etl2pcap $etl --out (Join-Path $OutDir 'university_quic.pcapng')
 & pktmon etl2txt $etl --stats | Out-File (Join-Path $OutDir 'etl_statistics.txt')
 & pktmon status | Out-File (Join-Path $OutDir 'status_after.txt')
} catch { $_ | Out-String | Set-Content (Join-Path $OutDir 'error.txt') }
finally {
 if($owned) { & pktmon stop }
 if($filterAdded) { $nowFilters=(& pktmon filter list | Out-String); if($nowFilters -eq $ourFilters) { & pktmon filter remove } else { 'Filters changed concurrently; not removing' | Set-Content (Join-Path $OutDir 'filter_cleanup_note.txt') } }
 Stop-Transcript | Out-Null
 'DONE' | Set-Content (Join-Path $OutDir 'completed.txt')
}
