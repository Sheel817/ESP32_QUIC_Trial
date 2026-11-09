"""Apply only HBPSN-06 RUNNING after actual measured startup gates pass."""
from pathlib import Path
import copy,csv,datetime as dt,hashlib,io,json,os,re,zipfile,xml.etree.ElementTree as E
folder=Path(__file__).resolve().parent;study=folder.parents[2];root=study.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads((folder/n).read_text(encoding='utf-8-sig'))
def save(n,x):
    with (folder/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
assert not (folder/'registers_applied_running.json').exists()
running=load('RUNNING.json');start=load('reset_event.json');version=load('collector_version.json');assert running['run_id']=='HBPSN-06' and running['startup']['pass_all']
assert all(sha(x['path'])==x['sha256'] for x in load('earlier_runs_preservation_before.json'))
reg=study/'run_register.csv';xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
assert reg.read_bytes()==(folder/'before_run_register.csv').read_bytes() and xlsx.read_bytes()==(folder/'before_run_register.xlsx').read_bytes()
raw=reg.read_bytes();lines=raw.splitlines(keepends=True);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));headers=reader.fieldnames;rows=list(reader)
assert len(lines)==19 and [x['status'] for x in rows[:6]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','COMPLETE','NOT_RUN']
patch=dict(status='RUNNING',preflight_status='PASS',startup_status='PASS',settings_evidence_type='actual_GUI_pre_reset_image; post-recording and NEW HBPSN-06-specific operator review pending',boot_session_id='HBPSN-06/'+start['reset_release_utc'],reset_release_utc=start['reset_release_utc'],recording_end_utc=start['deadline_utc'],actual_assigned_ip=running['startup']['assigned_ip'],metadata_path=str((folder/'metadata.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((folder/'serial.raw.log').relative_to(study)).replace('\\','/'),deviation_reason='Validity NOT_APPROVED pending actual post-recording screenshot and operator review; earlier QUIC crash unresolved; no measured-start retry or extension.')
target=dict(rows[5]);target.update(patch);s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n');w.writerow(target)
updated_lines=list(lines);updated_lines[6]=s.getvalue().encode();assert all(updated_lines[i]==lines[i] for i in range(19) if i!=6)
(folder/'register_running.staged.csv').write_bytes(b''.join(updated_lines))
ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';q=lambda x:'{'+ns+'}'+x
def col(n):
    s=''
    while n:n,a=divmod(n-1,26);s=chr(65+a)+s
    return s
with zipfile.ZipFile(xlsx) as z:
    xml=z.read('xl/worksheets/sheet1.xml');m=re.search(rb'<(?:\w+:)?row\b[^>]*\br="7"[^>]*>.*?</(?:\w+:)?row>',xml,re.S);assert m
    row=E.fromstring(b'<root xmlns="'+ns.encode()+b'" xmlns:x="'+ns.encode()+b'" xmlns:ns0="'+ns.encode()+b'">'+m.group()+b'</root>')[0]
    for k,value in patch.items():
        ref=col(headers.index(k)+1)+'7';c=next((c for c in row if c.get('r')==ref),None)
        if c is None:c=E.SubElement(row,q('c'),{'r':ref})
        for child in list(c):c.remove(child)
        c.set('t','inlineStr');E.SubElement(E.SubElement(c,q('is')),q('t')).text=str(value)
    updated=xml[:m.start()]+E.tostring(row,encoding='utf-8')+xml[m.end():]
    with zipfile.ZipFile(folder/'register_running.staged.xlsx','x') as targetzip:
        for info in z.infolist():targetzip.writestr(copy.copy(info),updated if info.filename=='xl/worksheets/sheet1.xml' else z.read(info.filename))
    with zipfile.ZipFile(folder/'register_running.staged.xlsx') as check:
        assert check.testzip() is None and all(check.read(n)==z.read(n) for n in z.namelist() if n!='xl/worksheets/sheet1.xml')
before={str(p):sha(p) for p in [reg,xlsx]}
save('register_running_review.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),patch=patch,only_hbpsn06_row_changed=True,validity_status='NOT_APPROVED'))
for dest,staged in [(reg,folder/'register_running.staged.csv'),(xlsx,folder/'register_running.staged.xlsx')]:
    temp=dest.with_name(dest.name+'.HBPSN06_RUNNING.tmp');assert not temp.exists();temp.write_bytes(staged.read_bytes());os.replace(temp,dest)
save('registers_applied_running.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),before_hashes=before,after_hashes={str(p):sha(p) for p in [reg,xlsx]},only_hbpsn06_row_changed=True))
boundaries={}
for name,b in start['server_boundaries'].items():
    with Path(b['source']).open('rb') as f:prefix=f.read(b['byte_offset'])
    assert len(prefix)==b['byte_offset'];(folder/f'historical_{name}_prefix.snapshot').write_bytes(prefix)
    boundaries[name]=dict(**b,prefix_sha256=hashlib.sha256(prefix).hexdigest(),historical=True,anchor_utc=start['reset_release_utc'])
save('historical_prefix_boundaries.json',boundaries)
evidence=load('pre_run_settings_check.json')['evidence']
report=f'''# HBPSN-06 TCP_TLS DROP1_OUT — RUNNING

Actual measured start **{running['actual_start_helsinki']}**. Fixed finish **{running['deadline_helsinki']}**, exactly2220 monotonic seconds from controlled-reset release. UTC {start['reset_release_utc']}–{start['deadline_utc']}. Host API completion anchor, not a measured electrical edge. No retry or extension.

HOME_BOARD COM6 / MAC40:4c:ca:56:bb:b0, actual IP **{running['startup']['assigned_ip']}**. Preserved formal TCP_TLS WIFI_PS_NONE applicationff97eb5d20c9c47375539395f9cf23c1d0780381562cf511094d4b525ab17de8; matching ELF1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6. All3 flashed image verifications passed. No rebuild, source or application-setting edit. [Flash](./flash.log), [preflight/hash provenance](./preflight.json), [setup resets](./identification_reset.json).

This measured startup independently passed TCP_TLS/MQTT and TCP_NODELAY=1, connection and subscription, matching ELF prefix, explicit requested/returned WIFI_PS_NONE(0), TLS1.3 / TLS_AES_128_GCM_SHA256 / suite0x1301 / ALPNmqtt / certificate verification NONE(mode0). [Startup checks](./startup_checks.json). Formal TCP_TLS firmware remains on board. Unresolved earlier QUIC crash remains documented; this passing startup does not establish a fix.

Fresh actual [pre-reset image](./clumsy_actual_pre_reset.jpg) captured {evidence['capture_started_utc']}–{evidence['capture_completed_utc']}, SHA256 `{evidence['sha256']}`. Exact `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`; capture running; only Drop1.0% enabled, outbound checked, inbound unchecked, all other main effects off. Configured impairment is not a per-packet latency claim. [Nonce-linked image evidence](./pre_run_settings_check.json).

Persistent collector **{version['version']}**, SHA256 `{version['files'][0]['sha256']}`, PID{running['collector_pid']}; monitorPID{running['monitor_pid']}. [Version](./collector_version.json), [heartbeat](./heartbeat.json), [reset anchor](./reset_event.json). Independent deadline worker finalizes after the agent reply; heartbeat/report failures do not extend the window. A post-deadline image request is not an actual image; absence remains flagged. Collector cannot operate the GUI, so post-image requires an active observer/operator.

Live output: [fixed-window serial](./serial.raw.log), [serial receipts](./serial_receipts.jsonl), [server stdout](./server.stdout.raw.log), [stderr](./server.stderr.raw.log), [sensor CSV tail](./server.sensor_csv.raw.log). At measured release fresh source offsets were stdout{boundaries['stdout']['byte_offset']}, stderr{boundaries['stderr']['byte_offset']}, sensor CSV{boundaries['sensor_csv']['byte_offset']}. Historical bytes/errors kept separately in [prefix snapshots and hashes](./historical_prefix_boundaries.json). Host-only probe results and probe boundaries are saved separately before measured-start offsets. Windows listener-reporting discrepancy retained; actual measured board startup verified independently. Actual environment/hotspot/server processes: [preflight](./system_preflight.json). Chrome Remote Desktop usage operator-reported.

Retain entire37minutes; initial measured boot only, exclude ESP log uptime below60000ms and at/above2220000ms, select first415 eligible matched RTTs in arrival order. Preserve extras/outliers/errors/resets/gaps and report shortfalls. Do not extend or pool subsequent boots.

Final validity **NOT_APPROVED / PENDING_MANUAL_REVIEW** until actual post-recording screenshot and NEW HBPSN-06-specific operator stability review. Collector30-second evidence wait is not a frozen lateness cutoff. Only HBPSN-06 RUNNING row changed in both registers. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with flags, HBPSN-03 FAILED_STARTUP, HBPSN-04 COMPLETE with flags and HBPSN-05 COMPLETE with flags remain unchanged. No further run before review. [Register audit](./registers_applied_running.json).
'''
with (folder/'RUNNING_STATUS.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(status='RUNNING',start=running['actual_start_helsinki'],finish=running['deadline_helsinki'],report=str(folder/'RUNNING_STATUS.md')),indent=2))
