# Elevated packet capture for one long run (must run as administrator; started once by run_long.ps1 via UAC).
# Usage: powershell -File pktmon_run.ps1 -OutDir <dir> -Seconds N -Port <14568|14567>
# Captures only: the MQTT server port (TCP 14568 or UDP 14567), ARP and ICMP, on all NICs (the hotspot
# virtual adapter included), full packet size, circular file 2 GB. Stops itself after N seconds (or when
# <OutDir>\pktmon.stop exists) and converts the ETL file to pcapng. All steps are logged to pktmon_run.log.
param([string]$OutDir, [int]$Seconds, [int]$Port)
$log = Join-Path $OutDir 'pktmon_run.log'
function L($m) { "$([DateTime]::UtcNow.ToString('o')) $m" | Add-Content -Path $log -Encoding utf8 }
$etl = Join-Path $OutDir 'pktmon.etl'
$stop = Join-Path $OutDir 'pktmon.stop'
L "PKTMON_RUN start seconds=$Seconds port=$Port"
L ("filter remove: " + (pktmon filter remove 2>&1 | Out-String).Trim())
L ("filter add port: " + (pktmon filter add MQTT_PORT -p $Port 2>&1 | Out-String).Trim())
L ("filter add arp: " + (pktmon filter add ARP -d ARP 2>&1 | Out-String).Trim())
L ("filter add icmp: " + (pktmon filter add ICMP -t ICMP 2>&1 | Out-String).Trim())
L ("filter list: " + (pktmon filter list 2>&1 | Out-String).Trim())
L ("start: " + (pktmon start --capture --comp nics --pkt-size 0 --file-name $etl --file-size 2048 --log-mode circular 2>&1 | Out-String).Trim())
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end -and -not (Test-Path $stop)) { Start-Sleep -Seconds 10 }
L ("stop: " + (pktmon stop 2>&1 | Out-String).Trim())
L ("etl2pcap: " + (pktmon etl2pcap $etl --out (Join-Path $OutDir 'pktmon.pcapng') 2>&1 | Out-String).Trim())
L ("filter remove: " + (pktmon filter remove 2>&1 | Out-String).Trim())
L "PKTMON_RUN end"
