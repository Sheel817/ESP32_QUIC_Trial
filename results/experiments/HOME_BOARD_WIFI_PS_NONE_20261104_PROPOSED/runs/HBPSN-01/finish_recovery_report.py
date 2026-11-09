"""Verify and document the existing offline recovery; no device operations."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,math,re,statistics,zipfile,xml.etree.ElementTree as ET
from decimal import Decimal
base=Path(__file__).resolve().parent
a=base/'attempt_20261104T002840Z'; out=a/'recovery_20261104T013757Z';study=base.parents[1];root=study.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(out/name).write_text(json.dumps(x,indent=2),encoding='utf-8')
s=read(out/'statistics.json');prov=read(out/'provenance.json');checks=read(out/'integrity_checks.json')
for r in read(out/'source_hashes.json'):assert sha(Path(r['path']))==r['sha256']
assert prov['plan_sha256']==read(a/'preflight.json')['plan_sha256']
assert prov['manifest_sha256']==read(a/'preflight.json')['freeze_manifest_sha256']
with (out/'selected_first_415.csv').open(newline='') as f:sel=list(csv.DictReader(f))
v=[Decimal(r['app_rtt_ms']) for r in sel]
assert len(v)==415 and float(sum(v)/len(v))==s['mean_ms']
assert float(sorted(v)[math.ceil(Decimal('.95')*len(v))-1])==s['p95_nearest_rank_ms']
assert [int(r['seq']) for r in sel]==list(range(11,426))
with (out/'server_sensor_records.csv').open(newline='') as f:sensors=list(csv.DictReader(f))
assert [int(r['seq']) for r in sensors]==list(range(1,442))
sensor_errors=[r for r in sensors if r['sensor_error']!='0']
server_flags=[dict(source_line=i,raw_line=line) for i,line in enumerate((a/'server.stdout.raw.log').read_text().splitlines(),1) if re.search(r'(?i)\b(?:error|exception|traceback|disconnect\w*|failed|warning)\b',line)]
assert (a/'server.stderr.raw.log').stat().st_size==0
with (out/'register_before_recovery.csv').open(newline='',encoding='utf-8-sig') as f:before=list(csv.DictReader(f))
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:after=list(csv.DictReader(f))
assert before[1:]==after[1:] and len(after)==18
assert after[0]['status']=='FAILED_SETTINGS' and all(r['status']=='NOT_RUN' for r in after[1:])
xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
# Independent saved-XLSX readback, never authors workbook XML.
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(xlsx) as z:
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
    sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    cells={c.attrib['r']:c for c in sheet.findall('.//m:c',ns)}
    def cell(ref):
        c=cells[ref];value=c.find('m:v',ns)
        if c.attrib.get('t')=='s':return strings[int(value.text)]
        if c.attrib.get('t')=='inlineStr':return ''.join(c.find('m:is',ns).itertext())
        return value.text if value is not None else ''
    assert cell('G2')=='FAILED_SETTINGS'
    assert all(cell('G'+str(i))=='NOT_RUN' for i in range(3,20))
intervals=[dict(source=str(a/'monitor_stream.log'),start_byte=checks['serial']['first_receipt']['monitor_stream_offset'],end_byte=checks['serial']['last_receipt']['monitor_stream_offset']+checks['serial']['last_receipt']['length'],sha256=sha(a/'serial.raw.log'),matches=str(a/'serial.raw.log')),dict(source=checks['stdout']['end_boundary']['source'],start_byte=380697,end_byte=456361,sha256=sha(a/'server.stdout.raw.log'),matches=str(a/'server.stdout.raw.log'))]
save('final_verification.json',dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),original_recording_hashes_unchanged=True,frozen_plan_and_manifest_unchanged=True,independent_selected_csv_recalculation_passed=True,server_sensor_sequence_range=[1,441],server_sensor_errors=sensor_errors,server_stdout_flagged_lines=server_flags,server_stderr_bytes=0,other_17_register_rows_unchanged=True,saved_xlsx_status_verified=True,live_source_intervals=intervals))
report=f'''# HBPSN-01 final recovered result

HOME_BOARD, QUIC, WIFI_PS_NONE, CONTROL. UDP 14567 capture running, all effects off: operator-reported and observed in preflight GUI. No post-recording settings check was saved.

**Final register status: FAILED_SETTINGS. Recording status: RECOVERED_FIXED_WINDOW.** The complete 37-minute data window was recovered, but the required contemporaneous post-recording settings evidence is missing. This is an evidence limitation, not a finding that settings changed. Startup checks passed. No replacement run was made.

## Original fixed window

4 November 2026, **02:38:26.327–03:15:26.327 Helsinki (UTC+02)**. UTC 00:38:26.327–01:15:26.327. Original stored reset-release anchor is 00:38:26.326642+00:00, deadline 01:15:26.326642+00:00; the displayed millisecond times are rounded. Selection uses these original full-precision anchors and host-monotonic interval [507017.5434011, 509237.5434011), exactly 2,220 seconds. The reset anchor is host reset-API completion rather than a measured electrical edge.

## Automatic finalization and recovery

Automatic finalization **failed** at 00:46:45.650030 UTC (02:46:45.650 Helsinki). Windows raised WinError 5 Access denied replacing heartbeat.json.tmp with heartbeat.json. The original [failure traceback](../collector_failure.json) remains untouched; a [preserved copy](./collector_failure_preserved.json) and its hash are retained here. No automatic COMPLETE or final statistics existed. The main loop stopped, while the independent serial/server reader threads continued gating by the original monotonic deadline.

Offline recovery checked every raw line against its receipt, contiguous byte offsets, original UTC/monotonic window, and corresponding bytes in the live source logs. All checks passed. Server tails closed at 01:15:26.327186 and 01:15:26.327014 UTC. Serial recording ends at the last received line before cutoff, 01:15:24.292193 UTC; later live-monitor lines are not included. The fixed serial log remains immutable. Live source interval hashes identify the relevant bytes without hashing later appended data.

## Counts and selection

| Item | Count |
|---|---:|
| Raw serial lines | {s['raw_serial_lines']} |
| Raw numeric APP_RTT records | {s['raw_app_rtt_count']} |
| Warm-up excluded (ESP log uptime <60,000 ms) | {s['warmup_excluded_count']} |
| Other excluded numeric records | {s['other_excluded_count']} |
| Eligible within initial boot/window | {s['eligible_count']} |
| Selected first eligible records | {s['selected_count']} |
| Extra eligible records retained outside primary subset | {s['extra_eligible_count']} |
| Shortfall | {s['shortfall']} |

All 441 numeric RTTs are sequences 1–441. Selected sequences are **11–425**, ESP log uptime **63,653–2,137,793 ms**. Selected host receipts are **00:39:29.994180–01:14:04.114527 UTC**, or **02:39:29.994180–03:14:04.114527 Helsinki**. Raw source lines 161–575. All numeric outliers remain in their original arrival order. Every eligible value, including the 16 extras (426–441), is preserved.

| Selected APP_RTT statistic | ms |
|---|---:|
| Minimum | {s['minimum_ms']:.3f} |
| Mean | {s['mean_ms']:.10f} |
| Median | {s['median_ms']:.3f} |
| Nearest-rank P95 | {s['p95_nearest_rank_ms']:.3f} |
| Maximum | {s['maximum_ms']:.3f} |

P95 is ascending sorted observation rank ceil(0.95 × 415) = **395**, with no interpolation. RTTs have the firmware's printed precision; no censoring or trimming was applied.

## Resets, errors and limitations

One designated startup; **0 additional resets**, **0 timestamp regressions**, **0 sequence gaps/repeats**, **0 unparsed APP_RTT lines**, and **0 logged connection errors**. Three startup Wi-Fi warning lines are retained in the [warning ledger](./warning_error_ledger.csv): WPA2 authentication-threshold adjustment, rate-table trace, and BA-add trace. No serial E-level lines were found. Server stderr is empty; server stdout has {len(server_flags)} error/warning/disconnect pattern matches. Server sensor CSV has 441 records, sequences 1–441, with {len(sensor_errors)} nonzero sensor errors. This corroborates matching sequences; receipt timing is not a network packet capture or independent impairment measurement.

The recorder supervisor's heartbeat failed during the run, so its later periodic liveness checks and automatic finalizer did not execute. Continuous sequence and byte receipt evidence shows no observed recording interruption; it cannot establish absence of every unlogged external event. Required post-recording GUI/settings evidence is missing. Preflight verified the frozen QUIC UDP filter and all effects unchecked; this does not establish per-packet effect state throughout the session. The monitor and server were left running; recovery performed no reset, build, flash, ping or settings change.

## Files, provenance and register

- [Original serial recording](../serial.raw.log), [serial receipt index](../serial_receipts.jsonl), [server stdout](../server.stdout.raw.log), [server stderr](../server.stderr.raw.log).
- [All RTTs](./all_rtts.csv), [warm-up exclusions](./excluded_rtts.csv), [eligible RTTs](./eligible_rtts.csv), [selected first 415](./selected_first_415.csv), [extra eligible RTTs](./eligible_extra.csv), [server sensor records](./server_sensor_records.csv).
- [Statistics](./statistics.json), [provenance and firmware/configuration hashes](./provenance.json), [byte/receipt integrity checks](./integrity_checks.json), [final verification](./final_verification.json), [source SHA-256](./source_hashes.json), [output and register SHA-256 manifest](./SHA256SUMS.json).
- [Run register CSV](../../../../run_register.csv) and [run register workbook](../../../../../../../outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx): only HBPSN-01 updated from RUNNING to FAILED_SETTINGS, with fixed deadline, counts, statistics and recovery path. Other 17 entries remain NOT_RUN and unchanged. [Update receipt](./register_final_update.json). Pre-recovery register copies retained here.
- Frozen plan SHA-256 `{prov['plan_sha256']}`; freeze manifest SHA-256 `{prov['manifest_sha256']}`. Both unchanged. Earlier failed preflight report remains preserved outside the successful attempt.

Recovered at {s['recovered_utc']}. No later measurements included and no recording extension made.
'''
(out/'SUMMARY.md').write_text(report,encoding='utf-8')
save('FINALIZED.json',dict(status=s['status'],recording_status=s['recording_window_status'],recovered_utc=s['recovered_utc'],original_window_unchanged=True,summary=str(out/'SUMMARY.md'),selected_count=415,register_updated=True))
files=[p for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json']+[study/'run_register.csv',xlsx,study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'freeze_manifest.json',base/'PREFLIGHT_BLOCKED.md',base/'recover_fixed_window.py',Path(__file__).resolve()]
save('SHA256SUMS.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
print(json.dumps(dict(status=s['status'],summary=str(out/'SUMMARY.md'),hashes={p.name:sha(p) for p in [a/'serial.raw.log',out/'selected_first_415.csv',out/'statistics.json',out/'SUMMARY.md',study/'run_register.csv',xlsx,out/'SHA256SUMS.json']}),indent=2))
