"""Review original criteria and update only HBPSN-04 in both registers."""
from pathlib import Path
import copy,csv,datetime as dt,hashlib,io,json,os,re,shutil,zipfile,xml.etree.ElementTree as E
out=Path(__file__).resolve().parent;run=out.parent;study=run.parents[2];root=study.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x):
    with (out/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
assert not (out/'REGISTERS_UPDATED.json').exists()
statement=dict(exact_statement='yes i know..',source='Operator response relayed by user from ChatGPT',receipt_observed_utc='2026-11-06T12:59:46.7782638Z',receipt_observed_helsinki='2026-11-06T14:59:46.7782638+02:00',receipt_clock_source='First local UTC clock observation while processing this user message; original chat ingress timestamp unavailable',user_clarified_scope='Unchanged Clumsy filter, effects and capture; no Stop/Start or close/reopen, throughout6November2026,04:01:38–04:41:44 Helsinki',covered_interval_as_reported_helsinki=['2026-11-06T04:01:38+02:00','2026-11-06T04:41:44+02:00'],scope_interpretation='User explicitly confirms the previously requested run-start-through-post-screenshot interval; reported endpoints are second precision. Exact acquisition times remain separate.',not_backdated=True)
save('operator_statement.json',statement)
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
prior=load(run/'manual_review_20261106T024832982148Z/manual_review.json')
assert prior['decision']=='NOT_APPROVED_PENDING_STABILITY_CONFIRMATION'
v=load(run/'post_recording_evidence_20261106T024143336Z/POST_RECORDING_VERIFICATION.json')
pre=v['pre_image'];post=v['post_image'];postdir=run/'post_recording_evidence_20261106T024143336Z'
assert sha(run/pre['screenshot'])==pre['sha256'] and sha(postdir/post['image'])==post['sha256']
assert v['visible_settings_match'] and not any(post['main_effects'].values())
assert not v['subsequent_resets'] and not v['sequence_gaps'] and not v['interruptions'] and not v['server_tail_errors']
assert v['counts']['selected']==415 and v['counts']['shortfall']==0
assert all(sha(run/x['path'])==x['sha256'] for x in load(run/'SHA256SUMS.json'))
automatic=load(run/'FINALIZED.json');assert automatic['status']=='FAILED_SETTINGS' and automatic['processing_status']=='FINALIZED'
reg=study/'run_register.csv';xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
shutil.copy2(reg,out/'before_run_register.csv');shutil.copy2(xlsx,out/'before_run_register.xlsx')
before={str(p):sha(p) for p in [reg,xlsx]}
raw=reg.read_bytes();lines=raw.splitlines(keepends=True);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));headers=reader.fieldnames;rows=list(reader)
assert len(rows)==18 and [x['status'] for x in rows[:4]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','RUNNING']
deviation='Manual review COMPLETE with retained flags. Operator exact statement yes i know.. relayed by user; local receipt2026-11-06T12:59:46.7782638Z, original chat ingress unavailable; stability confirmed through actual post-image. Post-image184.654217s late; no frozen cutoff. One new unattributed server TCP+TLS ERROR retained; no serial connection error/reboot/gap/shortfall. Original automatic FAILED_SETTINGS/MISSING and all prior reviews preserved. Windows listener reporting discrepancy and pre-reset host evidence PermissionError retained. QUIC crash unresolved.'
patch=dict(status='COMPLETE',settings_evidence_type='actual_pre_post_GUI_images_and_operator_reported_stability; manually_reviewed',recording_end_utc=v['window_utc'][1],actual_duration_seconds=2220,eligible_count=431,selected_count=415,shortfall=0,connection_error_count=1,sequence_gap_count=0,mean_app_rtt_ms=v['statistics']['mean_ms'],minimum_app_rtt_ms=v['statistics']['minimum_ms'],maximum_app_rtt_ms=v['statistics']['maximum_ms'],metadata_path=str((out/'manual_review.json').relative_to(study)).replace('\\','/'),deviation_reason=deviation)
target=dict(rows[3]);target.update(patch);buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n');w.writerow(target)
assert len(lines)==19;updated_lines=list(lines);updated_lines[4]=buf.getvalue().encode();assert all(updated_lines[i]==lines[i] for i in range(19) if i!=4)
(out/'updated_register.csv').write_bytes(b''.join(updated_lines))
ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';q=lambda x:'{'+ns+'}'+x
def col(n):
    s=''
    while n:n,a=divmod(n-1,26);s=chr(65+a)+s
    return s
with zipfile.ZipFile(xlsx) as z:
    xml=z.read('xl/worksheets/sheet1.xml');m=re.search(rb'<(?:\w+:)?row\b[^>]*\br="5"[^>]*>.*?</(?:\w+:)?row>',xml,re.S);assert m
    row=E.fromstring(b'<root xmlns="'+ns.encode()+b'" xmlns:x="'+ns.encode()+b'" xmlns:ns0="'+ns.encode()+b'">'+m.group()+b'</root>')[0]
    for k,value in patch.items():
        ref=col(headers.index(k)+1)+'5';cell=next((c for c in row if c.get('r')==ref),None)
        if cell is None:cell=E.SubElement(row,q('c'),{'r':ref})
        for child in list(cell):cell.remove(child)
        cell.set('t','inlineStr');E.SubElement(E.SubElement(cell,q('is')),q('t')).text=str(value)
    updated=xml[:m.start()]+E.tostring(row,encoding='utf-8')+xml[m.end():]
    with zipfile.ZipFile(out/'updated_register.xlsx','x') as targetzip:
        for info in z.infolist():targetzip.writestr(copy.copy(info),updated if info.filename=='xl/worksheets/sheet1.xml' else z.read(info.filename))
    with zipfile.ZipFile(out/'updated_register.xlsx') as check:
        assert check.testzip() is None
        assert all(check.read(n)==z.read(n) for n in z.namelist() if n!='xl/worksheets/sheet1.xml')
        assert updated.startswith(xml[:m.start()]) and updated.endswith(xml[m.end():])
nextrow=next(x for x in rows[4:] if x['status']=='NOT_RUN')
review=dict(run_id='HBPSN-04',reviewed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),decision='COMPLETE',validity_status='APPROVED_UNDER_ORIGINAL_FROZEN_PLAN',qualifier='COMPLETE with retained flags, not error-free',operator_statement=statement,plan_sha256=sha(plan),original_rules=prior['exact_original_rules'],criteria_assessment=dict(fixed_window=True,startup=True,first415_selection=True,pre_post_images_hashes=True,settings_match=True,stability_operator_confirmed=True,post_lateness_seconds=184.654217,no_frozen_numeric_lateness_cutoff=True,collector_timeout_not_frozen_cutoff=True,server_error='One new unattributed error retained and flagged under non-reboot connection-error rule; cause unknown, not declared harmless',reboot=False,shortfall=0),automatic_flags_preserved=automatic,original_verification=v,previous_pending_review=str(run/'manual_review_20261106T024832982148Z/manual_review.json'),register_patch=patch,connection_error_count_definition='1 server error plus0 serial connection errors; original serial-only counter0 remains in original automatic statistics',next_scheduled={k:nextrow[k] for k in ['order','run_id','transport','condition','status']},artifact_tool_unavailable='Import failed Module not found @oai/artifact-tool; narrow standard-library OOXML patch preserves every other row and ZIP part')
save('manual_review.json',review)
for dest,staged in [(reg,out/'updated_register.csv'),(xlsx,out/'updated_register.xlsx')]:
    temp=dest.with_name(dest.name+'.HBPSN04_COMPLETE.tmp');assert not temp.exists();temp.write_bytes(staged.read_bytes());os.replace(temp,dest)
