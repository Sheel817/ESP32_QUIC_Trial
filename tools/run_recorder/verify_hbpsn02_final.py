"""Verify existing fixed-window data; add a separate post-capture review report."""
from pathlib import Path
from decimal import Decimal
import csv,datetime as dt,hashlib,io,json,math,re,statistics

root=Path(__file__).resolve().parents[2];study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
a=Path(Path(__file__).with_name('active_hbpsn02_path.txt').read_text().strip())
postdirs=sorted(a.glob('post_recording_evidence_*'));out=postdirs[-1]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(out/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def csvread(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
start=load(a/'reset_event.json');auto=load(a/'statistics.json');finalized=load(a/'FINALIZED.json');post=load(out/'capture_metadata.json');pre=load(a/'pre_run_settings_check.json')['evidence']
assert finalized['processing_status']=='FINALIZED' and finalized['validity_status']=='NOT_APPROVED'
assert start['reset_release_utc']=='2026-11-04T12:17:27.280042+00:00' and start['deadline_utc']=='2026-11-04T12:54:27.280042+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert sha(a/pre['screenshot'])==pre['sha256']
assert sha(Path(post['image_path']))==post['sha256']
assert pre['observed']==post['observed']
protected=[p for p in a.iterdir() if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log','heartbeat.json'}]
save('original_finalization_hashes.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in protected])
checks={}
serial_lines=serial_receipts=None
for channel,rawname,idxname in [('serial','serial.raw.log','serial_receipts.jsonl')]+[(n,f'server.{n}.raw.log',f'server.{n}.receipts.jsonl') for n in ['stdout','stderr','sensor_csv']]:
    raw=(a/rawname).read_bytes();lines=raw.splitlines(keepends=True);receipts=[json.loads(line) for line in (a/idxname).read_text().splitlines()]
    assert len(lines)==len(receipts)
    pos=0;previous=None;source=a/'monitor_stream.log' if channel=='serial' else Path(start['server_boundaries'][channel]['source'])
    with source.open('rb') as f:
        for line,r in zip(lines,receipts):
            assert r['offset']==pos and r['length']==len(line)
            assert start['reset_release_monotonic']<=r['monotonic']<start['deadline_monotonic']
            assert dt.datetime.fromisoformat(start['reset_release_utc'])<=dt.datetime.fromisoformat(r['utc'])<dt.datetime.fromisoformat(start['deadline_utc'])
            assert previous is None or r['monotonic']>=previous
            previous=r['monotonic'];pos+=len(line)
            f.seek(r['monitor_stream_offset'] if channel=='serial' else r['source_offset']);assert f.read(len(line))==line
    assert pos==len(raw)
    checks[channel]=dict(bytes=len(raw),lines=len(lines),first_receipt=receipts[0] if receipts else None,last_receipt=receipts[-1] if receipts else None,all_receipts_in_original_window=True,source_bytes_match=True,sha256=sha(a/rawname))
    if channel=='serial':serial_lines=[r.decode('utf-8',errors='replace').rstrip('\r\n') for r in lines];serial_receipts=receipts
    else:
        boundary=load(a/f'server_{channel}_boundary_end.json')
        assert boundary['end_byte']-boundary['start_byte']==len(raw)
        checks[channel]['source_boundary']=boundary
all_csv=csvread(a/'all_rtts.csv');eligible_csv=csvread(a/'eligible_rtts.csv');selected=csvread(a/'selected_first_415.csv');excluded=csvread(a/'excluded_rtts.csv');extra=csvread(a/'eligible_extra.csv')
parsed=[];eligible=[];warmup=[];gaps=[];resets=[];lastseq=None;lasttime=None;regressions=[];unparsed=[]
for n,(line,receipt) in enumerate(zip(serial_lines,serial_receipts),1):
    if 'ESP-ROM:esp32c6' in line:resets.append(dict(source_line=n,raw_line=line,utc=receipt['utc']))
    up=re.search(r'\b[IWE] \((\d+)\)',line)
    if up:
        t=int(up[1])
        if lasttime is not None and lasttime>60000 and t<lasttime-1000:regressions.append(dict(source_line=n,previous=lasttime,current=t))
        lasttime=t
    m=re.search(r'\bI \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',line)
    if not m:
        if 'APP_RTT' in line:unparsed.append(dict(source_line=n,raw_line=line))
        continue
    record=dict(seq=int(m[2]),esp_log_uptime_ms=int(m[1]),app_rtt_ms=m[3],source_line=n,host_receipt_utc=receipt['utc'])
    parsed.append(record)
    if lastseq is not None and record['seq']!=lastseq+1:gaps.append(dict(previous=lastseq,current=record['seq']))
    lastseq=record['seq']
    if record['esp_log_uptime_ms']<60000:warmup.append(record)
    elif record['esp_log_uptime_ms']<2220000:eligible.append(record)
assert len(resets)==1 and not regressions and not gaps and not unparsed
def key(r):return (int(r['seq']),int(r['esp_log_uptime_ms']),str(r['app_rtt_ms']))
assert [key(r) for r in parsed]==[key(r) for r in all_csv]
assert [key(r) for r in eligible]==[key(r) for r in eligible_csv]
assert [key(r) for r in eligible[:415]]==[key(r) for r in selected]
assert [key(r) for r in eligible[415:]]==[key(r) for r in extra]
assert len(excluded)==len(warmup) and all(r['exclusion_reason']=='warmup_below_60000_ms' for r in excluded)
values=[Decimal(r['app_rtt_ms']) for r in selected];ordered=sorted(values)
stats=dict(raw_serial_lines=len(serial_lines),raw_rtt_count=len(parsed),warmup_excluded=len(warmup),other_excluded=0,eligible_count=len(eligible),selected_count=len(selected),extra_eligible_count=len(extra),shortfall=max(0,415-len(selected)),minimum_ms=float(min(values)),mean_ms=float(sum(values)/len(values)),mean_decimal=str(sum(values)/len(values)),median_ms=float(statistics.median(values)),p95_nearest_rank_ms=float(ordered[math.ceil(.95*len(values))-1]),p95_rank=math.ceil(.95*len(values)),maximum_ms=float(max(values)),first_selected=selected[0],last_selected=selected[-1])
for derived,automatic in [('raw_rtt_count','all_rtt_count'),('eligible_count','eligible_count'),('selected_count','selected_count'),('minimum_ms','minimum_ms'),('mean_ms','mean_ms'),('median_ms','median_ms'),('maximum_ms','maximum_ms'),('p95_nearest_rank_ms','p95_ms')]:assert stats[derived]==auto[automatic]
stderr_lines=(a/'server.stderr.raw.log').read_text().splitlines();stderr_receipts=[json.loads(x) for x in (a/'server.stderr.receipts.jsonl').read_text().splitlines()]
new_server_errors=[dict(raw_line=line,receipt=receipt,attribution='New within fixed window, retained. Bare message has no peer/session identity; cannot conclusively attribute it to the measured ESP connection.') for line,receipt in zip(stderr_lines,stderr_receipts) if 'ERROR' in line]
journal=[json.loads(x) for x in (a/'reporting_errors.jsonl').read_text().splitlines()]
assert not any(r.get('exhausted') for r in journal)
sensors=csvread(a/'server_sensor_records.csv')
assert [int(r['seq']) for r in sensors]==[r['seq'] for r in parsed]
sensor_errors=[r for r in sensors if r.get('sensor_error')!='0']
elapsed=(dt.datetime.fromisoformat(post['capture_started_utc'])-dt.datetime.fromisoformat(start['deadline_utc'])).total_seconds()
save('post_vs_pre_comparison.json',dict(pre_image=str(a/pre['screenshot']),pre_sha256=pre['sha256'],pre_capture_started_utc=pre['capture_started_utc'],pre_capture_completed_utc=pre['capture_completed_utc'],post_image=post['image_path'],post_sha256=post['sha256'],post_capture_started_utc=post['capture_started_utc'],post_capture_completed_utc=post['capture_completed_utc'],visible_settings_match=True,settings=post['observed'],post_capture_started_seconds_after_deadline=elapsed,operator_stability_confirmation='PENDING',validity='NOT_APPROVED / PENDING_EVIDENCE_REVIEW',original_automatic_missing_image_flag_preserved=True,note='No settings changed by agent before capture. Matching point-in-time images do not establish continuous stability or operator actions between them. The frozen plan has no numerical post-image deadline; 30 seconds was an implementation wait only.'))
save('verified_statistics.json',dict(**stats,original_window=start,processing_status='FINALIZED',automatic_status=finalized['status'],validity_status='NOT_APPROVED',evidence_review_status='PENDING_EVIDENCE_REVIEW',resets=resets,additional_resets=0,gaps=gaps,timestamp_regressions=regressions,serial_connection_errors=auto['connection_error_lines'],new_server_errors=new_server_errors,serial_warnings=auto['warning_error_lines'],reporting_errors=journal,server_sensor_records=len(sensors),sensor_errors=sensor_errors))
save('fixed_window_integrity.json',checks)
save('automatic_finalization_preserved.json',dict(marker=finalized,original_marker_path=str(a/'FINALIZED.json'),post_image_added_separately=True,no_reanalysis_of_later_measurements=True))
# Stage just HBPSN-02's row, retaining the original machine failure flag until review.
reg=study/'run_register.csv';rows=csvread(reg);lines=reg.read_bytes().splitlines(keepends=True)
assert rows[0]['status']=='FAILED_SETTINGS' and rows[1]['run_id']=='HBPSN-02' and rows[1]['status']=='RUNNING'
with reg.open(newline='',encoding='utf-8-sig') as f:headers=next(csv.reader(f))
save('register_before_review.json',dict(hbpsn02=rows[1],register_sha256=sha(reg)))
(out/'register_before_review.csv').write_bytes(reg.read_bytes())
(out/'register_before_review.xlsx').write_bytes((root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx').read_bytes())
patch=dict(status=finalized['status'],recording_end_utc=start['deadline_utc'],actual_duration_seconds=2220,eligible_count=len(eligible),selected_count=len(selected),shortfall=stats['shortfall'],connection_error_count=len(new_server_errors)+len(auto['connection_error_lines']),sequence_gap_count=0,mean_app_rtt_ms=stats['mean_ms'],minimum_app_rtt_ms=stats['minimum_ms'],maximum_app_rtt_ms=stats['maximum_ms'],deviation_reason='Data finalized in original fixed window. Original automatic FAILED_SETTINGS flag preserved after 30s image wait; actual post image captured 2026-11-04T13:12:42.221Z separately. Visible settings match; operator stability confirmation/evidence review PENDING, validity NOT_APPROVED. One new unattributed server TCP error retained; zero serial connection errors.')
target=dict(rows[1]);target.update(patch);buf=io.StringIO(newline='');csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n').writerow(target)
lines[2]=buf.getvalue().encode();staged=out/'register_final.staged.csv';staged.write_bytes(b''.join(lines))
save('register_apply_request.json',dict(run_id='HBPSN-02',phase='FINAL_REVIEW_PENDING',output_dir=str(out),csv_staged_path=str(staged),patch=patch))
Path(__file__).with_name('hbpsn02_review_path.txt').write_text(str(out))
print(json.dumps(dict(review_directory=str(out),statistics=stats,new_server_errors=new_server_errors,reporting_error_count=len(journal),sensor_errors=len(sensor_errors),post_capture_delay_seconds=elapsed),indent=2))
