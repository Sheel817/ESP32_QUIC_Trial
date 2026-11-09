"""Save provenance and stage only HBPSN-02's RUNNING register row."""
from pathlib import Path
import csv,datetime as dt,hashlib,io,json
root=Path(__file__).resolve().parents[2];study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
folder=Path(Path(__file__).with_name('active_hbpsn02_path.txt').read_text().strip())
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(folder/n).write_text(json.dumps(x,indent=2))
running=load(folder/'RUNNING.json');start=load(folder/'reset_event.json');pf=load(folder/'preflight.json');version=load(folder/'collector_version.json')
assert running['startup']['pass_all']
assert all(sha(Path(x['path']))==x['sha256'] for x in load(folder/'hbpsn01_preservation_before.json'))
boundaries={}
for name,b in start['server_boundaries'].items():
    with Path(b['source']).open('rb') as f:prefix=f.read(b['byte_offset'])
    assert len(prefix)==b['byte_offset']
    (folder/('historical_'+name+'_prefix.snapshot')).write_bytes(prefix)
    boundaries[name]=dict(**b,prefix_sha256=hashlib.sha256(prefix).hexdigest(),prefix_lines=len(prefix.splitlines()),anchor_utc=start['reset_release_utc'],historical=True)
save('historical_prefix_boundaries.json',boundaries)
save('historical_tcp_errors.json',dict(scope='Before designated HBPSN-02 reset only; never attributed to HBPSN-02',errors=(folder/'historical_stderr_prefix.snapshot').read_text().splitlines(),future_errors='Every newly received line is retained in server.stderr.raw.log and its receipt index.'))
reg=study/'run_register.csv';raw=reg.read_bytes();lines=raw.splitlines(keepends=True)
with reg.open(newline='',encoding='utf-8-sig') as f:reader=csv.DictReader(f);headers=reader.fieldnames;rows=list(reader)
assert len(lines)==19 and rows[0]['status']=='FAILED_SETTINGS' and rows[1]['status']=='NOT_RUN'
patch=dict(status='RUNNING',preflight_status='PASS',startup_status='PASS',settings_evidence_type='actual_GUI_pre_reset_image; operator stability review pending',boot_session_id='HBPSN-02/'+start['reset_release_utc'],reset_release_utc=start['reset_release_utc'],recording_end_utc=start['deadline_utc'],actual_assigned_ip=running['startup']['assigned_ip'],metadata_path=str((folder/'metadata.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((folder/'serial.raw.log').relative_to(study)).replace('\\','/'),deviation_reason='Validity NOT_APPROVED; post-recording actual screenshot and operator confirmation require review. Initial old-monitor close helper issue preserved; no measured-start retry.')
target=dict(rows[1]);target.update(patch);text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n');writer.writerow(target)
lines[2]=text.getvalue().encode('utf-8');staged=folder/'register_running.staged.csv';staged.write_bytes(b''.join(lines))
save('register_running_apply_request.json',dict(run_id='HBPSN-02',output_dir=str(folder),csv_staged_path=str(staged),patch=patch))
fresh=load(folder/'pre_run_settings_check.json')['evidence']
report=f'''# HBPSN-02 TCP_TLS LAG100_OUT — RUNNING

Actual measured start **{running['actual_start_helsinki']}**. Fixed finish **{running['deadline_helsinki']}**, exactly 2,220 monotonic seconds after designated reset release. UTC {start['reset_release_utc']}–{start['deadline_utc']}. No extension or automatic measured-start retry.

HOME_BOARD MAC 40:4c:ca:56:bb:b0, COM6, WIFI_PS_NONE, TCP_TLS, configured Lag 100 ms outbound only, all other main effects off. Actual IP **{running['startup']['assigned_ip']}**. Startup gates all PASS: firmware/ELF prefix 1f661a4f7, TLS1.3 / TLS_AES_128_GCM_SHA256 / suite0x1301 / ALPNmqtt / certificate modeNONE, TCP_NODELAY=1, MQTT connection and subscription, requested/returned WIFI_PS_NONE(0). These refer to the new controlled boot, not flash setup boots.

Flash verification PASS for all three matching preserved images; no rebuild or firmware edits. [Flash output](./flash.log), [identification/setup resets](./identification_reset.json), [flash result](./flash_result.json). Setup-only resets precede measurement. Initial close-helper pipe-name query stalled; its helper alone was stopped before any hardware action. Pipe metadata then identified one collector-created client-end write pipe, and the SDK exit command gracefully closed only the old COM6 monitor. This setup issue and the no-command ambiguous-handle guard are preserved; no identification, flash or measured-start failure was retried. Original HBPSN-01 results/status remain unchanged; closing its live monitor added a separate monitor-exit event without rewriting its historical result files.

## Collector and persistent output

Version **{version['version']}**, collector SHA-256 `{version['files'][0]['sha256']}`. Runtime source copied into this attempt before launch; [all runtime hashes](./collector_version.json). Collector PID {running['collector_pid']}; monitor launcher PID {running['monitor_pid']}. It continues after this agent reply. Deadline worker is independent of heartbeat/report writes; bounded report retries and error journal remain active.

- [Serial fixed-window raw log](./serial.raw.log), [serial receipts](./serial_receipts.jsonl), [complete monitor stream](./monitor_stream.log).
- [Server stdout fixed-window log](./server.stdout.raw.log), [server stderr fixed-window log](./server.stderr.raw.log), [server sensor CSV raw tail](./server.sensor_csv.raw.log); matching receipt indexes remain alongside them.
- [Exact reset/start anchor and fresh boundaries](./reset_event.json), [startup checks](./startup_checks.json), [heartbeat](./heartbeat.json), [running metadata](./RUNNING.json), [preflight and firmware/configuration hashes](./preflight.json).

At the actual reset release, new source offsets were captured: stdout **{boundaries['stdout']['byte_offset']}**, stderr **{boundaries['stderr']['byte_offset']}**, sensor CSV **{boundaries['sensor_csv']['byte_offset']}**. Exact source paths, prefix hashes and snapshots are in [historical-prefix provenance](./historical_prefix_boundaries.json). All previous bare TCP errors lie before stderr byte51 and remain historical/unattributed. Every new error line is retained with a host receipt; unidentified peers cannot be inferred merely from an unlabelled error.

## Actual image evidence and validity

The previously verified [pre-reset image copy](./verified_prior_pre_reset.jpg) is preserved unchanged: 2026-11-04T11:59:26.536Z–11:59:26.994Z; SHA-256 7c376f1aeab829828f5687cc3fe2d00cf379315b847bf4e260108e817a453517.

A fresh actual [image](./clumsy_actual_pre_reset.jpg), not a request, was acquired {fresh['capture_started_utc']}–{fresh['capture_completed_utc']}, before this measured reset. SHA-256 **{fresh['sha256']}**. Visually verified exact TCP14568 filter, capture running, Lag enabled100ms, Inbound off, Outbound on, and all seven other main effects off. No Clumsy setting was changed. [Nonce-linked actual-image evidence](./pre_run_settings_check.json).

At the fixed deadline, preserve the whole window; exclude initial-boot ESP log uptime below60,000ms and at/above2,220,000ms; select the first415 eligible APP_RTTs, retain extras/outliers, and report actual shortfalls, resets/gaps/errors. Do not extend recording. Automatic finalization writes CSV/statistics/provenance with validity **NOT_APPROVED / PENDING_MANUAL_REVIEW**. A missing post-run screenshot remains missing, even if a screenshot request exists. An actual post-recording image must be captured before any settings change, and reviewed with the operator's stability confirmation before any positive validity decision. No later evidence is backdated. The collector does not itself operate the GUI; an active read-only observer or operator must supply the actual post image. This status report does not claim a post image already exists.

Frozen plan/order unchanged; HBPSN-01 stays FAILED_SETTINGS. Only HBPSN-02's RUNNING row is staged for synchronized register application. No other tests, pings, builds or setting changes are to occur during recording.
'''
(folder/'RUNNING_STATUS.md').write_text(report,encoding='utf-8')
print(json.dumps(dict(status='RUNNING',start=running['actual_start_helsinki'],fixed_finish=running['deadline_helsinki'],report=str(folder/'RUNNING_STATUS.md'),register_request=str(folder/'register_running_apply_request.json')),indent=2))
