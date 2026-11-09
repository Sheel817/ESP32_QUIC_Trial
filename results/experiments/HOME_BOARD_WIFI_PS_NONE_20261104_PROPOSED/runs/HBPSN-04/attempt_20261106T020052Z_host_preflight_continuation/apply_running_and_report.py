"""Apply reviewed HBPSN-04 RUNNING request only; preserve other register rows."""
from pathlib import Path
import copy,csv,datetime as dt,hashlib,io,json,os,re,zipfile,xml.etree.ElementTree as E
folder=Path(__file__).resolve().parent;study=folder.parents[2];root=study.parents[2]
def load(n):return json.loads((folder/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
    with (folder/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
assert not (folder/'registers_applied_running.json').exists()
running=load('RUNNING.json');start=load('reset_event.json');pf=load('preflight.json');version=load('collector_version.json')
assert running['run_id']=='HBPSN-04' and running['startup']['pass_all']
assert all(sha(x['path'])==x['sha256'] for x in load('earlier_runs_preservation_before.json'))
reg=study/'run_register.csv';xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
assert reg.read_bytes()==(folder/'before_run_register.csv').read_bytes()
assert xlsx.read_bytes()==(folder/'before_run_register.xlsx').read_bytes()
raw=reg.read_bytes();lines=raw.splitlines(keepends=True)
reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));headers=reader.fieldnames;rows=list(reader)
assert len(rows)==18 and [r['status'] for r in rows[:4]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','NOT_RUN']
patch=dict(status='RUNNING',preflight_status='PASS',startup_status='PASS',settings_evidence_type='actual_GUI_pre_reset_image; post-image and operator stability review pending',boot_session_id='HBPSN-04/'+start['reset_release_utc'],reset_release_utc=start['reset_release_utc'],recording_end_utc=start['deadline_utc'],actual_assigned_ip=running['startup']['assigned_ip'],metadata_path=str((folder/'metadata.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((folder/'serial.raw.log').relative_to(study)).replace('\\','/'),deviation_reason='Validity NOT_APPROVED; actual post-recording screenshot and operator confirmation await manual review. Windows listener reporting discrepancy retained; functional host TLS probes passed. Earlier probe errors excluded by measured-start byte boundaries. QUIC crash unresolved.')
target=dict(rows[3]);target.update(patch)
buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n');writer.writerow(target)
assert len(lines)==19;newlines=list(lines);newlines[4]=buf.getvalue().encode()
assert all(newlines[i]==lines[i] for i in range(len(lines)) if i!=4)
staged_csv=folder/'register_running.staged.csv';staged_csv.write_bytes(b''.join(newlines))
ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';q=lambda n:'{'+ns+'}'+n
with zipfile.ZipFile(xlsx) as archive:
    xml=archive.read('xl/worksheets/sheet1.xml')
    match=re.search(rb'<(?:x:)?row\b[^>]*\br="5"[^>]*>.*?</(?:x:)?row>',xml,re.S)
    assert match,'Workbook row5 unavailable'
    row=E.fromstring(b'<root xmlns="'+ns.encode()+b'" xmlns:x="'+ns.encode()+b'">'+match.group()+b'</root>')[0]
    def col(index):
        result=''
        while index:
            index,a=divmod(index-1,26);result=chr(65+a)+result
        return result
    for key,value in patch.items():
        cellid=col(headers.index(key)+1)+'5'
        cell=next((c for c in row if c.get('r')==cellid),None)
        if cell is None:cell=E.SubElement(row,q('c'),{'r':cellid})
        for child in list(cell):cell.remove(child)
        cell.set('t','inlineStr');item=E.SubElement(cell,q('is'));E.SubElement(item,q('t')).text=str(value)
    updated=xml[:match.start()]+E.tostring(row,encoding='utf-8')+xml[match.end():]
    staged_xlsx=folder/'register_running.staged_v2.xlsx'
    with zipfile.ZipFile(staged_xlsx,'x') as target_zip:
        for info in archive.infolist():target_zip.writestr(copy.copy(info),updated if info.filename=='xl/worksheets/sheet1.xml' else archive.read(info.filename))
    with zipfile.ZipFile(staged_xlsx) as check:
        assert all(check.read(n)==archive.read(n) for n in archive.namelist() if n!='xl/worksheets/sheet1.xml')
        assert updated[:match.start()]==xml[:match.start()] and updated.endswith(xml[match.end():])
save('register_running_apply_review.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),run_id='HBPSN-04',patch=patch,only_row4_csv_row5_xlsx_changes=True,validity='NOT_APPROVED',earlier_run_files_unchanged=True))
# Retain staged copies; atomic replacements use separate sibling temporary files.
reg_temp=reg.with_name('run_register.HBPSN04_RUNNING.tmp.csv');xlsx_temp=xlsx.with_name('run_register.HBPSN04_RUNNING.tmp.xlsx')
assert not reg_temp.exists() and not xlsx_temp.exists()
reg_temp.write_bytes(staged_csv.read_bytes());xlsx_temp.write_bytes(staged_xlsx.read_bytes())
os.replace(reg_temp,reg);os.replace(xlsx_temp,xlsx)
save('registers_applied_running.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),run_id='HBPSN-04',status='RUNNING',csv_sha256=sha(reg),xlsx_sha256=sha(xlsx),other_rows_unchanged=True,previous_csv_sha256=sha(folder/'before_run_register.csv'),previous_xlsx_sha256=sha(folder/'before_run_register.xlsx')))
boundaries={}
for name,b in start['server_boundaries'].items():
    with Path(b['source']).open('rb') as f:prefix=f.read(b['byte_offset'])
    assert len(prefix)==b['byte_offset'];(folder/f'historical_{name}_prefix.snapshot').write_bytes(prefix)
    boundaries[name]=dict(**b,prefix_sha256=hashlib.sha256(prefix).hexdigest(),historical=True,measured_start_utc=start['reset_release_utc'])
save('historical_prefix_boundaries.json',boundaries)
save('historical_probe_errors.json',dict(scope='Before measured reset; not attributed to HBPSN-04',lines=(folder/'historical_stderr_prefix.snapshot').read_text().splitlines(),source_probe_results=str(root/'results/diagnostics/HOST_ONLY_TCP14568_20261106T014632766Z/probe_results.json'),new_error_policy='All newly received stderr retained in fixed-window tail with receipt times; never silently discarded.'))
evidence=load('pre_run_settings_check.json')['evidence']
report=f'''# HBPSN-04 TCP_TLS CONTROL — RUNNING

Actual measured start **{running['actual_start_helsinki']}**. Fixed finish **{running['deadline_helsinki']}**, exactly2220 monotonic seconds after reset release. UTC {start['reset_release_utc']}–{start['deadline_utc']}. Host anchor samples SDK reset-release API completion, not a physical-edge measurement.

HOME_BOARD COM6, MAC40:4c:ca:56:bb:b0. Assigned IP **{running['startup']['assigned_ip']}**. All measured startup gates passed: matching formal ELF prefix1f661a4f7, TCP_TLS, TLS1.3 / TLS_AES_128_GCM_SHA256 / suite0x1301 / ALPNmqtt / certificate_verification=NONE(mode0), TCP_NODELAY=1, requested/returned WIFI_PS_NONE(0), MQTT and subscription. Values come from this controlled board startup, not host probes. [Startup checks](./startup_checks.json), [raw serial](./serial.raw.log).

Preserved formal TCP_TLS profile flashed once, all3 image hash verifications passed. No rebuild/source/configuration edit. [Flash log](./flash.log), [formal artifact and config hashes](./preflight.json), [setup reset evidence](./identification_reset.json). Setup-only automatic flash boot excluded; measured recording starts at a separate designated controlled reset. Diagnostic stable outputs preserved, only identified completed loggerPID32104 terminated to release COM6; [preservation](./diagnostic_preservation_after_close.json). Formal TCP_TLS firmware now remains on the board.

Collector **{version['version']}**, SHA256 `{version['files'][0]['sha256']}`, PID{running['collector_pid']}; monitor launcherPID{running['monitor_pid']}. [Version hashes](./collector_version.json), [persistent session](./monitor_session.json), [heartbeat](./heartbeat.json), [reset anchor](./reset_event.json). Independent deadline thread remains active after agent reply. No retry or extension.

Fresh actual [pre-reset screenshot](./clumsy_actual_pre_reset.jpg) captured {evidence['capture_started_utc']}–{evidence['capture_completed_utc']}; SHA256 `{evidence['sha256']}`. Exact TCP14568 filter, capture running, all8 main effects disabled. Inactive saved Lag/Drop values and directions are retained; neither effect enabled. [Nonce-linked evidence](./pre_run_settings_check.json). No Clumsy settings changed.

Server PID36536 remains the verified project .quic-venv process. Successful host-local TCP/TLS checks and READY-after-listen source ordering satisfy functional readiness, with Windows State0/absent-listener reporting discrepancy retained. The frozen plan names no particular Windows readout. All host-probe errors remain historical: [prefix hashes/boundaries](./historical_prefix_boundaries.json), [probe-error separation](./historical_probe_errors.json). Measured reset fresh offsets: stdout{boundaries['stdout']['byte_offset']}, stderr{boundaries['stderr']['byte_offset']}, sensor CSV{boundaries['sensor_csv']['byte_offset']}. Host hotspot ON,2.4GHz,192.168.137.1; Chrome Remote Desktop activity operator-reported. [Environment](./system_preflight.json).

Persistent outputs: [serial raw](./serial.raw.log), [serial receipts](./serial_receipts.jsonl), [monitor stream](./monitor_stream.log), [server stdout](./server.stdout.raw.log), [server stderr](./server.stderr.raw.log), [server sensor CSV tail](./server.sensor_csv.raw.log). Complete raw fixed window retained. Exclude initial-boot ESP log uptime below60000ms or at/above2220000ms; select first415 eligible matched APP_RTTs in arrival order. Retain outliers, errors, reboots, gaps and shortfalls. Never pool subsequent boots or extend window.

At cutoff the collector finalizes even if settings/reporting fails. Validity remains **NOT_APPROVED / PENDING_MANUAL_REVIEW** until an actual post-recording screenshot and operator stability confirmation are reviewed. A screenshot request is not an image. The collector requests end evidence but cannot operate the GUI; missing actual evidence stays flagged. Its30-second response wait is not a frozen lateness cutoff. No automatic positive validity approval.

Only HBPSN-04's RUNNING row was applied to both registers, with prior snapshots preserved. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP unchanged. QUIC crash unresolved. [Register application](./registers_applied_running.json). Frozen plan/order unchanged.
'''
with (folder/'RUNNING_STATUS.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(status='RUNNING',start=running['actual_start_helsinki'],fixed_finish=running['deadline_helsinki'],report=str(folder/'RUNNING_STATUS.md')),indent=2))
