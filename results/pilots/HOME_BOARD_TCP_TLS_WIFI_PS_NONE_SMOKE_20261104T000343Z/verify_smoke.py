"""Verify the measured TCP_TLS startup and first five sequence-matched echoes."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics
import time

folder=Path(__file__).resolve().parent
root=folder.parents[2]
profile=root/'profiles/tcp_tls_wifi_ps_none_20261104'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write_csv(name,rows):
    with (folder/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
flash=json.loads((folder/'flash_result.json').read_text(encoding='utf-8-sig'))
assert flash['exit_code']==0
flash_text=(folder/'HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_flash.log').read_text(encoding='utf-16')
assert flash_text.count('Hash of data verified.')==3
validation=json.loads((profile/'validation.json').read_text())
for entry in validation['artifacts'].values():assert sha(Path(entry['path']))==entry['sha256']
assert validation['artifacts']['quic_demo.bin']['sha256']=='ff97eb5d20c9c47375539395f9cf23c1d0780381562cf511094d4b525ab17de8'
session=json.loads((folder/'monitor_session.json').read_text())
reset=dt.datetime.fromisoformat(session['controlled_reset_requested_utc'])
server=json.loads((folder/'server_session.json').read_text(encoding='utf-8-sig'))
sensor_path=Path(server['sensor_csv'])
serial_path=folder/'HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_serial.log'
deadline=time.monotonic()+100
while True:
    raw=serial_path.read_text(encoding='utf-8',errors='replace')
    startup=raw.split("--- Command: 'reset'",1)[1]
    matches=list(re.finditer(r'(?m)^(\S+) I \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+).*$',startup))[:5]
    with sensor_path.open(encoding='utf-8',newline='') as f:sensors=list(csv.DictReader(f))
    eligible_sensors=[r for r in sensors if dt.datetime.fromisoformat(r['server_receive_utc'].replace('Z','+00:00'))>=reset]
    selected=[]
    for m in matches:
        options=[r for r in eligible_sensors if int(r['seq'])==int(m[3]) and r['client_id']=='esp32_quic_client' and r['topic']=='esp32/quic/test']
        if len(options)==1:selected.append(options[0])
    if len(matches)==5 and len(selected)==5:break
    if time.monotonic()>deadline:raise RuntimeError('Startup/echo/sensor evidence incomplete')
    time.sleep(0.25)
assert [int(m[3]) for m in matches]==[1,2,3,4,5]
digest=re.search(r'ELF file SHA256:\s*([a-f0-9]+)',startup)[1]
assert validation['artifacts']['quic_demo.elf']['sha256'].startswith(digest)
ip=re.search(r'example_netif_sta ip: ([\d.]+)',startup)[1]
assert 'Starting ESP32-C6 DHT11 over TCP_TLS' in startup
assert 'requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)' in startup
assert 'TCP_NODELAY=1;' in startup
assert 'TCP_TLS connection established' in startup and 'MQTT connected over TCP_TLS' in startup and 'Subscription acknowledged' in startup
tls_line=next(line for line in startup.splitlines() if 'TCP_TLS negotiated TLS=' in line)
for required in ('TLS=TLSv1.3','cipher=TLS_AES_128_GCM_SHA256','suite=0x1301','ALPN=mqtt','certificate_verification=NONE (mode=0)'):assert required in tls_line
end=matches[-1].end()
startup_interval=startup[:end]
errors=[line for line in startup_interval.splitlines() if re.search(r'(?i)(\bE \(\d+\)|disconnect|connection.*(?:fail|error|lost)|handshake.*(?:fail|error)|APP_RTT (?:ignored|storage full)|panic|abort\()',line)]
assert startup_interval.count('ESP-ROM:esp32c6')<=1
rows=[]
for match,sensor in zip(matches,selected):
    assert sensor['sensor']=='DHT11' and sensor['sensor_error']=='0'
    assert sensor['temperature_c'] and sensor['humidity_pct']
    assert int(sensor['uptime_ms'])<=int(match[2])
    local=dt.datetime.fromisoformat(match[1]).replace(tzinfo=dt.timezone(dt.timedelta(hours=2)))
    rows.append(dict(seq=int(match[3]),esp_log_uptime_ms=int(match[2]),app_rtt_ms=match[4],host_receipt_utc=local.astimezone(dt.timezone.utc).isoformat(),server_receive_utc=sensor['server_receive_utc'],payload_uptime_ms=sensor['uptime_ms'],sensor=sensor['sensor'],temperature_c=sensor['temperature_c'],humidity_pct=sensor['humidity_pct'],sensor_error=sensor['sensor_error'],client_id=sensor['client_id'],topic=sensor['topic'],label='HOME_BOARD TCP_TLS WIFI_PS_NONE SMOKE; startup verification only; not a formal run'))
write_csv('first_five_echoes_and_sensors.csv',rows)
write_csv('matching_server_sensor_records.csv',selected)
(folder/'serial_startup_through_first_five.log').write_text(raw.split("--- Command: 'reset'",1)[0]+"--- Command: 'reset'"+startup_interval+'\n',encoding='utf-8')
(folder/'tcp_tls_server_stdout_snapshot.log').write_bytes((folder/'tcp_tls_server.stdout.log').read_bytes())
(folder/'tcp_tls_server_stderr_snapshot.log').write_bytes((folder/'tcp_tls_server.stderr.log').read_bytes())
preserved=json.loads((folder/'preserved_before.json').read_text(encoding='utf-8-sig'))
for entry in preserved:assert sha(Path(entry['Path']))==entry['Hash'].lower()
inventory=json.loads((profile/'preservation_before.json').read_text())
counts={}
for kind,base in [('original_build',root/'build'),('quic_profile',root/'profiles/wifi_ps_none_20261103')]:
    for name,digest_expected in inventory[kind].items():assert sha(base/name)==digest_expected
    counts[kind]=len(inventory[kind])
register_path=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/run_register.csv'
with register_path.open(encoding='utf-8',newline='') as f:register=list(csv.DictReader(f))
assert len(register)==18 and all(r['status']=='NOT_RUN' for r in register)
first=register[0]
values=[float(r['app_rtt_ms']) for r in rows]
server_error_lines=[line for line in (folder/'tcp_tls_server.stderr.log').read_text(encoding='utf-8',errors='replace').splitlines() if 'ERROR' in line]
result=dict(status='PASS' if not errors else 'PASS_WITH_LOGGED_ERRORS',test='Startup smoke verification only; not a formal experiment',completed_utc=utc(),profile=str(profile),image_sha256=validation['artifacts']['quic_demo.bin']['sha256'],elf_sha256=validation['artifacts']['quic_demo.elf']['sha256'],reported_elf_prefix=digest,flash_verification='PASS, 3 artifact hashes verified, exit 0',controlled_reset_requested_utc=session['controlled_reset_requested_utc'],wifi_ps_requested='WIFI_PS_NONE(0)',wifi_ps_returned='WIFI_PS_NONE(0)',assigned_ip=ip,transport='TCP_TLS',tcp_nodelay=1,tls_line=tls_line,mqtt_connected=True,subscription_acknowledged=True,first_five=rows,echo_mean_ms=statistics.mean(values),matching_sensor_records=5,sensor_errors=0,connection_errors=errors,sequence_gaps=[],server_sensor_source=str(sensor_path),preserved_quic_inventory_files=counts,formal_register_unchanged=True,formal_run_count=18,formal_all_not_run=True,first_registered_run={k:first[k] for k in ('run_id','transport','condition')})
result['server_stderr_error_lines']=server_error_lines
result['server_error_attribution']='Server stderr has no timestamps or connection IDs; bare error cannot be attributed to controlled boot versus separate setup/probe connection.' if server_error_lines else 'No server error lines observed'
if server_error_lines and not errors:result['status']='PASS_WITH_SERVER_LOG_WARNING'
(folder/'verification.json').write_text(json.dumps(result,indent=2))
table='\n'.join(f"| {r['seq']} | {r['esp_log_uptime_ms']} | {r['app_rtt_ms']} | {r['temperature_c']} | {r['humidity_pct']} | {r['sensor_error']} |" for r in rows)
summary=f'''# HOME_BOARD TCP_TLS WIFI_PS_NONE startup smoke verification

**{result['status']}**. Startup check only; no formal experiment was started. All 18 registered runs remain NOT_RUN and the CSV/workbook hashes are unchanged.

## Prepared artifacts and flash

Used only [matching TCP_TLS profile artifacts](../../../profiles/tcp_tls_wifi_ps_none_20261104/README.md): [application](../../../profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.bin), [ELF](../../../profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.elf), bootloader and partition table from the same profile. App SHA-256 **{result['image_sha256']}**; ELF SHA-256 **{result['elf_sha256']}**. [Pre-flash artifact checks](./preflash_artifacts.json).

Flash command from that build directory: `esptool --chip esp32c6 --port COM6 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args`. Bootloader 0x0, partition 0x8000 and app 0x10000 all passed written-data hash verification; exit 0. [Successful raw flash log](./HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_flash.log), [result](./flash_result.json). Esptool logged an in-memory bootloader header/digest update for flash parameters; prepared disk inputs remain hash-identical.

An initial attempt failed opening the still-busy COM6 port, before connection/reset/write: [failed-attempt evidence](./flash_attempt1_port_busy.log). Its prerequisite listener query had returned no match because Windows CIM reports this listener with blank State/offload metadata, despite the project server process and socket existing. A [local TLS readiness probe](./server_tls_readiness.json) verified the actual listener before retrying. The probe used TLS_AES_256_GCM_SHA384; it is a separate host-only connection, not the board negotiation. The existing monitor was then gracefully exited via its control file, flushing/closing output: [closure record](./previous_monitor_closed.json). No unrelated listener or QUIC server was stopped.

## Persistent server and monitor

Project tcp_tls_server.py started persistently with `.quic-venv/Scripts/python.exe -u`, TCP 0.0.0.0:14568, owner PID {server['process']['ProcessId']}. [Server metadata](./server_session.json), [live stdout](./tcp_tls_server.stdout.log), [live stderr](./tcp_tls_server.stderr.log), [sensor CSV source]({sensor_path.as_uri()}). No server source changes. The listener is further demonstrated by successful board connections and matching sensor records.

The new persistent ESP-IDF monitor uses the TCP_TLS ELF, COM6 at 115200: [monitor command and PIDs](./monitor_session.json), [HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE serial log](./HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_serial.log). Logging was active before the controlled startup reset requested at **{session['controlled_reset_requested_utc']}**. Initial startup output from opening the port precedes the explicit reset marker and is excluded from the checked five echoes. Flash downloader/post-write resets and this controlled startup reset are recorded; no formal 37-minute recording was started.

Startup digest prefix `{result['reported_elf_prefix']}...` matches the prepared ELF; a full on-device ELF digest was not printed. Explicit setter/readback reports **requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)**. Assigned IP **{ip}**. TCP_NODELAY **1**. TCP_TLS connection, MQTT connection and subscription acknowledgement confirmed.

Actual board TLS evidence:

```text
{tls_line}
```

## First five APP_RTT echoes and matching sensors

| Sequence | ESP log uptime ms | APP_RTT ms | Temperature C | Humidity %RH | Sensor error |
|---:|---:|---:|---:|---:|---:|
{table}

All five match server records by post-reset UTC boundary, sequence, client ID `esp32_quic_client`, topic `esp32/quic/test` and DHT11 payload. Each sensor_error is 0. [Joined echoes/sensor CSV](./first_five_echoes_and_sensors.csv), [matching sensor rows](./matching_server_sensor_records.csv), [serial snapshot](./serial_startup_through_first_five.log), [server stdout snapshot](./tcp_tls_server_stdout_snapshot.log). These are startup echoes, without warmup exclusion or formal-run eligibility. No connection errors or sequence gaps were observed in this controlled startup through echo five; all warning/error evidence remains in the raw log.

## Preservation and next registered run

All {counts['original_build']} original-build and {counts['quic_profile']} QUIC-profile inventoried files retain their recorded hashes; both QUIC BIN/ELF pairs and the formal register CSV/workbook match their pre-smoke hashes. No rebuild, firmware edit or dependency change occurred. This smoke output is separate under results/pilots. Clumsy effects were not enabled or settings changed by this task; existing filter remains untouched.

First registered run is **{first['run_id']} — {first['transport']} — {first['condition']}**, still **NOT_RUN**. [Register](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/run_register.csv). This smoke test does not consume or substitute for it. TCP server and new monitor are left running; the prior QUIC server is also preserved.

[Structured verification](./verification.json) contains actual source/artifact paths, reset/completion UTC times, all first-five measurements, sensor UTC timestamps and preservation checks.
'''
if server_error_lines:
    summary+='\n\n## Server-log warning\n\nThe persistent server stderr contains '+str(len(server_error_lines))+' bare `TCP+TLS ERROR:` line(s), with no timestamp, peer/connection ID or error detail. They cannot be confidently attributed to the measured boot versus setup/local-probe connections. The controlled serial startup through the first five echoes has no connection errors, all five matching sensor records succeeded, and later fresh RTTs continue. This caveat is retained rather than claiming an entirely error-free server log. See [server stderr snapshot](./tcp_tls_server_stderr_snapshot.log) and structured verification.\n'
summary=summary.replace(sensor_path.as_uri(),'../../../logs/'+sensor_path.name)
(folder/'SUMMARY.md').write_text(summary,encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
