"""Derive reference records from the live ESP-IDF log, then run 30 pings."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import time
import zipfile

folder = Path(__file__).resolve().parent
root = folder.parents[2]
checkpoint = Path('C:/Users/newsh/Desktop/ESP32_QUIC_Checkpoints/pre_wifi_ps_none_20261103T162643Z')
condition = 'HOME_BOARD; original/default-power-saving firmware; Clumsy stopped'
def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(name, rows):
    with (folder / name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

manifest = json.loads((checkpoint / 'original_build_hashes.json').read_text())
elf_hash = sha(root / 'build/quic_demo.elf')
bin_hash = sha(root / 'build/quic_demo.bin')
assert elf_hash == manifest['quic_demo.elf']
assert bin_hash == manifest['quic_demo.bin']
log_path = folder / 'HOME_BOARD_PS_DEFAULT_serial.log'
deadline = time.monotonic() + 240
while True:
    raw = log_path.read_text(encoding='utf-8', errors='replace')
    startup = raw.split("--- Command: 'reset'", 1)[1]
    digest = re.search(r'ELF file SHA256:\s*([0-9a-f]+)', startup)
    if digest:
        assert elf_hash.startswith(digest[1]), 'Firmware ELF digest mismatch: abort before collection'
    ip_match = re.search(r'example_netif_sta ip: (\d+\.\d+\.\d+\.\d+)', startup)
    matches = list(re.finditer(r'(?m)^(\S+) I \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+).*$', startup))
    selected = [m for m in matches if int(m[2]) >= 60000][:10]
    if len(selected) == 10:
        assert digest and ip_match and 'Starting ESP32-C6 DHT11 over QUIC' in startup
        break
    if time.monotonic() > deadline:
        raise RuntimeError(f'Only {len(selected)} qualifying APP_RTT records; no ping started')
    time.sleep(0.5)

ip = ip_match[1]
rows = []
for n, m in enumerate(selected, 1):
    host = dt.datetime.fromisoformat(m[1]).replace(tzinfo=dt.timezone(dt.timedelta(hours=2)))
    rows.append(dict(sample=n,host_received_local=m[1]+'+02:00',host_received_utc=host.astimezone(dt.timezone.utc).isoformat(),esp_log_uptime_ms=int(m[2]),seq=int(m[3]),app_rtt_ms=m[4],condition=condition,source_log=log_path.name,raw_line=m[0]))
write_csv('HOME_BOARD_PS_DEFAULT_APP_RTT_20261103T225407Z.csv', rows)
(folder / 'HOME_BOARD_PS_DEFAULT_serial_through_collection.log').write_text(raw, encoding='utf-8')
collection_complete = utc()
ping_start = utc()
ping_command = ['ping.exe', '-n', '30', '-w', '1000', ip]
ping_rows = []
ping_lines = []
with (folder / 'HOME_BOARD_PS_DEFAULT_ping_raw.txt').open('w', encoding='utf-8') as out:
    proc = subprocess.Popen(ping_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        received = utc()
        line = line.rstrip('\n')
        out.write(line+'\n')
        out.flush()
        ping_lines.append(dict(received_utc=received,raw_line=line))
        reply = re.search(r'Reply from ([\d.]+): bytes=\d+ time([=<])(\d+)ms TTL=(\d+)', line)
        if reply or 'timed out' in line or 'unreachable' in line:
            ping_rows.append(dict(request_number=len(ping_rows)+1,received_utc=received,ip=ip,status='reply' if reply else ('timeout' if 'timed out' in line else 'unreachable'),rtt_reported_ms=(('<' if reply[2]=='<' else '')+reply[3]) if reply else '',rtt_exact_ms=reply[3] if reply and reply[2]=='=' else '',condition=condition,raw_line=line))
    proc.wait()
ping_end = utc()
assert len(ping_rows) == 30, f'Unexpected ping result count: {len(ping_rows)}'
write_csv('HOME_BOARD_PS_DEFAULT_ping_20261103T225407Z.csv', ping_rows)
write_csv('HOME_BOARD_PS_DEFAULT_ping_output_timestamped.csv', ping_lines)
values = [float(r['app_rtt_ms']) for r in rows]
replies = [r for r in ping_rows if r['status']=='reply']
exact = [float(r['rtt_exact_ms']) for r in replies if r['rtt_exact_ms']!='']
less = [r for r in replies if r['rtt_reported_ms']=='<1']
result = dict(condition=condition,assigned_ip=ip,elf_sha256=elf_hash,bin_sha256=bin_hash,reported_elf_digest_prefix=digest[1],digest_comparison='Reported prefix matches; full on-board digest not printed. Local ELF/bin full hashes match preserved checkpoint.',collection_complete_utc=collection_complete,ping_start_utc=ping_start,ping_end_utc=ping_end,ping_command=ping_command,app_rtt_ms=values,app_mean_ms=statistics.mean(values),app_min_ms=min(values),app_max_ms=max(values),ping_replies=len(replies),ping_timeouts=sum(r['status']=='timeout' for r in ping_rows),ping_other_failures=sum(r['status']=='unreachable' for r in ping_rows),ping_less_than_1_ms=len(less),ping_integer_rtt_min_ms=min(exact) if exact else None,ping_integer_rtt_max_ms=max(exact) if exact else None,ping_integer_rtt_mean_ms=statistics.mean(exact) if exact else None,ping_windows_summary='\n'.join(x['raw_line'] for x in ping_lines[-6:]),power_evidence=[line for line in startup.splitlines() if 'pm start' in line or 'beacon interval' in line or 'wifi:dp:' in line])
if less:
    result['ping_all_reply_mean_bounds_ms'] = [sum(exact)/len(replies),(sum(exact)+len(less))/len(replies)]
(folder / 'HOME_BOARD_PS_DEFAULT_statistics.json').write_text(json.dumps(result, indent=2))

references = []
with zipfile.ZipFile(checkpoint / 'tested_source_config_and_QUIC_artifacts.zip') as archive:
    for requested in ['main/quic_demo_main.c','main/CMakeLists.txt']:
        names = [n for n in archive.namelist() if n.replace('\\','/') == requested]
        if not names:
            names = [n for n in archive.namelist() if n.replace('\\','/').endswith('/'+requested)]
        assert len(names)==1, names
        content = archive.read(names[0])
        dest = folder / ('preserved_original_'+Path(requested).name+'.txt')
        dest.write_bytes(content)
        references.append(dict(source=str(checkpoint / 'tested_source_config_and_QUIC_artifacts.zip')+'::'+names[0],snapshot=dest.name,sha256=hashlib.sha256(content).hexdigest()))
for path in [root/'build/CMakeCache.txt', root/'build/compile_commands.json',Path('C:/esp/v6.1/esp-idf/components/esp_wifi/include/esp_wifi.h'),Path('C:/esp/v6.1/esp-idf/components/esp_wifi/include/esp_wifi_types_generic.h')]:
    references.append(dict(source=str(path),sha256=sha(path)))
(folder/'source_references.json').write_text(json.dumps(references,indent=2))
print(json.dumps(result,indent=2), flush=True)
