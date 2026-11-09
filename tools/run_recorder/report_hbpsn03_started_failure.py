"""Document initial-boot failure; do not operate device or running collector."""
from pathlib import Path
import csv,datetime as dt,hashlib,io,json,re
root=Path(__file__).resolve().parents[2];study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
folder=Path(Path(__file__).with_name('active_hbpsn03_path.txt').read_text().strip())
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(folder/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
start=load(folder/'reset_event.json');gate=load(folder/'startup_checks.json');version=load(folder/'collector_version.json')
assert gate['fatal'] and not gate['pass_all']
text=(folder/'serial.raw.log').read_text(encoding='utf-8',errors='replace');lines=text.splitlines()
receipts=[json.loads(s) for s in (folder/'serial_receipts.jsonl').read_text().splitlines()]
errors=[]
for n,line in enumerate(lines):
    if any(s in line for s in ['Guru Meditation','Rebooting...','ESP-ROM:','rst:','WinError 2']):
        errors.append(dict(source_line=n+1,raw_line=line,host_receipt_utc=receipts[n].get('utc') if n<len(receipts) else None))
assert text.count('ESP-ROM:esp32c6')>=2 and 'Load access fault' in text
preserved=load(folder/'earlier_runs_preservation_before.json')
assert all(sha(x['path'])==x['sha256'] for x in preserved)
save('earlier_runs_preservation_verified.json',dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),original_files_checked=len(preserved),all_unchanged=True,scope='Prior immutable originals; live monitor shutdown added separate exit/control audit files only.'))
boundaries={}
for name,b in start['server_boundaries'].items():
    with Path(b['source']).open('rb') as f:prefix=f.read(b['byte_offset'])
    assert len(prefix)==b['byte_offset']
    (folder/('historical_'+name+'_prefix.snapshot')).write_bytes(prefix)
    boundaries[name]=dict(**b,prefix_sha256=hashlib.sha256(prefix).hexdigest(),anchor_utc=start['reset_release_utc'],historical=True)
