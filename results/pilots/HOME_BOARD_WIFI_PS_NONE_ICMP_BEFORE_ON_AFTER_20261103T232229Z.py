"""Recompute ICMP diagnostic statistics from the three actual request CSVs."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

folder=Path(__file__).resolve().parent
prefix=Path(__file__).with_suffix('')
sources=[('Before','HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z'),('Lag on','HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z'),('After','HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z')]
stats=[]
all_rows=[]
by_stage={}
def output(suffix):return prefix.with_name(prefix.name+suffix)
def csv_write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
for stage,stem in sources:
    path=folder/(stem+'.requests.csv')
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==30 and [int(r['request_number']) for r in rows]==list(range(1,31)),path
    by_stage[stage]=rows
    replies=[r for r in rows if r['status']=='reply']
    censored=[r for r in replies if r['rtt_reported_ms'].startswith('<')]
    low=[0.0 if r['rtt_reported_ms'].startswith('<') else float(r['rtt_reported_ms']) for r in replies]
    high=[float(r['rtt_reported_ms'].lstrip('<')) for r in replies]
    assert replies
    row=dict(stage=stage,requests=len(rows),replies=len(replies),timeouts=sum(r['status']=='timeout' for r in rows),other_failures=sum(r['status']=='other_failure' for r in rows),censored_replies=len(censored),minimum_reported_ms=('<'+str(min(float(r['rtt_reported_ms'][1:]) for r in censored))) if censored else min(low),median_ms=statistics.median(low) if statistics.median(low)==statistics.median(high) else '',median_lower_bound_ms=statistics.median(low),median_upper_bound_ms=statistics.median(high),mean_ms=statistics.mean(low) if not censored else '',mean_lower_bound_ms=statistics.mean(low),mean_upper_bound_ms=statistics.mean(high),mean_upper_bound_exclusive=bool(censored),maximum_reported_ms=max(high) if any(not r['rtt_reported_ms'].startswith('<') for r in replies) else '<'+str(max(high)),source_csv=path.name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),utc_start=json.loads((folder/(stem+'.json')).read_text(encoding='utf-8'))['started_utc'],utc_end=json.loads((folder/(stem+'.json')).read_text(encoding='utf-8'))['ended_utc'])
    stats.append(row)
    for request in rows:
        all_rows.append(dict(stage=stage,source_csv=path.name,**request))
assert round(stats[0]['mean_ms'],4)==2.6333
assert round(stats[1]['mean_ms'],4)==128.6667
csv_write(output('.statistics.csv'),stats)
csv_write(output('.all_requests.csv'),all_rows)
output('.json').write_text(json.dumps(dict(label='HOME_BOARD WIFI_PS_NONE ICMP diagnostic; capture running; before/on/after',settings_evidence='Operator-reported capture/effect settings; no GUI changes or fresh firmware readback in these ping runs',statistics=stats),indent=2,ensure_ascii=False),encoding='utf-8')
def mean_text(s):
    if s['censored_replies']:return f"[{s['mean_lower_bound_ms']:.4f}, {s['mean_upper_bound_ms']:.4f})"
    return f"{s['mean_ms']:.4f}"
def median_text(s):
    return str(s['median_ms']) if s['median_ms']!='' else f"[{s['median_lower_bound_ms']}, {s['median_upper_bound_ms']}]"
summary_table='\n'.join(f"| {s['stage']} | {s['requests']} | {s['replies']} | {s['timeouts']} | {s['other_failures']} | {s['minimum_reported_ms']} | {median_text(s)} | {mean_text(s)} | {s['maximum_reported_ms']} | {s['censored_replies']} |" for s in stats)
def value(r): return r['rtt_reported_ms'] if r['status']=='reply' else r['status']
values_table='\n'.join(f"| {i+1} | {value(by_stage['Before'][i])} | {value(by_stage['Lag on'][i])} | {value(by_stage['After'][i])} |" for i in range(30))
links='\n'.join(f"- {stage}: [actual 30-request CSV](./{stem}.requests.csv), [complete raw output](./{stem}.raw.txt), [UTC timestamped output](./{stem}.output_timestamped.csv), [run metadata](./{stem}.json)." for stage,stem in sources)
differences=''
if not any(s['censored_replies'] for s in stats):
    differences=f"Lag-on mean minus before: **{stats[1]['mean_ms']-stats[0]['mean_ms']:.4f} ms**. Return-to-control mean minus before: **{stats[2]['mean_ms']-stats[0]['mean_ms']:.4f} ms**. Return-to-control mean minus lag-on: **{stats[2]['mean_ms']-stats[1]['mean_ms']:.4f} ms**."
text=f'''# HOME_BOARD WIFI_PS_NONE — ICMP diagnostic, before/on/after

Three separate 30-request ICMP runs to 192.168.137.212 using `ping.exe /n 30 /w 2000 192.168.137.212`. Statistics below were recomputed from the actual three per-request CSVs, not copied from reference means. No default-power-saving, university-board, or APP_RTT data are included.

Before: ICMP capture running, all effects disabled. On: Lag 100 ms outbound only, other effects off. After: **HOME_BOARD, WIFI_PS_NONE, ICMP capture running, all effects off, return-to-control.** Capture and effects settings are operator-reported. No GUI or firmware/filter/server/monitor settings were changed in the return run. A 10-second wait preceded that ping command. WIFI_PS_NONE was verified in the [earlier controlled startup](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json); no fresh readback or reset was performed.

| Stage | Requests | Replies | Timeouts | Other failures | Min ms | Median ms | Mean ms | Max ms | Censored |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{summary_table}

{differences}

All reported RTTs are retained in request order, including failures and `<1 ms` if present. Statistics are reply-only, at Windows ping's reporting resolution. If censored values exist, each `<1 ms` contributes the interval [0,1) rather than an invented exact value; the mean is reported as lower-inclusive/upper-exclusive bounds. Zero censored counts mean no such bounds were required.

| Request | Before RTT ms | Lag-on RTT ms | After RTT ms |
|---:|---:|---:|---:|
{values_table}

## Actual input sources

{links}

[Recomputed statistics CSV](./{output('.statistics.csv').name}), [all 90 requests with source/UTC metadata](./{output('.all_requests.csv').name}), [statistics and source SHA-256 hashes](./{output('.json').name}). Original source files are preserved; these derived artifacts use new filenames.

This remains an **ICMP diagnostic**, not an application/QUIC RTT experiment. The sequential pilot shows the observed before/on/after pattern under operator-reported settings; it does not measure packet-by-packet Clumsy delays or establish a long-run distribution. Capture is left running with Lag off as reported by the operator, without automated settings changes.
'''
output('.md').write_text(text,encoding='utf-8')
print(json.dumps(stats,indent=2))
