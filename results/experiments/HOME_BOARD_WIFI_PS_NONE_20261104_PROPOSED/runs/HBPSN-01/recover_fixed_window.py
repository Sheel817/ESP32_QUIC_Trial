"""Offline recovery only. Never imports or controls the live recorder/device."""
from pathlib import Path
import csv, datetime as dt, hashlib, json, math, re, shutil, statistics
from decimal import Decimal

base = Path(__file__).resolve().parent
a = base / 'attempt_20261104T002840Z'
study = base.parents[1]
root = study.parents[2]
now = dt.datetime.now(dt.timezone.utc)
out = a / ('recovery_' + now.strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(exist_ok=False)
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name, data): (out/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def table(name, rows, fields):
    with (out/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
start=load(a/'reset_event.json'); pre=load(a/'preflight.json')
assert start['reset_release_utc']=='2026-11-04T00:38:26.326642+00:00'
assert start['deadline_utc']=='2026-11-04T01:15:26.326642+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert not (a/'COMPLETE.json').exists()
fixed_names=['serial.raw.log','serial_receipts.jsonl','server.stdout.raw.log','server.stdout.receipts.jsonl','server.stderr.raw.log','server.stderr.receipts.jsonl','server_stdout_boundary_end.json','server_stderr_boundary_end.json','reset_event.json','startup_checks.json','preflight.json','collector_failure.json','collector.py','monitor_instrumented.py','collector_prepared.json','RUNNING.json','flash_result.json','flash.log','identification.log','final_settings_precheck.json']
sources=[dict(path=str(a/n),bytes=(a/n).stat().st_size,sha256=digest(a/n)) for n in fixed_names]
shutil.copy2(a/'collector_failure.json',out/'collector_failure_preserved.json')
shutil.copy2(study/'run_register.csv',out/'register_before_recovery.csv')
shutil.copy2(root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',out/'register_before_recovery.xlsx')
checks={}; serial_lines=None;serial_receipts=None
for channel,rawname,idxname in [('serial','serial.raw.log','serial_receipts.jsonl'),('stdout','server.stdout.raw.log','server.stdout.receipts.jsonl'),('stderr','server.stderr.raw.log','server.stderr.receipts.jsonl')]:
    raw=(a/rawname).read_bytes(); lines=raw.splitlines(keepends=True)
    receipts=[json.loads(s) for s in (a/idxname).read_text().splitlines()]
    assert len(lines)==len(receipts),(channel,'line/receipt mismatch')
    pos=0;prev=None
    with (a/'monitor_stream.log' if channel=='serial' else Path(start['server_boundaries'][channel]['source'])).open('rb') as stream:
        for line,rec in zip(lines,receipts):
            assert rec['offset']==pos and rec['length']==len(line)
            assert start['reset_release_monotonic']<=rec['monotonic']<start['deadline_monotonic']
            assert start['reset_release_utc']<=rec['utc']<start['deadline_utc']
            assert prev is None or rec['monotonic']>=prev
            prev=rec['monotonic'];pos+=len(line)
            stream.seek(rec['monitor_stream_offset'] if channel=='serial' else rec['source_offset'])
            assert stream.read(len(line))==line, (channel,'source interval mismatch')
    assert pos==len(raw)
    checks[channel]=dict(line_count=len(lines),bytes=len(raw),contiguous_byte_index=True,all_receipts_in_original_window=True,source_bytes_match=True,first_receipt=receipts[0] if receipts else None,last_receipt=receipts[-1] if receipts else None)
    if channel=='serial':serial_lines=[s.decode('utf-8',errors='replace').rstrip('\r\n') for s in lines];serial_receipts=receipts
    else:
        end=load(a/f'server_{channel}_boundary_end.json')
        assert end['end_byte']-end['start_byte']==len(raw)
        checks[channel]['end_boundary']=end

rows=[];eligible=[];excluded=[];warnings=[];errors=[];resets=[];gaps=[];malformed=[]
seen=set();boots=0;initial=True;last_up=None;last_seq=None
for n,(line,rec) in enumerate(zip(serial_lines,serial_receipts),1):
    evidence=dict(source_line=n,host_receipt_utc=rec['utc'],raw_line=line)
    if 'ESP-ROM:esp32c6' in line:
        boots+=1;resets.append(dict(**evidence,initial_designated_boot=boots==1))
        if boots>1:initial=False
    stamp=re.search(r'\b[IWE] \((\d+)\)',line)
    if stamp:
        up=int(stamp[1])
        if last_up is not None and last_up>60000 and up<last_up-1000:
            initial=False;resets.append(dict(**evidence,reason='timestamp_regression'))
        last_up=up
    if re.search(r'\b[WE] \(\d+\)',line):warnings.append(evidence)
    if re.search(r'(?i)(\bE \(\d+\)|disconnect|connection.*(?:error|fail|lost)|handshake.*(?:error|fail)|APP_RTT (?:ignored|storage full)|panic|abort\(|serial.*(?:closed|error)|waiting for.*port)',line):errors.append(evidence)
    m=re.search(r'\bI \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',line)
    if not m:
        if 'APP_RTT' in line:malformed.append(evidence)
        continue
    r=dict(run_id='HBPSN-01',board='HOME_BOARD',transport='QUIC',wifi_ps_mode='WIFI_PS_NONE',condition='CONTROL',source_line=n,source_byte_offset=rec['offset'],host_receipt_utc=rec['utc'],host_monotonic=rec['monotonic'],esp_log_uptime_ms=int(m[1]),seq=int(m[2]),app_rtt_ms=m[3],raw_line=line)
    rows.append(r)
    if last_seq is not None and r['seq']!=last_seq+1:gaps.append(dict(previous_seq=last_seq,current_seq=r['seq'],source_line=n))
    last_seq=r['seq']
    reason= 'subsequent_boot_or_regression' if not initial else ('warmup_below_60000_ms' if r['esp_log_uptime_ms']<60000 else ('at_or_above_2220000_ms' if r['esp_log_uptime_ms']>=2220000 else ('duplicate_sequence' if r['seq'] in seen else '')))
    if reason:excluded.append(dict(**r,exclusion_reason=reason))
    else:eligible.append(r)
    seen.add(r['seq'])
selected=eligible[:415];vals=[Decimal(r['app_rtt_ms']) for r in selected];ordered=sorted(vals)
fields=list(rows[0])
for name,data in [('all_rtts.csv',rows),('eligible_rtts.csv',eligible),('selected_first_415.csv',selected),('eligible_extra.csv',eligible[415:])]:table(name,data,fields)
table('excluded_rtts.csv',excluded,fields+['exclusion_reason'])
table('warning_error_ledger.csv',[dict(**r,classification='warning_or_error') for r in warnings],['source_line','host_receipt_utc','raw_line','classification'])
sensor_source=Path(pre['server_sensor_source'])
with sensor_source.open(newline='',encoding='utf-8') as f:
    rd=csv.DictReader(f);sf=rd.fieldnames
    sensor=[r for r in rd if dt.datetime.fromisoformat(start['reset_release_utc'])<=dt.datetime.fromisoformat(r['server_receive_utc'].replace('Z','+00:00'))<dt.datetime.fromisoformat(start['deadline_utc'])]
table('server_sensor_records.csv',sensor,sf)
post=a/'post_recording_settings_check.json'
postcheck=load(post) if post.exists() else dict(status='MISSING',reason='No contemporaneous post-recording screenshot/settings check saved. Late observation cannot establish deadline settings.')
interrupted=len(resets)>1 or any(a.glob('*tail_failure.json')) or (a/'monitor_exit.json').exists()
startup=load(a/'startup_checks.json')
status='FAILED_STARTUP' if not startup['pass_all'] else ('INTERRUPTED' if interrupted else ('FAILED_SETTINGS' if postcheck.get('status')!='PASS' else ('COMPLETE_SHORTFALL' if len(selected)<415 else 'COMPLETE')))
limitations=['Automatic finalization failed at 2026-11-04T00:46:45.650030+00:00 (WinError 5 heartbeat replacement); independent byte-indexed recording threads continued to original cutoff.',postcheck.get('reason',''),'Host API return is the reset-release anchor, not a measured physical edge. ESP log timestamps define uptime eligibility; host receipt time defines fixed-window inclusion.','No continuous GUI or per-packet proof of effect state; preflight screenshot/operator evidence only.']
stats=dict(run_id='HBPSN-01',status=status,recording_window_status='RECOVERED_FIXED_WINDOW',automatic_finalization_succeeded=False,recovered_utc=now.isoformat(),recording_start_utc=start['reset_release_utc'],recording_end_utc=start['deadline_utc'],recording_start_helsinki='2026-11-04T02:38:26.326642+02:00',recording_end_helsinki='2026-11-04T03:15:26.326642+02:00',duration_seconds=2220,raw_serial_lines=len(serial_lines),raw_app_rtt_count=len(rows),warmup_excluded_count=sum(r['exclusion_reason']=='warmup_below_60000_ms' for r in excluded),other_excluded_count=sum(r['exclusion_reason']!='warmup_below_60000_ms' for r in excluded),eligible_count=len(eligible),selected_count=len(selected),extra_eligible_count=max(0,len(eligible)-415),shortfall=max(0,415-len(selected)),minimum_ms=float(min(vals)),mean_ms=float(sum(vals)/len(vals)),mean_ms_decimal=str(sum(vals)/len(vals)),median_ms=float(statistics.median(vals)),p95_nearest_rank_ms=float(ordered[math.ceil(.95*len(vals))-1]),p95_rank=math.ceil(.95*len(vals)),p95_method='Nearest rank: sorted ascending, 1-based ceil(0.95*N)',maximum_ms=float(max(vals)),first_selected=selected[0],last_selected=selected[-1],initial_designated_boot_count=min(boots,1),additional_reset_count=max(0,boots-1),resets=resets,sequence_gaps=gaps,warning_error_lines=warnings,connection_error_lines=errors,unparsed_app_rtt_lines=malformed,post_recording_settings_check=postcheck,limitations=limitations,server_sensor_record_count=len(sensor),startup=startup)
save('statistics.json',stats)
save('integrity_checks.json',checks)
save('source_hashes.json',sources)
save('provenance.json',dict(protocol_id='HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED_V1',source_directory=str(a),recovery_directory=str(out),plan_path=str(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),plan_sha256=digest(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),manifest_sha256=digest(study/'freeze_manifest.json'),original_reset_anchor=start,preflight=pre,sensor_source=str(sensor_source),sensor_selection='UTC interval [original reset release, original deadline), no later rows',source_hashes=sources))
save('register_final_request.json',dict(output_dir=str(out),final=True,patch=dict(status=status,recording_end_utc=start['deadline_utc'],actual_duration_seconds=2220,eligible_count=len(eligible),selected_count=len(selected),shortfall=max(0,415-len(selected)),connection_error_count=len(errors),sequence_gap_count=len(gaps),mean_app_rtt_ms=stats['mean_ms'],minimum_app_rtt_ms=stats['minimum_ms'],maximum_app_rtt_ms=stats['maximum_ms'],metadata_path=str((out/'statistics.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((a/'serial.raw.log').relative_to(study)).replace('\\','/'),deviation_reason='Recovered original fixed window after automatic heartbeat WinError 5 failure. Missing required contemporaneous post-recording settings evidence; retained as FAILED_SETTINGS, no replacement or extension.')))
assert all(digest(Path(s['path']))==s['sha256'] for s in sources)
print(json.dumps(dict(recovery_directory=str(out),statistics=stats),indent=2))
