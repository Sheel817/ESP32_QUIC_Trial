"""Read only new bytes of the existing monitor log; never open the COM port."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics
import time

prefix=Path(__file__).with_suffix('')
def output(suffix):return prefix.with_name(prefix.name+suffix)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
wait_started=utc()
time.sleep(60)
source_path=Path('C:/Users/newsh/Desktop/ESP32_QUIC_Trial/results/pilots/HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log')
boundary_offset=source_path.stat().st_size
boundary_data=dict(source_log=str(source_path),boundary_utc=utc(),byte_offset=boundary_offset,label='QUIC, HOME_BOARD, WIFI_PS_NONE, UDP 14567 capture, Lag 100 ms outbound only; other effects off — operator-reported settings.',wait_started_utc=wait_started,requested_wait_seconds=60)
output('.boundary.json').write_text(json.dumps(boundary_data,indent=2,ensure_ascii=False),encoding='utf-8')
boundary=json.loads(output('.boundary.json').read_text(encoding='utf-8-sig'))
source=Path(boundary['source_log'])
offset=boundary['byte_offset']
watcher_started=utc()
with source.open('rb') as f:
    before=f.read(offset)
partial_boundary=bool(before and not before.endswith(b'\n'))
previous_matches=list(re.finditer(rb'APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',before))
previous_seq=int(previous_matches[-1][1]) if previous_matches else None
pattern=re.compile(r'^(\S+) I \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)')
deadline=time.monotonic()+180
while True:
    with source.open('rb') as f:
        f.seek(0,2)
        assert f.tell()>=offset,'Source log was truncated'
        f.seek(offset)
        appended=f.read()
    parts=appended.splitlines(keepends=True)
    rows=[]
    interval=[]
    end_offset=offset
    for index,part in enumerate(parts):
        if not part.endswith(b'\n'):
            break
        end_offset+=len(part)
        if index==0 and partial_boundary:
            continue
        line=part.decode('utf-8',errors='replace').rstrip('\r\n')
        interval.append(line)
        match=pattern.match(line)
        if match and int(match[2])>60000:
            local=dt.datetime.fromisoformat(match[1]).replace(tzinfo=dt.timezone(dt.timedelta(hours=2)))
            rows.append(dict(sample=len(rows)+1,source_log=str(source),boundary_utc=boundary['boundary_utc'],boundary_byte_offset=offset,record_host_local=local.isoformat(),record_host_utc=local.astimezone(dt.timezone.utc).isoformat(),seq=int(match[3]),esp_log_uptime_ms=int(match[2]),app_rtt_ms=match[4],label=boundary['label'],raw_line=line))
            if len(rows)==10:
                break
    if len(rows)==10:
        break
    if time.monotonic()>deadline:
        raise RuntimeError(f'Only {len(rows)} fresh qualifying records; original monitor untouched')
    time.sleep(0.25)
finished=utc()
captured=appended[:end_offset-offset]
output('.raw.log').write_bytes(captured)
with output('.csv').open('w',encoding='utf-8',newline='') as f:
    fields=list(rows[0])+['collection_finished_utc']
    writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader()
    writer.writerows(dict(r,collection_finished_utc=finished) for r in rows)
gaps=[]
last=previous_seq
for r in rows:
    if last is not None and r['seq']!=last+1:
        gaps.append(dict(previous=last,current=r['seq'],expected=last+1))
    last=r['seq']
warnings=[line for line in interval if re.search(r'\b[WE] \(\d+\)',line)]
errors=[line for line in interval if re.search(r'(?i)(disconnect|connection.*(?:error|fail|lost)|handshake.*(?:error|fail)|MQTT.*(?:error|fail)|QUIC.*(?:error|fail)|ESP-ROM:|reboot|panic|abort\(|APP_RTT (?:ignored|storage full))',line)]
values=[float(r['app_rtt_ms']) for r in rows]
result=dict(label=boundary['label'],source_log=str(source),boundary_utc=boundary['boundary_utc'],boundary_byte_offset=offset,boundary_was_partial_line=partial_boundary,previous_app_rtt_seq_at_boundary=previous_seq,watcher_started_utc=watcher_started,collection_finished_utc=finished,first_record_host_utc=rows[0]['record_host_utc'],last_record_host_utc=rows[-1]['record_host_utc'],end_byte_offset=end_offset,raw_interval_sha256=hashlib.sha256(captured).hexdigest(),records=10,sequences=[r['seq'] for r in rows],esp_timestamps_ms=[r['esp_log_uptime_ms'] for r in rows],app_rtt_ms=[r['app_rtt_ms'] for r in rows],mean_ms=statistics.mean(values),minimum_ms=min(values),maximum_ms=max(values),sequence_gaps=gaps,connection_error_or_reboot_lines=errors,all_warning_error_lines=warnings,settings_evidence='Operator-reported GUI settings; not inspected or changed',actions='Read existing log only; no COM open, ping, reset, build, flash, or settings changes')
output('.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
table='\n'.join(f"| {r['seq']} | {r['record_host_utc']} | {r['esp_log_uptime_ms']} | {r['app_rtt_ms']} |" for r in rows)
summary=f'''# HOME_BOARD QUIC WIFI_PS_NONE — UDP outbound Lag 100 ms APP_RTT

{boundary['label']}

Source: [existing monitor log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Fresh boundary after the request: **{boundary['boundary_utc']}**, byte offset **{offset}**, immediately following prior APP_RTT sequence **{previous_seq}**. Boundary partial line: {partial_boundary}. Only complete records appended after this boundary were eligible. All 10 have ESP uptime >60000 ms, retained in arrival order without trimming.

UTC collection boundary/start: {boundary['boundary_utc']}; reader started: {watcher_started}; completed: **{finished}**. Source host timestamps are Europe/Helsinki UTC+02:00 at second resolution; CSV records their UTC equivalents. They are log receipt timestamps, not wire timestamps.

| Sequence | Host receipt UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
{table}

Mean **{result['mean_ms']:.4f} ms**, minimum **{result['minimum_ms']:.3f} ms**, maximum **{result['maximum_ms']:.3f} ms**.

Sequence gaps, including the boundary transition: **{len(gaps)}**. Connection-error/reboot/APP_RTT anomaly lines: **{len(errors)}**. All warning/error log lines in the captured interval: **{len(warnings)}**. These observations cover the saved interval through the tenth qualifying APP_RTT, not the entire historical log or unlogged network events.

[Timestamped CSV](./{output('.csv').name}), [raw appended interval](./{output('.raw.log').name}), [boundary metadata](./{output('.boundary.json').name}), [statistics, gap/error evidence and hashes](./{output('.json').name}). The original live log is not copied over or modified. No pings, port opens, resets, builds, flashes or settings changes were performed; existing monitor and server remain untouched.
'''
output('.md').write_text(summary,encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False),flush=True)

reference_path=prefix.parent/'HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.csv'
with reference_path.open(encoding='utf-8',newline='') as f:
    reference_rows=list(csv.DictReader(f))
assert [int(r['seq']) for r in reference_rows]==list(range(273,283))
reference_mean=statistics.mean(float(r['app_rtt_ms']) for r in reference_rows)
assert round(reference_mean,4)==66.2630
comparison=dict(reference_csv=str(reference_path),reference_csv_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),reference_sequences=[int(r['seq']) for r in reference_rows],reference_mean_ms=reference_mean,lag_mean_ms=result['mean_ms'],mean_change_ms=result['mean_ms']-reference_mean,wait_started_utc=wait_started,boundary_utc=boundary['boundary_utc'],requested_wait_seconds=60)
output('.comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
with output('.md').open('a',encoding='utf-8') as f:
    f.write(f"\n\n## Matching capture-only comparison\n\nWait began **{wait_started}**; a 60-second wait completed before marking the boundary above.\n\nReference: [actual capture-only CSV](./{reference_path.name}), sequences **273–282**, recomputed mean **{reference_mean:.4f} ms**. Current Lag pilot mean **{result['mean_ms']:.4f} ms**, change **{result['mean_ms']-reference_mean:+.4f} ms**. Every selected RTT was retained, including high/low values. No ICMP, default-power-saving, or university-board data are included. GUI settings remain operator-reported.\n\n[Comparison metadata and reference hash](./{output('.comparison.json').name}).\n")
print(json.dumps(comparison,indent=2),flush=True)
