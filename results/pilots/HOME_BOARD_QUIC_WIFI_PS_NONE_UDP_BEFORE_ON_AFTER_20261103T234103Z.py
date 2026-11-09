"""Recompute the HOME_BOARD QUIC pilot from three immutable capture CSVs."""
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics

folder=Path(__file__).resolve().parent
prefix=Path(__file__).with_suffix('')
stages=[('Before','HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z',list(range(273,283))),('Lag on','HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z',list(range(351,361))),('After','HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z',None)]
def out(suffix):return prefix.with_name(prefix.name+suffix)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csv_write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
statistics_rows=[]
measurements=[]
evidence=[]
blocks=[]
for stage,stem,expected in stages:
    csv_path=folder/(stem+'.csv')
    metadata=json.loads((folder/(stem+'.json')).read_text(encoding='utf-8'))
    boundary=json.loads((folder/(stem+'.boundary.json')).read_text(encoding='utf-8-sig'))
    raw_path=folder/(stem+'.raw.log')
    raw=raw_path.read_bytes()
    with csv_path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==10
    sequences=[int(r['seq']) for r in rows]
    if expected is not None:assert sequences==expected
    assert all(int(r['esp_log_uptime_ms'])>60000 for r in rows)
    assert rows[0]['boundary_utc']==metadata['boundary_utc']==boundary['boundary_utc']
    assert metadata['raw_interval_sha256']==sha(raw_path)
    source=Path(metadata['source_log'])
    with source.open('rb') as f:
        source_prefix=f.read(metadata['end_byte_offset'])
    assert source_prefix[metadata['boundary_byte_offset']:metadata['end_byte_offset']]==raw
    raw_matches=re.findall(r'APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',raw.decode('utf-8',errors='replace'))
    assert [(str(r['seq']),r['app_rtt_ms']) for r in rows]==raw_matches
    gaps=[]
    previous=metadata['previous_app_rtt_seq_at_boundary']
    for sequence in sequences:
        if previous is not None and sequence!=previous+1:
            gaps.append(dict(previous=previous,current=sequence,expected=previous+1))
        previous=sequence
    interval=raw.decode('utf-8',errors='replace').splitlines()
    warnings=[s for s in interval if re.search(r'\b[WE] \(\d+\)',s)]
    errors=[s for s in interval if re.search(r'(?i)(disconnect|connection.*(?:error|fail|lost)|handshake.*(?:error|fail)|MQTT.*(?:error|fail)|QUIC.*(?:error|fail)|ESP-ROM:|reboot|panic|abort\(|APP_RTT (?:ignored|storage full))',s)]
    values=[float(r['app_rtt_ms']) for r in rows]
    row=dict(stage=stage,records=len(rows),first_seq=sequences[0],last_seq=sequences[-1],mean_ms=statistics.mean(values),minimum_ms=min(values),maximum_ms=max(values),sequence_gaps=len(gaps),connection_error_or_reboot_lines=len(errors),warning_error_lines=len(warnings),boundary_utc=boundary['boundary_utc'],boundary_byte_offset=boundary['byte_offset'],wait_started_utc=boundary.get('wait_started_utc',''),requested_wait_seconds=boundary.get('requested_wait_seconds',0),first_record_host_utc=rows[0]['record_host_utc'],last_record_host_utc=rows[-1]['record_host_utc'],collection_finished_utc=metadata['collection_finished_utc'],source_csv=str(csv_path),csv_sha256=sha(csv_path))
    statistics_rows.append(row)
    evidence.append(dict(stage=stage,label=metadata['label'],source_log=str(source),source_prefix_bytes=metadata['end_byte_offset'],source_prefix_sha256=hashlib.sha256(source_prefix).hexdigest(),boundary=boundary,collection_finished_utc=metadata['collection_finished_utc'],sequence_gaps=gaps,connection_error_or_reboot_lines=errors,all_warning_error_lines=warnings,files=[dict(path=str(folder/(stem+suffix)),sha256=sha(folder/(stem+suffix))) for suffix in ('.csv','.raw.log','.json','.boundary.json')]))
    for r in rows:measurements.append(dict(stage=stage,source_csv=csv_path.name,**r))
    table='\n'.join(f"| {r['seq']} | {r['record_host_utc']} | {r['esp_log_uptime_ms']} | {r['app_rtt_ms']} |" for r in rows)
    wait_text=f"Wait started {boundary.get('wait_started_utc')}; requested wait {boundary.get('requested_wait_seconds')} seconds." if boundary.get('requested_wait_seconds') else 'Immediate boundary after the capture-only request.'
    blocks.append(f'''## {stage}

Label: {metadata['label']}

{wait_text} Boundary **{boundary['boundary_utc']}**, byte **{boundary['byte_offset']}**, after sequence {metadata['previous_app_rtt_seq_at_boundary']}. First/last source host receipt UTC: {row['first_record_host_utc']} / {row['last_record_host_utc']}; reader completed {row['collection_finished_utc']}.

| Sequence | Host receipt UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
{table}

Mean {row['mean_ms']:.4f} ms; min {row['minimum_ms']:.3f}; max {row['maximum_ms']:.3f}. Gaps including boundary transition: {len(gaps)}; connection-error/reboot/APP_RTT anomaly lines: {len(errors)}; all warning/error lines: {len(warnings)}.

[Actual source CSV](./{stem}.csv), SHA-256 `{sha(csv_path)}`. [Raw interval](./{stem}.raw.log), SHA-256 `{sha(raw_path)}`. [Boundary metadata](./{stem}.boundary.json), [capture metadata/errors](./{stem}.json).
''')
assert round(statistics_rows[0]['mean_ms'],4)==66.2630
assert round(statistics_rows[1]['mean_ms'],4)==187.7515
comparison=dict(lag_on_minus_before_ms=statistics_rows[1]['mean_ms']-statistics_rows[0]['mean_ms'],after_minus_before_ms=statistics_rows[2]['mean_ms']-statistics_rows[0]['mean_ms'],after_minus_lag_on_ms=statistics_rows[2]['mean_ms']-statistics_rows[1]['mean_ms'])
csv_write(out('.statistics.csv'),statistics_rows)
csv_write(out('.all_measurements.csv'),measurements)
out('.json').write_text(json.dumps(dict(label='QUIC HOME_BOARD WIFI_PS_NONE UDP capture before/on/after pilot',statistics=statistics_rows,comparison=comparison,evidence=evidence),indent=2,ensure_ascii=False),encoding='utf-8')
top_table='\n'.join(f"| {r['stage']} | {r['first_seq']}–{r['last_seq']} | {r['mean_ms']:.4f} | {r['minimum_ms']:.3f} | {r['maximum_ms']:.3f} | {r['sequence_gaps']} | {r['connection_error_or_reboot_lines']} |" for r in statistics_rows)
text=f'''# HOME_BOARD WIFI_PS_NONE QUIC — before/on/after UDP Lag pilot

All statistics were recomputed from the actual three 10-record CSVs and cross-checked against their saved raw intervals and corresponding byte ranges in the existing source log. No values were removed. The earlier files were read only and remain preserved.

Source live log for all stages: [HOME_BOARD_WIFI_PS_NONE_serial.log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Absolute source paths, file hashes, hashes of the live-log prefixes up to each captured end offset, boundaries and all errors/gaps are recorded in [evidence JSON](./{out('.json').name}). A live growing file has no single fixed final hash; immutable intervals and exact prefixes are hashed instead.

| Stage | Sequences | Mean ms | Min ms | Max ms | Gaps | Connection/error/reboot lines |
|---|---|---:|---:|---:|---:|---:|
{top_table}

Lag-on minus before: **{comparison['lag_on_minus_before_ms']:+.4f} ms**. After minus before: **{comparison['after_minus_before_ms']:+.4f} ms**. After minus lag-on: **{comparison['after_minus_lag_on_ms']:+.4f} ms**.

This is a QUIC application RTT pilot, not an ICMP diagnostic. No ICMP, default-power-saving, or university-board results enter the comparison. Clumsy capture/effect settings are operator-reported and were not inspected or changed. The return condition is **UDP capture running, all effects off — operator-reported**. The new return run waited 60 seconds before marking its fresh boundary; only complete newly appended records after that boundary, with ESP uptime >60000 ms, were selected.

Sequence gaps are evaluated within each selected phase and from its own immediately preceding boundary sequence. Unmeasured time between phases is not called a sequence gap. Host timestamps have one-second resolution, converted from Europe/Helsinki UTC+02:00; precise boundary/collection UTC times are saved separately. APP_RTT includes application and transport scheduling as well as network delay. These sequential small samples do not establish a long-run latency distribution.

'''+ '\n'.join(blocks)+f'''
## Derived outputs and final state

[All 30 measurements with source paths, boundaries and UTC metadata](./{out('.all_measurements.csv').name}), [recomputed statistics CSV](./{out('.statistics.csv').name}), [full evidence and hashes](./{out('.json').name}). No pings, port opens, resets, builds, flashes, or firmware/filter/server/monitor/Clumsy settings changes were performed. Existing monitor and server were left untouched.
'''
out('.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(statistics=statistics_rows,comparison=comparison),indent=2))
