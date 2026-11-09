"""Original-criteria review; only HBPSN-05 register row may change."""
from pathlib import Path
import copy,csv,datetime as dt,hashlib,io,json,math,os,re,shutil,statistics,zipfile,xml.etree.ElementTree as E
out=Path(__file__).resolve().parent;run=out.parent;study=run.parents[2];root=study.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x):
    with (out/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def rows(p):return list(csv.DictReader(p.open(newline='',encoding='utf-8-sig')))
assert not (out/'REGISTERS_UPDATED.json').exists()
statement=dict(exact_statement='yes it wa sunchanged',source='Operator confirmation relayed by user from ChatGPT',receipt_observed_utc='2026-11-06T14:11:59.6194955Z',receipt_observed_helsinki='2026-11-06T16:11:59.6194955+02:00',receipt_clock_source='First local clock observation while processing the current user message; original chat ingress timestamp unavailable',covered_interval_helsinki=['2026-11-06T15:13:20.156+02:00','2026-11-06T15:53:14.719+02:00'],confirmed_scope='Unchanged Clumsy filter, effects and capture; no Stop/Start or close/reopen',not_backdated=True)
save('operator_statement.json',statement)
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';text=plan.read_text(encoding='utf-8');assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
rules=dict(images='Save screenshots before reset and after recording, with UTC and hashes.',stability='Settings must be stable before the measured reset and throughout the 37 minutes.',errors='If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.')
assert all(x in text for x in rules.values())
postdir=run/'post_recording_evidence_20261106T135313729Z';v=load(postdir/'POST_RECORDING_VERIFICATION.json');post=load(postdir/'capture_metadata.json');pre=load(run/'pre_run_settings_check.json')['evidence'];start=load(run/'reset_event.json');stats=load(run/'statistics.json');automatic=load(run/'FINALIZED.json')
assert load(run/'startup_checks.json')['pass_all']
assert start['reset_release_utc']=='2026-11-06T13:13:20.156359+00:00' and start['deadline_utc']=='2026-11-06T13:50:20.156359+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert automatic['processing_status']=='FINALIZED' and automatic['deadline_utc']==start['deadline_utc']
assert sha(run/pre['screenshot'])==pre['sha256'] and sha(postdir/post['image'])==post['sha256']
assert pre['observed']==post['observed']==load(run/'preflight.json')['expected_clumsy_settings']
selected=rows(run/'selected_first_415.csv');eligible=rows(run/'eligible_rtts.csv');allr=rows(run/'all_rtts.csv')
assert len(selected)==415 and len(eligible)==431 and len(allr)==441 and selected==eligible[:415]
assert all(60000<=int(r['esp_log_uptime_ms'])<2220000 for r in eligible)
assert all(start['reset_release_monotonic']<=float(r['host_monotonic'])<start['deadline_monotonic'] for r in allr)
values=[float(x['app_rtt_ms']) for x in selected]
assert statistics.mean(values)==stats['mean_ms'] and statistics.median(values)==stats['median_ms']
assert sorted(values)[math.ceil(.95*len(values))-1]==stats['p95_ms']
assert len(stats['resets'])==1 and stats['resets'][0]['initial_designated_boot']
assert not any(stats[k] for k in ['connection_error_lines','sequence_gaps','interruptions','server_tail_errors','server_stderr'])
manifest=load(run/'SHA256SUMS.json');assert all(sha(run/x['path'])==x['sha256'] for x in manifest)
assert all(sha(postdir/x['path'])==x['sha256'] for x in load(postdir/'SHA256SUMS.json'))
reg=study/'run_register.csv';xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
raw=reg.read_bytes();lines=raw.splitlines(keepends=True);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));headers=reader.fieldnames;rr=list(reader)
assert len(rr)==18 and [r['status'] for r in rr[:6]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','RUNNING','NOT_RUN']
ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';q=lambda x:'{'+ns+'}'+x
with zipfile.ZipFile(xlsx) as z:
    xml=z.read('xl/worksheets/sheet1.xml');workrows=E.fromstring(xml).findall('.//'+q('sheetData')+'/'+q('row'))
    for i,r in enumerate(rr,2):
        wr=workrows[i-1]
        for key,column in [('run_id','C'),('transport','D'),('condition','E'),('status','G')]:
            c=next(c for c in wr if c.get('r')==column+str(i));value=''.join(c.find(q('is')).itertext()) if c.get('t')=='inlineStr' else c.find(q('v')).text;assert value==r[key]
shutil.copy2(reg,out/'before_run_register.csv');shutil.copy2(xlsx,out/'before_run_register.xlsx');before={str(p):sha(p) for p in [reg,xlsx]}
deviation='Manual review COMPLETE with retained flags. Exact operator statement yes it wa sunchanged relayed from ChatGPT; local receipt2026-11-06T14:11:59.6194955Z; original chat ingress unavailable. Stability confirmed through post-image. Actual post-image173.572641s late; no frozen numerical cutoff. Three Wi-Fi warnings retained; no serial/server connection errors, subsequent resets, gaps or shortfall. Original automatic FAILED_SETTINGS/MISSING and all raw evidence preserved. Earlier QUIC crash remains unresolved.'
patch=dict(status='COMPLETE',settings_evidence_type='actual_pre_post_GUI_images_and_operator_reported_stability; manually_reviewed',recording_end_utc=start['deadline_utc'],actual_duration_seconds=2220,eligible_count=431,selected_count=415,shortfall=0,connection_error_count=0,sequence_gap_count=0,mean_app_rtt_ms=stats['mean_ms'],minimum_app_rtt_ms=stats['minimum_ms'],maximum_app_rtt_ms=stats['maximum_ms'],metadata_path=str((out/'manual_review.json').relative_to(study)).replace('\\','/'),deviation_reason=deviation)
target=dict(rr[4]);target.update(patch);buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n');w.writerow(target)
assert len(lines)==19;newlines=list(lines);newlines[5]=buf.getvalue().encode();assert all(newlines[i]==lines[i] for i in range(19) if i!=5)
(out/'updated_register.csv').write_bytes(b''.join(newlines))
def col(n):
    s=''
    while n:n,a=divmod(n-1,26);s=chr(65+a)+s
    return s
with zipfile.ZipFile(xlsx) as z:
    m=re.search(rb'<(?:\w+:)?row\b[^>]*\br="6"[^>]*>.*?</(?:\w+:)?row>',xml,re.S);assert m
    row=E.fromstring(b'<root xmlns="'+ns.encode()+b'" xmlns:x="'+ns.encode()+b'" xmlns:ns0="'+ns.encode()+b'">'+m.group()+b'</root>')[0]
    for k,value in patch.items():
        ref=col(headers.index(k)+1)+'6';c=next((c for c in row if c.get('r')==ref),None)
        if c is None:c=E.SubElement(row,q('c'),{'r':ref})
        for child in list(c):c.remove(child)
        c.set('t','inlineStr');E.SubElement(E.SubElement(c,q('is')),q('t')).text=str(value)
    updated=xml[:m.start()]+E.tostring(row,encoding='utf-8')+xml[m.end():]
    with zipfile.ZipFile(out/'updated_register.xlsx','x') as targetzip:
        for info in z.infolist():targetzip.writestr(copy.copy(info),updated if info.filename=='xl/worksheets/sheet1.xml' else z.read(info.filename))
    with zipfile.ZipFile(out/'updated_register.xlsx') as check:
        assert check.testzip() is None and all(check.read(n)==z.read(n) for n in z.namelist() if n!='xl/worksheets/sheet1.xml')
        assert updated.startswith(xml[:m.start()]) and updated.endswith(xml[m.end():])
nextrow=next(r for r in rr[5:] if r['status']=='NOT_RUN');frozen=load(study/'freeze_manifest.json')['schedule'];assert any(all(str(s[k])==nextrow[k] for k in ['order','run_id','transport','condition']) for s in frozen)
review=dict(run_id='HBPSN-05',reviewed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),decision='COMPLETE',validity_status='APPROVED_UNDER_ORIGINAL_FROZEN_PLAN',qualifier='COMPLETE with retained flags; no claim of independent continuous GUI observation or a repaired QUIC defect',operator_statement=statement,plan_sha256=sha(plan),exact_original_rules=rules,criteria=dict(fixed_window_pass=True,startup_pass=True,first415_selection_pass=True,pre_post_image_hashes_match=True,settings_match=True,stability_operator_confirmed=True,post_actual_start_utc=post['capture_started_utc'],post_actual_end_utc=post['capture_completed_utc'],post_lateness_seconds=173.572641,no_new_timing_cutoff=True,collector_30_second_wait_not_frozen_cutoff=True),counts=v['counts'],statistics=v['statistics'],warnings=stats['warning_error_lines'],errors=stats['connection_error_lines'],server_stderr=stats['server_stderr'],resets=stats['resets'],automatic_flags_preserved=automatic,original_verification=str(postdir/'POST_RECORDING_VERIFICATION.json'),original_final_manifest_verified=len(manifest),register_patch=patch,next_scheduled={k:nextrow[k] for k in ['order','run_id','transport','condition','status']},only_hbpsn05_row_changes=True,unresolved_quic_crash_preserved=True,next_run_started=False)
save('manual_review.json',review)
for dest,staged in [(reg,out/'updated_register.csv'),(xlsx,out/'updated_register.xlsx')]:
    temp=dest.with_name(dest.name+'.HBPSN05_COMPLETE.tmp');assert not temp.exists();temp.write_bytes(staged.read_bytes());os.replace(temp,dest)