save('historical_prefix_boundaries.json',boundaries)
report=dict(run_id='HBPSN-03',status='FAILED_STARTUP',processing_status='RECORDING_ORIGINAL_FIXED_WINDOW',validity_status='NOT_APPROVED',evidence_review_status='PENDING_ACTUAL_POST_IMAGE_AND_OPERATOR_REVIEW',documented_utc=dt.datetime.now(dt.timezone.utc).isoformat(),recording_start_utc=start['reset_release_utc'],fixed_deadline_utc=start['deadline_utc'],start_helsinki=dt.datetime.fromisoformat(start['reset_release_utc']).astimezone(dt.timezone(dt.timedelta(hours=2))).isoformat(),fixed_finish_helsinki=dt.datetime.fromisoformat(start['deadline_utc']).astimezone(dt.timezone(dt.timedelta(hours=2))).isoformat(),failure='Initial boot: QUIC/TLS established and WIFI_PS_NONE verified, then Load access fault panic before MQTT/subscription; spontaneous firmware reboot. No agent retry.',startup_gate=gate,reset_and_tool_errors=errors,subsequent_boot_policy='Retain entire original fixed recording. All post-reboot APP_RTTs excluded from initial-boot first415. Later MQTT success cannot repair the failed initial startup.',collector_version=version,plan_sha256=sha(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),host_activity='Chrome Remote Desktop in use, operator reported; host/AP/load/counters saved in host_hotspot_activity_preflight.json. Brief agent provenance/register work during early recording; no pings/builds/tests.',flash_verification=load(folder/'flash_result.json'),fresh_pre_reset_evidence=load(folder/'pre_run_settings_check.json'),old_verified_image=dict(path=str(folder/'verified_prior_pre_reset.jpg'),sha256=sha(folder/'verified_prior_pre_reset.jpg')),logs={n:str(folder/n) for n in ['serial.raw.log','serial_receipts.jsonl','monitor_stream.log','server.stdout.raw.log','server.stderr.raw.log','server.sensor_csv.raw.log']},automatic_finalization='Repaired v2 collector remains alive; original2220s deadline, no extension. Requests actual post-image and finalizes regardless of missing evidence. It does not itself operate the GUI or approve validity.')
save('STARTUP_FAILURE_REVIEW.json',report)
raw=(study/'run_register.csv').read_bytes();csvlines=raw.splitlines(keepends=True)
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:reader=csv.DictReader(f);headers=reader.fieldnames;rows=list(reader)
assert len(csvlines)==19 and [r['status'] for r in rows[:3]]==['FAILED_SETTINGS','COMPLETE','NOT_RUN']
patch=dict(status='FAILED_STARTUP',preflight_status='PASS',startup_status='FAIL',settings_evidence_type='actual_pre_flash_and_pre_reset_GUI_images; post-image/operator review pending',boot_session_id='HBPSN-03/'+start['reset_release_utc'],reset_release_utc=start['reset_release_utc'],recording_end_utc=start['deadline_utc'],actual_assigned_ip=gate['assigned_ip'],metadata_path=str((folder/'STARTUP_FAILURE_REVIEW.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((folder/'serial.raw.log').relative_to(study)).replace('\\','/'),deviation_reason='Initial boot Load access fault panic before MQTT/subscription; spontaneous reboot. FAILED_STARTUP; original fixed-window recording continues to designated deadline. Post-reboot RTTs excluded; no retry, no Drop change. Validity NOT_APPROVED; actual post-image/operator review pending. Chrome Remote Desktop in use. Monitor panic symbolization missing xtensa-esp32-elf-addr2line retained.')
row=dict(rows[2]);row.update(patch);buf=io.StringIO(newline='');csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n').writerow(row);csvlines[3]=buf.getvalue().encode('utf-8')
staged=folder/'register_started_failure.staged.csv';staged.write_bytes(b''.join(csvlines))
save('register_started_failure_apply_request.json',dict(run_id='HBPSN-03',output_dir=str(folder),csv_staged_path=str(staged),patch=patch))
md=f'''# HBPSN-03 QUIC DROP1_OUT — FAILED_STARTUP

The scheduled measured attempt started **{report['start_helsinki']}**, with fixed deadline **{report['fixed_finish_helsinki']}**, exactly2220 host-monotonic seconds after designated reset release. [Reset anchor](./reset_event.json).

The initial boot verified HOME_BOARD, matching ELF prefix9b23e164f, requested/returned WIFI_PS_NONE(0), IP192.168.137.112, QUIC and TLS1.3/TLS_AES_128_GCM_SHA256/suite0x1301/ALPNmqtt/certificate modeNONE. Before MQTT/subscription it panicked with a Load access fault and rebooted automatically. [Initial startup checks](./startup_checks.json), [failure evidence with receipt timestamps](./STARTUP_FAILURE_REVIEW.json), [raw recording](./serial.raw.log). Cause is not established. The monitor's failed addr2line invocations are retained; no toolchain or firmware changes were made to fix symbolization during recording.

Later MQTT success belongs to the subsequent boot and does not validate the initial boot. Under the frozen rules, retain the original window and exclude all subsequent-boot RTTs from primary selection. No commanded retry/reset, Drop disable or window extension occurred. Recording continues persistently to the original deadline; automatic finalization remains armed with validity NOT_APPROVED and post-recording evidence/operator review pending.

Flash verified all3 matching images. [Flash output](./flash.log), [identification setup reset](./identification_reset.json), [flash result](./flash_result.json). [Firmware/configuration/plan hashes](./preflight.json), [collector runtime hashes](./collector_version.json), [host/hotspot/Chrome Remote Desktop context](./host_hotspot_activity_preflight.json). Hotspot was enabled once using saved configuration; SSID/password hash/band and sharing source preserved.

Actual fresh [pre-reset image](./clumsy_actual_pre_reset.jpg) at {report['fresh_pre_reset_evidence']['evidence']['capture_started_utc']}–{report['fresh_pre_reset_evidence']['evidence']['capture_completed_utc']}, SHA256 {report['fresh_pre_reset_evidence']['evidence']['sha256']}. Exact UDP14567 filter, capture running, only Drop1.0% outbound, inbound unchecked. [Nonce-linked observations](./pre_run_settings_check.json). [Fresh pre-flash image](./clumsy_actual_pre_flash.jpg) separately predates identification/flash resets. Clumsy unchanged.

[Serial receipts](./serial_receipts.jsonl), [complete monitor stream](./monitor_stream.log), [server stdout](./server.stdout.raw.log), [server stderr](./server.stderr.raw.log), [server sensor raw tail](./server.sensor_csv.raw.log). [Historical prefix source boundaries/hashes](./historical_prefix_boundaries.json) isolate setup and earlier server output from this reset. Collector remains running after agent reply. The end-of-run screenshot broker is a request, not an image; actual post-image must be acquired before any settings change and reviewed with the operator confirmation. No evidence may be backdated.

HBPSN-01 FAILED_SETTINGS and HBPSN-02 COMPLETE with retained flags stay unchanged; original files verified. Only HBPSN-03's row is staged as FAILED_STARTUP, with processing continuing. No final RTT statistics or duration claims before deadline.
'''
(folder/'START_STATUS.md').write_text(md,encoding='utf-8')
print(json.dumps(dict(status=report['status'],processing_status=report['processing_status'],start=report['start_helsinki'],deadline=report['fixed_finish_helsinki'],report=str(folder/'START_STATUS.md'),register_request=str(folder/'register_started_failure_apply_request.json')),indent=2))
