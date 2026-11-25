# Unattended chain for RECONNECT_TEST: wait for the 8 h QUIC run to end, flash fq3v4 on COM6, 20 QUIC cycles,
# flash ft3v4 on COM6, 20 TCP+TLS cycles, analyze both. Stops at the first failure (pre-check, flash, abort).
# Usage: powershell -ExecutionPolicy Bypass -File reconnect_test_chain.ps1 -OutRoot <results dir> -WaitRunDir <8 h run dir>
param([string]$OutRoot, [string]$WaitRunDir, [string]$Port = 'COM6')
$ErrorActionPreference = 'Continue'  # exit codes are checked explicitly (PS 5.1 turns native stderr into errors)
$prof = 'C:\Users\newsh\Desktop\ESP32_QUIC_Trial\profiles\reconnect_20261124'
$idfPy = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe'
New-Item -ItemType Directory -Force $OutRoot | Out-Null
$OutRoot = (Resolve-Path $OutRoot).Path
$log = Join-Path $OutRoot 'chain.log'
function L($m) { "$([DateTime]::UtcNow.ToString('o')) $m" | Add-Content $log -Encoding utf8; Write-Output $m }
function Stop-Chain($m) { L "CHAIN_STOPPED $m"; exit 2 }

# 1. wait for the 8 h run (RUN_END) plus 60 s so the capture has released the port
L "WAIT_FOR_8H_RUN $WaitRunDir"
$ev = Join-Path $WaitRunDir 'run_events.jsonl'
$deadline = (Get-Date).AddHours(3)
while ((Get-Date) -lt $deadline -and -not (Select-String -Path $ev -Pattern 'RUN_END' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep -Seconds 20 }
if (-not (Select-String -Path $ev -Pattern 'RUN_END' -Quiet -ErrorAction SilentlyContinue)) { Stop-Chain '8 h run did not report RUN_END within 3 h' }
L '8H_RUN_ENDED'; Start-Sleep -Seconds 60

function Flash($tag, $expectSha) {
    $bin = Join-Path $prof "build_$tag\quic_demo.bin"
    $sha = (Get-FileHash $bin -Algorithm SHA256).Hash.ToLower()
    if ($sha -ne $expectSha) { Stop-Chain "$tag image hash mismatch $sha" }
    $flog = Join-Path $OutRoot "flash_${tag}_com6.log"
    L "FLASH $tag sha256=$sha"
    Push-Location (Join-Path $prof "build_$tag")
    "esptool --chip esp32c6 -p $Port -b 460800 --before default-reset --after no-reset write-flash --flash-mode dio --flash-freq 80m --flash-size 8MB 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 quic_demo.bin" | Set-Content $flog -Encoding utf8
    & $idfPy -m esptool --chip esp32c6 -p $Port -b 460800 --before default-reset --after no-reset write-flash --flash-mode dio --flash-freq 80m --flash-size 8MB `
        0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 quic_demo.bin 2>&1 | ForEach-Object { "$_" } | Add-Content $flog -Encoding utf8
    $frc = $LASTEXITCODE
    Pop-Location
    if ($frc -ne 0 -or -not (Select-String -Path $flog -Pattern 'Hash of data verified' -Quiet)) { Stop-Chain "flash $tag failed exit=$frc" }
    L "FLASH_OK $tag"; Start-Sleep -Seconds 5
}
function Cycles($proto, $label) {
    L "CYCLES_START $proto"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $prof 'reconnect_cycles.ps1') -Proto $proto -OutDir (Join-Path $OutRoot $proto) -Port $Port *>> (Join-Path $OutRoot "${proto}_runner.txt")
    $rc = $LASTEXITCODE; L "CYCLES_END $proto exit=$rc"
    & $idfPy -I (Join-Path $prof 'analyze_cycles.py') (Join-Path $OutRoot $proto) $label *>> (Join-Path $OutRoot "${proto}_analysis.txt")
    if ($rc -ne 0) { Stop-Chain "$proto cycles exit $rc" }
}
# IPv4-only images (deviation: CONFIG_EXAMPLE_CONNECT_IPV6=n), QUIC first, then TCP+TLS, same board COM6
Flash 'fq3v4' '318e51412fbef3aec9071ae7596e793e867944e67723b0e855cb3ab7bfc13d0e'
Cycles 'quic' 'QUIC (fq3v4, IPv4-only start-up)'
Flash 'ft3v4' 'cc8332a5b3aced6b9c41d102a32fa29e54b2fd5484c5a34029733baa2a19114d'
Cycles 'tcp_tls' 'TCP+TLS (ft3v4, IPv4-only start-up)'
L 'CHAIN_DONE'; exit 0
