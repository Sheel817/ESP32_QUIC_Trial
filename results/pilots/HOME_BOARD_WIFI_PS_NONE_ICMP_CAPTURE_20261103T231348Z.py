"""One operator-requested ping run; no device or application settings changes."""
import csv
import datetime as dt
import json
from pathlib import Path
import re
import statistics
import subprocess

prefix=Path(__file__).with_suffix('')
label='HOME_BOARD, WIFI_PS_NONE verified at startup, Clumsy ICMP capture running, all effects disabled — operator-reported GUI settings.'
command=['ping.exe','/n','30','/w','2000','192.168.137.212']
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def output(suffix): return prefix.with_name(prefix.name+suffix)
def csv_write(suffix,rows):
    with output(suffix).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

started=utc()
lines=[]
requests=[]
with output('.raw.txt').open('w',encoding='utf-8') as raw:
    proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for text in proc.stdout:
        received=utc()
        text=text.rstrip('\r\n')
        raw.write(text+'\n')
        raw.flush()
        lines.append(dict(received_utc=received,raw_line=text))
        reply=re.search(r'Reply from ([\d.]+): bytes=\d+ time([=<])(\d+)ms TTL=(\d+)',text)
        timeout='Request timed out.' in text
        failure=('unreachable' in text.lower() or 'general failure' in text.lower() or 'transmit failed' in text.lower())
        if reply or timeout or failure:
            reported=(('<' if reply[2]=='<' else '')+reply[3]) if reply else ''
            requests.append(dict(request_number=len(requests)+1,received_utc=received,status='reply' if reply else ('timeout' if timeout else 'other_failure'),rtt_reported_ms=reported,rtt_numeric_reported_ms=reply[3] if reply and reply[2]=='=' else '',censored=bool(reply and reply[2]=='<'),reply_ip=reply[1] if reply else '',label=label,raw_line=text))
    exit_code=proc.wait()
ended=utc()
csv_write('.requests.csv',requests)
csv_write('.output_timestamped.csv',lines)
assert len(requests)==30, f'Expected 30 per-request results; found {len(requests)}'
replies=[r for r in requests if r['status']=='reply']
numeric=[float(r['rtt_numeric_reported_ms']) for r in replies if not r['censored']]
censored=[r for r in replies if r['censored']]
low_values=[0.0 if r['censored'] else float(r['rtt_numeric_reported_ms']) for r in replies]
high_values=[float(r['rtt_reported_ms'][1:]) if r['censored'] else float(r['rtt_numeric_reported_ms']) for r in replies]
result=dict(label=label,command=command,started_utc=started,ended_utc=ended,exit_code=exit_code,requests=len(requests),replies=len(replies),timeouts=sum(r['status']=='timeout' for r in requests),other_failures=sum(r['status']=='other_failure' for r in requests),all_rtt_reported_ms=[r['rtt_reported_ms'] if r['status']=='reply' else r['status'] for r in requests],censored_replies=len(censored),startup_verification_source='HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json',clumsy_evidence='Operator-reported only; GUI not inspected or changed during this run',settings_actions='None: no reset/build/flash/firmware/Clumsy/server/monitor settings changes')
if replies:
    if censored:
        result.update(mean_lower_bound_ms=statistics.mean(low_values),mean_upper_bound_exclusive_ms=statistics.mean(high_values),median_lower_bound_ms=statistics.median(low_values),median_upper_bound_ms=statistics.median(high_values),minimum_reported_ms='<'+str(min(float(r['rtt_reported_ms'][1:]) for r in censored)),maximum_reported_ms=max(numeric) if numeric else '<'+str(max(high_values)),censoring='Each <1 ms observation is interval-censored in [0,1) ms; no exact RTT assigned. Mean bounds use these intervals; all other ping RTTs have integer reporting resolution.')
    else:
        result.update(minimum_ms=min(numeric),median_ms=statistics.median(numeric),mean_ms=statistics.mean(numeric),maximum_ms=max(numeric),censoring='No less-than observations. Statistics use the integer-resolution RTTs reported by Windows ping.')
output('.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
table='\n'.join(f"| {r['request_number']} | {r['received_utc']} | {r['status']} | {r['rtt_reported_ms']} |" for r in requests)
if censored:
    metrics=f"Minimum reported: {result['minimum_reported_ms']} ms; median bounds: {result['median_lower_bound_ms']:.4f} to {result['median_upper_bound_ms']:.4f} ms; mean **{result['mean_lower_bound_ms']:.4f} <= mean < {result['mean_upper_bound_exclusive_ms']:.4f} ms**; maximum reported: {result['maximum_reported_ms']} ms. {len(censored)} censored observations."
else:
    metrics=f"Minimum **{result['minimum_ms']:g} ms**, median **{result['median_ms']:g} ms**, mean **{result['mean_ms']:.4f} ms**, maximum **{result['maximum_ms']:g} ms**."
summary=f'''# HOME_BOARD WIFI_PS_NONE — ICMP capture, effects disabled

{label}

Exact command: `{' '.join(command)}`

UTC start: {started}; UTC finish: {ended}. Exit code: {exit_code}.

Requests: **30**; replies: **{len(replies)}**; timeouts: **{result['timeouts']}**; other failures: **{result['other_failures']}**.

{metrics}

{result['censoring']} Reply-only RTT statistics; failures are retained separately.

| Request | Host output receipt UTC | Status | Reported RTT ms |
|---:|---|---|---:|
{table}

[Complete raw output](./{output('.raw.txt').name}), [per-request CSV](./{output('.requests.csv').name}), [complete output with UTC receipt timestamps](./{output('.output_timestamped.csv').name}), [metadata and statistics](./{output('.json').name}). UTC receipt timestamps indicate when the host read each output line, not exact ICMP wire timestamps.

WIFI_PS_NONE was verified in the preceding controlled startup: [startup evidence](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json). No fresh mode readback or reset was performed. Clumsy capture/effects settings are operator-reported; no GUI inspection or changes were made in this run. No firmware, server, or monitor settings changed. This run remains separate from default-power-saving, previous Clumsy-stopped, and university-board results; no data were pooled or overwritten.
'''
output('.md').write_text(summary,encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False),flush=True)
