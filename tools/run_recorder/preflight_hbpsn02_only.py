"""Read-only HBPSN-02 preparation. No serial/network probe, reset or recording."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,socket,ssl,subprocess,sys,time

root=Path(__file__).resolve().parents[2]
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
out=root/'results/preflights'/('HBPSN02_PREFLIGHT_ONLY_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(parents=True,exist_ok=False)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(out/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
protected=[p for p in (study/'runs/HBPSN-01').rglob('*') if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts]
protected += [study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'freeze_manifest.json',study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx']
save('protected_original_hashes.json',[dict(path=str(p),sha256=sha(p)) for p in protected])
manifest=json.loads((study/'freeze_manifest.json').read_text())
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
assert rows[0]['status']=='FAILED_SETTINGS'
assert [rows[1][k] for k in ('run_id','transport','condition','status')]==['HBPSN-02','TCP_TLS','LAG100_OUT','NOT_RUN']
assert [(r['run_id'],r['transport'],r['condition']) for r in rows]==[(r['run_id'],r['transport'],r['condition']) for r in manifest['schedule']]
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md'
assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
profile=root/'profiles/tcp_tls_wifi_ps_none_20261104'
validation=json.loads((profile/'validation.json').read_text())
artifacts=[]
for expected in manifest['artifacts']:
    if expected['transport']!='TCP_TLS':continue
    p=Path(expected['path']);actual=sha(p)
    artifacts.append(dict(path=str(p),bytes=p.stat().st_size,sha256=actual,expected_sha256=expected['sha256'],matches=actual==expected['sha256']))
assert all(r['matches'] for r in artifacts)
flash_checks=[]
for name in ['flash_args','flasher_args.json']:
    expected=validation['artifacts'][name]
    p=profile/'build'/name
    flash_checks.append(dict(path=str(p),sha256=sha(p),matches=sha(p)==expected['sha256']))
assert all(r['matches'] for r in flash_checks)
cache=(profile/'build/CMakeCache.txt').read_text()
assert 'DEMO_TRANSPORT:STRING=TCP_TLS' in cache and 'DEMO_WIFI_PS_NONE:BOOL=ON' in cache
config=json.loads((profile/'build/config/sdkconfig.json').read_text())
quicconfig=json.loads((root/'profiles/wifi_ps_none_20261103/build/config/sdkconfig.json').read_text())
assert config==quicconfig
source_expected=json.loads((profile/'source_before.json').read_text())
source_checks=[]
for name in ['tcp_tls_server.py','quic_server.py','server-cert.pem','dependencies.lock']:
    source_checks.append(dict(path=str(root/name),sha256=sha(root/name),expected_sha256=source_expected.get(name),matches=sha(root/name)==source_expected.get(name)))
assert all(r['matches'] for r in source_checks)
sys.path.insert(0,str(root))
import tcp_tls_server
context=tcp_tls_server.tls_context(root)  # Local config/key load only: no socket opened.
assert context.minimum_version==context.maximum_version==ssl.TLSVersion.TLSv1_3
assert 'TLS_AES_128_GCM_SHA256' in [r['name'] for r in context.get_ciphers()]
tls=dict(checked_utc=utc(),context_load='PASS',minimum_version=context.minimum_version.name,maximum_version=context.maximum_version.name,aes128_gcm_available=True,alpn_configured_from_source='mqtt',certificate_sha256=sha(root/'server-cert.pem'),note='Disk context/cert/key load; separate local TLS-only preflight probe below. No board/MQTT test or negotiated run-session claim.')
ps="""$ErrorActionPreference='Stop'; $listener=@(Get-NetTCPConnection -LocalPort 14568 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,State,OwningProcess); $processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'python' -and $_.CommandLine -match 'tcp_tls_server.py'} | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine); @{checked_utc=[DateTime]::UtcNow.ToString('o');listeners=$listener;processes=$processes} | ConvertTo-Json -Depth 5"""
probe=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True,timeout=30)
assert probe.returncode==0,probe.stderr
system=json.loads(probe.stdout)
assert len(system['listeners'])==1
owner=system['listeners'][0]['OwningProcess']
process=next(r for r in system['processes'] if r['ProcessId']==owner)
assert str(root/'.quic-venv/Scripts/python.exe').lower().replace('\\','/') in process['CommandLine'].lower().replace('\\','/')
assert any(r['ProcessId']==process['ParentProcessId'] and '.quic-venv' in r['ExecutablePath'] for r in system['processes'])
smoke=root/'results/pilots/HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_20261104T000343Z'
sources=dict(stdout=smoke/'tcp_tls_server.stdout.log',stderr=smoke/'tcp_tls_server.stderr.log',sensor_csv=root/'logs/sensor_tcp_tls_20261104T000344_550740Z_xly3omnb.csv')
probe_start_offsets={n:p.stat().st_size for n,p in sources.items()}
client=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client.check_hostname=False;client.verify_mode=ssl.CERT_NONE  # Existing experiment's mode; not a server setting change.
client.minimum_version=client.maximum_version=ssl.TLSVersion.TLSv1_3
client.set_alpn_protocols(['mqtt'])
probe_started=utc()
with socket.create_connection(('127.0.0.1',14568),timeout=5) as raw:
    with client.wrap_socket(raw,server_hostname='localhost') as secure:
        negotiated=dict(tls=secure.version(),cipher=secure.cipher(),alpn=secure.selected_alpn_protocol(),peer_certificate_der_sha256=hashlib.sha256(secure.getpeercert(binary_form=True)).hexdigest())
        assert negotiated['tls']=='TLSv1.3' and negotiated['alpn']=='mqtt'
        assert negotiated['peer_certificate_der_sha256']==hashlib.sha256(ssl.PEM_cert_to_DER_cert((root/'server-cert.pem').read_text())).hexdigest()
tls['local_tls_only_probe']=dict(started_utc=probe_started,completed_utc=utc(),endpoint='127.0.0.1:14568',negotiated=negotiated,source_offsets_before_probe=probe_start_offsets,purpose='Preflight only; no MQTT/sensor publication; not ESP startup or HBPSN-02 run traffic',pass_all=True)
tls['passive_state_limitation']='State-filtered Get-NetTCPConnection and netstat did not reliably expose LISTENING; PID/port association plus successful current TLS handshake establish readiness.'
time.sleep(.25)  # Allow this preflight connection's existing server logging to flush before EOF snapshot.
boundaries={}
for name,p in sources.items():
    first=utc()
    with p.open('rb') as f:
        end=f.seek(0,2);f.seek(0);prefix=f.read(end)
    last=utc()
    assert len(prefix)==end
    (out/(name+'_existing_prefix.snapshot')).write_bytes(prefix)
    boundaries[name]=dict(source=str(p),boundary_observed_utc_start=first,boundary_observed_utc_end=last,next_byte_offset=end,prefix_sha256=hashlib.sha256(prefix).hexdigest(),prefix_line_count=len(prefix.splitlines()),ends_at_line_boundary=not prefix or prefix.endswith(b'\n'),source_modified_utc=dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),scope='Preflight-only EOF boundary; not a recording-start anchor. Re-snapshot at later authorized measured reset.')
stderr=(out/'stderr_existing_prefix.snapshot').read_text()
historical_errors=[dict(line=n,raw_line=line,attribution='historical/unattributed; before HBPSN-02 preflight boundary') for n,line in enumerate(stderr.splitlines(),1) if 'TCP+TLS ERROR:' in line]
save('server_log_boundaries.json',boundaries)
save('historical_tcp_error_ledger.json',historical_errors)
save('server_readiness.json',dict(status='PASS_READ_ONLY',system=system,tls=tls,source_checks=source_checks,server_log_boundaries=boundaries,historical_unattributed_error_count=len(historical_errors),attribution_limit='Existing log lines have no peer/session/timestamp. Byte and receipt-time separation prevents mixing historical lines into a later run, but does not by itself identify the peer responsible for future bare errors.'))
save('image_verification.json',dict(status='PASS',artifacts=artifacts,flash_argument_files=flash_checks,transport='TCP_TLS',wifi_ps_none_build=True,effective_sdkconfig_matches_quic=True,build_report_result=validation['result'],plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),on_device_state='Not verified/changed in this preflight. Current monitor/board is not claimed to be TCP_TLS. New measured startup readback remains required.'))
save('preflight_scope.json',dict(run_id='HBPSN-02',phase='PREFLIGHT_ONLY',recording_started=False,register_status='NOT_RUN',transport='TCP_TLS',condition='LAG100_OUT',required_settings=dict(filter='tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)',capture='RUNNING',Lag=dict(enabled=True,delay_ms=100,inbound=False,outbound=True),other_main_effects={x:False for x in ['Drop','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']}),actual_pre_reset_screenshot='Required fresh at later authorized startup; not yet captured for the measured boot. Preflight observation is not substituted.',final_validity='NOT_APPROVED; PENDING_EVIDENCE_REVIEW until actual pre/post screenshots and operator confirmation are reviewed',observer_readiness='Separate active read-only observer required; unattended 37-minute observer lifetime not demonstrated.'))
Path(__file__).with_name('hbpsn02_preflight_output.txt').write_text(str(out))
assert all(sha(Path(row['path']))==row['sha256'] for row in json.loads((out/'protected_original_hashes.json').read_text()))
save('preservation_verification.json',dict(checked_utc=utc(),protected_files=len(protected),all_unchanged=True,hbpsn01_status='FAILED_SETTINGS',hbpsn02_status='NOT_RUN',frozen_order_unchanged=True))
print(json.dumps(dict(output=str(out),image='PASS',server_listener_owner=owner,boundaries=boundaries,historical_errors=len(historical_errors)),indent=2))