save('REGISTERS_UPDATED.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),before_hashes=before,after_hashes={str(p):sha(p) for p in [reg,xlsx]},only_hbpsn04_row_changed=True,next_scheduled=review['next_scheduled']))
report=f'''# HBPSN-04 final manual review — COMPLETE with retained flags

Recorded exact operator response **“yes i know..”**, relayed from ChatGPT. First local receipt clock observation **2026-11-06T12:59:46.7782638Z /14:59:46.7782638 Helsinki**; original chat ingress timestamp unavailable. User explicitly confirmed unchanged Clumsy filter/effects/capture and no Stop/Start or close/reopen throughout the run through the post screenshot. This confirmation is recorded now, not backdated. [Statement](./operator_statement.json).

Original frozen criteria satisfied: startup and2220-second window passed,431 eligible/415 selected/zero shortfall, no subsequent reset/gap/interruption; actual pre/post image hashes verified and settings match CONTROL. Prior missing stability evidence is now supplied by the explicit operator report. **COMPLETE with retained flags**, not a claim of continuous independent GUI observation or an error-free run.

Post-image actual lateness **184.654217seconds** retained. No numeric cutoff exists in the original frozen plan; the collector30-second wait is not one. One new unattributed server `TCP+TLS ERROR:` remains flagged, cause/peer unknown. Original non-reboot error rule requires retaining evidence and eligible samples, not automatic invalidation. Both original automatic FAILED_SETTINGS/MISSING flags and earlier pending decisions remain unchanged in the audit trail. Original serial-only connection error count0 is distinguished from the register's total1 retained server error.

Both registers updated **only HBPSN-04**. Prior register snapshots retained. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with flags, HBPSN-03 FAILED_STARTUP unchanged. QUIC crash unresolved. Raw data, original manifests, plan and firmware untouched.

Next NOT_RUN entry read from the schedule/register: **{nextrow['run_id']} — {nextrow['transport']} — {nextrow['condition']}**, order{nextrow['order']}. [Decision and evidence](./manual_review.json), [register snapshots/update hashes](./REGISTERS_UPDATED.json).
'''
with (out/'REVIEW.md').open('x',encoding='utf-8') as f:f.write(report)
save('SHA256SUMS.json',[dict(path=p.name,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'])
print(json.dumps(dict(decision='COMPLETE_WITH_RETAINED_FLAGS',next_scheduled=review['next_scheduled'],review=str(out/'REVIEW.md')),indent=2))
