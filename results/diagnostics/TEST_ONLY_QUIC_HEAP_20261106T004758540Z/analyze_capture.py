"""Offline TEST_ONLY analysis. Never opens a serial port or modifies inputs."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

out = Path(__file__).resolve().parent
root = out.parents[2]
def load(name): return json.loads((out/name).read_text(encoding='utf-8'))
def save(name, value):
    with (out/name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
complete = load('CAPTURE_COMPLETE.json')
assert not (out/'HOST_FAILURE.json').exists()
raw = (out/'TEST_ONLY_uart.raw.log').read_bytes()
text = raw.decode('utf-8', errors='replace')
receipts = [json.loads(s) for s in (out/'TEST_ONLY_uart_receipts.jsonl').read_text().splitlines()]
start = load('reset_release.json')
deadline = start['observation_deadline_monotonic']
boot_offsets = [m.start() for m in re.finditer(rb'ESP-ROM:esp32c6',raw)]
rtts=[]
for m in re.finditer(rb'I \((\d+)\).*?APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',raw):
    receipt = next((x for x in receipts if x['offset'] <= m.start() < x['offset']+x['length']),None)
    rtts.append(dict(boot=sum(x<=m.start() for x in boot_offsets),esp_ms=int(m[1]),sequence=int(m[2]),rtt_ms=float(m[3]),raw_offset=m.start(),receipt_utc=receipt['utc'] if receipt else None,received_by_primary_deadline=receipt['monotonic']<=deadline if receipt else None))
save('TEST_ONLY_rtt_observations.json',rtts)
cores=[]
for n,m in enumerate(re.finditer(rb'=+ CORE DUMP START =+\r?\n',raw),1):
    end=re.search(rb'=+ CORE DUMP END =+',raw[m.end():])
    d=out/f'TEST_ONLY_core_{n:02d}';d.mkdir(exist_ok=False)
    stop=m.end()+end.start() if end else len(raw)
    (d/'TEST_ONLY_core.b64').write_bytes(raw[m.end():stop])
    (d/'TEST_ONLY_core_framed.raw').write_bytes(raw[m.start():m.end()+end.end()] if end else raw[m.start():])
    cores.append(dict(ordinal=n,directory=str(d),complete=end is not None,raw_start=m.start(),boot=sum(x<=m.start() for x in boot_offsets)))
issues=[s for s in text.splitlines() if re.search(r'Guru Meditation|panic|CORRUPT|CHECK_FAIL|abort\(\)|assert failed|^E \(|^W \(',s,re.I)]
fault = bool(re.search(r'Guru Meditation|CORRUPT|CHECK_FAIL|abort\(\)|assert failed',text,re.I) or cores)
gaps=[]
for a,b in zip(rtts,rtts[1:]):
    if a['boot']==b['boot'] and b['sequence']!=a['sequence']+1:gaps.append([a['sequence'],b['sequence']])
server=[]
for name,boundary in start['server_boundaries'].items():
    p=Path(boundary['path']);end=p.stat().st_size
    with p.open('rb') as f:f.seek(boundary['bytes']);data=f.read(end-boundary['bytes'])
    target=out/f'TEST_ONLY_server_{name}.snapshot.log';target.write_bytes(data)
    server.append(dict(stream=name,source=str(p),start_offset=boundary['bytes'],end_offset=end,snapshot=str(target),sha256=digest(target),snapshot_utc=dt.datetime.now(dt.timezone.utc).isoformat(),note='Snapshot extends to analysis time; host timestamps/contents must delimit primary window. No claim all bytes are within180s.'))
analysis=dict(label='TEST_ONLY',result='FAULT_OBSERVED' if fault else 'NOT_REPRODUCED',observation_start_utc=start['reset_release_utc'],observation_deadline_utc=start['observation_deadline_utc'],completion=complete,application_boots=len(boot_offsets),automatic_reboots=max(0,len(boot_offsets)-1),first_startup_captured=raw.startswith(b'ESP-ROM:esp32c6'),diagnostic_elf_prefix_confirmed='ELF file SHA256:  a8056d24f' in text,test_only_banner='TEST_ONLY QUIC HEAP DIAGNOSTIC v1' in text,wifi_ps_none_readback='requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)' in text,ip=re.findall(r'example_netif_sta ip: ([\d.]+)',text),quic_connected='QUIC connection established' in text,mqtt_connected='MQTT connected over QUIC' in text,tls_lines=[s for s in text.splitlines() if 'negotiated TLS=' in s],rtt_count=len(rtts),sequence_gaps=gaps,warnings_errors_fault_lines=issues,core_dumps=cores,server_snapshots=server,heap_checkpoint_observability='Passing checkpoints remain in RAM and are not printed on normal execution. Without a panic/core or failure trace, last passing checkpoint cannot be recovered from this UART record. No first failing checkpoint observed.' if not fault else 'Requires core/text-trace decoding; do not infer from candidate frames.',limitations=['One180-second instrumented boot cannot establish a fix.','Trace and heap checks perturb timing.','UART host receipt times and reset API return are host anchors, not physical edge measurements.','No RAM readback was attempted on a live healthy target.'],protection=load('protection_after.json'),firmware_remaining=complete['firmware_remaining'])
save('TEST_ONLY_ANALYSIS.json',analysis)
print(json.dumps(analysis,indent=2))
