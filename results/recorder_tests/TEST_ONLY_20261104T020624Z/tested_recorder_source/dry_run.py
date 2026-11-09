"""60-second TEST_ONLY synthetic recorder; never accesses COM6 or any server."""
import csv,datetime as dt,hashlib,json,os,sys,threading,time
from pathlib import Path
from reliability import Reports,SettingsEvidence,arm_deadline,utc
from test_reliability import windows_share_lock_probe

folder=Path(__file__).with_name('test_output_path.txt').read_text().strip()
folder=Path(folder)
assert folder.parent.name=='recorder_tests' and folder.name.startswith('TEST_ONLY_')
assert not (folder/'test_start.json').exists()
lock_probe=windows_share_lock_probe(folder)
assert lock_probe['winerror']==5 and lock_probe['replacement_after_handle_close']
def failing_replace(source,target):
    if Path(target).name in ('heartbeat.json','optional_report.json'):
        raise PermissionError(13,'TEST_ONLY injected heartbeat/report replacement Access denied')
    os.replace(source,target)
reports=Reports(folder,failing_replace)
expected=dict(filter='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)',capture='RUNNING',effects='all unchecked')
evidence=SettingsEvidence(reports,expected,timeout=180)
pre=evidence.capture('pre_run')
assert pre['status']=='PASS', 'TEST_ONLY requires actual timestamped pre-run GUI evidence'
evidence.timeout=45
start_mono=time.monotonic();start_utc=dt.datetime.now(dt.timezone.utc)
start=dict(test_only=True,source='synthetic records only; no ESP reset',reset_release_monotonic=start_mono,deadline_monotonic=start_mono+60,reset_release_utc=start_utc.isoformat(),deadline_utc=(start_utc+dt.timedelta(seconds=60)).isoformat(),duration_seconds=60)
reports.save('test_start.json',start)
raw=[];accepted=[];rejected=[];data_lock=threading.Lock();finalized=threading.Event()
stream=(folder/'TEST_ONLY_synthetic_stream.jsonl').open('x',buffering=1)
def receive(seq,received=None):
    now=time.monotonic() if received is None else received
    r=dict(test_only=True,synthetic=True,seq=seq,esp_log_uptime_ms=65000+seq*500,app_rtt_ms='67.500',host_monotonic=now,host_receipt_utc=utc())
    with data_lock:
        stream.write(json.dumps(r)+'\n');raw.append(r)
        (accepted if start_mono<=now<start['deadline_monotonic'] else rejected).append(r)
def finalize(anchor,post):
    # Explicitly exercise post-cutoff arrival exclusion. No window extension.
    receive(99999)
    with data_lock:
        selected=list(accepted)
    with (folder/'TEST_ONLY_accepted.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
    reports.save('optional_report.json',dict(test_only=True,will_fail=True))
    result=dict(test_only=True,status='TEST_ONLY_COMPLETE' if post['status']=='PASS' else 'TEST_ONLY_FAILED_SETTINGS',start=anchor,pre_settings=pre,post_settings=post,accepted_count=len(selected),rejected_count=len(rejected),all_accepted_before_deadline=all(start_mono<=r['host_monotonic']<anchor['deadline_monotonic'] for r in selected),late_record_excluded=any(r['seq']==99999 for r in rejected),heartbeat_permission_error_attempts=sum(e.get('target','').endswith('heartbeat.json') for e in reports.errors),report_permission_error_attempts=sum(e.get('target','').endswith('optional_report.json') for e in reports.errors),finalization_utc=utc(),register_touched=False,device_or_settings_changed=False)
    assert result['all_accepted_before_deadline'] and result['late_record_excluded']
    assert result['heartbeat_permission_error_attempts']>=3 and result['report_permission_error_attempts']==3
    assert reports.save('TEST_ONLY_FINALIZED.json',result)
    finalized.set()
stopped,worker=arm_deadline(start,reports,evidence,finalize)
seq=1
while time.monotonic()<start['deadline_monotonic']:
    receive(seq);seq+=1
    reports.save('heartbeat.json',dict(test_only=True,utc=utc(),remaining=max(0,start['deadline_monotonic']-time.monotonic())))
    time.sleep(min(.5,max(0,start['deadline_monotonic']-time.monotonic())))
worker.join(60)
assert finalized.is_set(), 'TEST_ONLY finalizer did not complete'
stream.close()
assert (folder/'recording_cutoff_observed.json').exists()
originals=json.loads((folder/'protected_original_hashes.json').read_text())
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in originals)
reports.save('originals_unchanged.json',dict(test_only=True,checked_utc=utc(),protected_files=len(originals),all_unchanged=True))
print((folder/'TEST_ONLY_FINALIZED.json').read_text())