save('REGISTERS_UPDATED.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),before_hashes=before,after_hashes={str(p):sha(p) for p in [reg,xlsx]},only_hbpsn05_row_changed=True,next_scheduled=review['next_scheduled']))
report=f'''# HBPSN-05 final review — COMPLETE with retained flags

Exact operator statement **“yes it wa sunchanged”**, relayed from ChatGPT. First observed local receipt **6November2026,16:11:59.6194955 Helsinki /14:11:59.6194955UTC**. Original chat ingress timestamp unavailable; none invented. Confirmation covers unchanged Clumsy filter/effects/capture, no Stop/Start or close/reopen,15:13:20.156–15:53:14.719Helsinki. [Statement](./operator_statement.json).

Original frozen criteria satisfied: original2220-second window15:13:20.156359–15:50:20.156359Helsinki; startup gates pass;441raw RTTs,10warm-up excluded,431eligible,415selected,16extras,zero shortfall. Actual pre/post image hashes match and show the frozen UDP14567/Lag100ms outbound-only condition. Continuous stability is operator-reported, not independently observed throughout.

Actual post-image lateness **173.572641seconds** preserved. No numerical cutoff exists in the frozen plan; collector30-second wait does not add one. Three Wi-Fi warnings retained. No serial/server connection errors, subsequent resets, gaps or interruptions recorded. Original automatic FAILED_SETTINGS/MISSING and all original raw evidence remain intact. Final approval does not rewrite those historical flags. Mean190.899824ms; median185.994ms; nearest-rankP95 245.685ms; min125.069ms; max525.973ms.

Both registers updated **only HBPSN-05**; prior snapshots and hashes preserved. Earlier outcomes unchanged; QUIC crash remains unresolved. No board, settings, server or monitor action taken.

Next scheduled NOT_RUN entry, independently matched between both registers and frozen schedule: **{nextrow['run_id']} — {nextrow['transport']} — {nextrow['condition']}**. It was **not started**. [Detailed review](./manual_review.json), [register audit](./REGISTERS_UPDATED.json).
'''
with (out/'REVIEW.md').open('x',encoding='utf-8') as f:f.write(report)
save('SHA256SUMS.json',[dict(path=p.name,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'])
print(json.dumps(dict(decision='COMPLETE_WITH_RETAINED_FLAGS',next_scheduled=review['next_scheduled'],review=str(out/'REVIEW.md')),indent=2))
