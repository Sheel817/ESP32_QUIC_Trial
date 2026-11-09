"""Capture 10 post-warmup APP_RTT records, then 30 sequential Windows pings."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import time

folder = Path(__file__).resolve().parent
root = folder.parents[2]
build = root/'profiles/wifi_ps_none_20261103/build'
reference = root/'results/pilots/HOME_BOARD_PS_DEFAULT_20261103T225407Z'
condition = 'HOME_BOARD experimental WIFI_PS_NONE firmware; Clumsy stopped'
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_csv(name, rows):
    with (folder/name).open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

audit = json.loads((folder/'preflash_audit.json').read_text())
flash = json.loads((folder/'flash_result.json').read_text(encoding='utf-8-sig'))
flash_text = (folder/'HOME_BOARD_WIFI_PS_NONE_flash.log').read_text(encoding='utf-16')
assert flash['exit_code']==0 and flash_text.count('Hash of data verified.')==3
assert sha(build/'quic_demo.bin') == audit['artifacts']['quic_demo.bin']['sha256']
elf_hash = sha(build/'quic_demo.elf')
log_path = folder/'HOME_BOARD_WIFI_PS_NONE_serial.log'
deadline = time.monotonic()+240
gates_recorded = False
while True:
    raw = log_path.read_text(encoding='utf-8',errors='replace')
    startup = raw.split("--- Command: 'reset'",1)[1]
    digest = re.search(r'ELF file SHA256:\s*([0-9a-f]+)',startup)
    if digest:
        assert elf_hash.startswith(digest[1]), 'Unexpected firmware digest; abort'
    mode = 'requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)'
    ip_match = re.search(r'example_netif_sta ip: (\d+\.\d+\.\d+\.\d+)',startup)
    gates = digest and ip_match and mode in startup and 'MQTT connected over QUIC' in startup and 'QUIC connection established' in startup
    assert startup.count('ESP-ROM:esp32c6')<=1, 'Unexpected reboot during collection'
    if gates and not gates_recorded:
        (folder/'startup_checks.json').write_text(json.dumps(dict(checked_utc=utc(),condition=condition,flash_verification='3/3 artifact hashes verified, exit 0',elf_sha256=elf_hash,reported_digest_prefix=digest[1],requested_and_returned='WIFI_PS_NONE(0)',quic_connected=True,mqtt_connected=True,assigned_ip=ip_match[1],raw_startup_log=log_path.name),indent=2))
        gates_recorded = True
    matches = list(re.finditer(r'(?m)^(\S+) I \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+).*$',startup))
    selected = [m for m in matches if int(m[2])>=60000][:10]
    if gates and len(selected)==10:
        break
    if time.monotonic()>deadline:
        raise RuntimeError('Startup checks or 10 APP_RTT records unavailable; no pings started')
    time.sleep(0.5)

rows=[]
for n,m in enumerate(selected,1):
    host=dt.datetime.fromisoformat(m[1]).replace(tzinfo=dt.timezone(dt.timedelta(hours=2)))
    rows.append(dict(sample=n,host_received_local=host.isoformat(),host_received_utc=host.astimezone(dt.timezone.utc).isoformat(),esp_log_uptime_ms=int(m[2]),seq=int(m[3]),app_rtt_ms=m[4],condition=condition,source_log=log_path.name,raw_line=m[0]))
write_csv('HOME_BOARD_WIFI_PS_NONE_APP_RTT_20261103T230410Z.csv',rows)
(folder/'HOME_BOARD_WIFI_PS_NONE_serial_through_collection.log').write_text(raw,encoding='utf-8')
collection_complete=utc()
ip=ip_match[1]
ping_command=['ping.exe','-n','30','-w','1000',ip]
ping_start=utc()
ping_rows=[]
ping_lines=[]
with (folder/'HOME_BOARD_WIFI_PS_NONE_ping_raw.txt').open('w',encoding='utf-8') as out:
    proc=subprocess.Popen(ping_command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for line in proc.stdout:
        received=utc()
        line=line.rstrip('\n')
        out.write(line+'\n')
        out.flush()
        ping_lines.append(dict(received_utc=received,raw_line=line))
        reply=re.search(r'Reply from ([\d.]+): bytes=\d+ time([=<])(\d+)ms TTL=(\d+)',line)
        if reply or 'timed out' in line or 'unreachable' in line:
            ping_rows.append(dict(request_number=len(ping_rows)+1,received_utc=received,ip=ip,status='reply' if reply else ('timeout' if 'timed out' in line else 'unreachable'),rtt_reported_ms=(('<' if reply[2]=='<' else '')+reply[3]) if reply else '',rtt_exact_ms=reply[3] if reply and reply[2]=='=' else '',condition=condition,raw_line=line))
    proc.wait()
ping_end=utc()
assert len(ping_rows)==30, f'Unexpected ping count {len(ping_rows)}'
write_csv('HOME_BOARD_WIFI_PS_NONE_ping_20261103T230410Z.csv',ping_rows)
write_csv('HOME_BOARD_WIFI_PS_NONE_ping_output_timestamped.csv',ping_lines)
values=[float(r['app_rtt_ms']) for r in rows]
replies=[r for r in ping_rows if r['status']=='reply']
exact=[float(r['rtt_exact_ms']) for r in replies if r['rtt_exact_ms']!='']
less=[r for r in replies if r['rtt_reported_ms']=='<1']
base=json.loads((reference/'HOME_BOARD_PS_DEFAULT_statistics.json').read_text())
assert base['app_mean_ms']==75.4349
assert round(base['ping_integer_rtt_mean_ms'],4)==268.8667
stats=dict(condition=condition,assigned_ip=ip,collection_complete_utc=collection_complete,ping_start_utc=ping_start,ping_end_utc=ping_end,ping_command=ping_command,app_rtt_ms=values,app_mean_ms=statistics.mean(values),app_min_ms=min(values),app_max_ms=max(values),ping_replies=len(replies),ping_timeouts=sum(r['status']=='timeout' for r in ping_rows),ping_other_failures=sum(r['status']=='unreachable' for r in ping_rows),ping_less_than_1_ms=len(less),ping_reported_integer_min_ms=min(exact) if exact else None,ping_reported_integer_max_ms=max(exact) if exact else None,ping_reported_integer_mean_ms=statistics.mean(exact) if exact else None,ping_windows_summary='\n'.join(x['raw_line'] for x in ping_lines[-6:]),reference=str(reference),reference_app_mean_ms=base['app_mean_ms'],reference_ping_mean_ms=base['ping_integer_rtt_mean_ms'])
stats['app_mean_change_ms']=stats['app_mean_ms']-base['app_mean_ms']
stats['app_mean_reduction_percent']=100*(base['app_mean_ms']-stats['app_mean_ms'])/base['app_mean_ms']
if less:
    stats['ping_all_reply_mean_bounds_ms']=[sum(exact)/len(replies),(sum(exact)+len(less))/len(replies)]
else:
    stats['ping_mean_change_ms']=stats['ping_reported_integer_mean_ms']-base['ping_integer_rtt_mean_ms']
    stats['ping_mean_reduction_percent']=100*(base['ping_integer_rtt_mean_ms']-stats['ping_reported_integer_mean_ms'])/base['ping_integer_rtt_mean_ms']
(folder/'HOME_BOARD_WIFI_PS_NONE_statistics.json').write_text(json.dumps(stats,indent=2))
comparison=[dict(metric='APP_RTT',reference_mean_ms=base['app_mean_ms'],experiment_mean_ms=stats['app_mean_ms'],experiment_mean_lower_bound_ms='',experiment_mean_upper_bound_exclusive_ms='',condition=condition)]
comparison.append(dict(metric='ICMP ping',reference_mean_ms=base['ping_integer_rtt_mean_ms'],experiment_mean_ms=stats['ping_reported_integer_mean_ms'] if not less else '',experiment_mean_lower_bound_ms=stats['ping_all_reply_mean_bounds_ms'][0] if less else '',experiment_mean_upper_bound_exclusive_ms=stats['ping_all_reply_mean_bounds_ms'][1] if less else '',condition=condition))
write_csv('HOME_BOARD_default_vs_WIFI_PS_NONE_comparison.csv',comparison)
print(json.dumps(stats,indent=2),flush=True)
