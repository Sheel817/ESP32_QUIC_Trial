"""Authorized HBPSN-02 setup only: verify, close exact monitor, identify and flash once."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,os,shutil,subprocess,sys,time,traceback
from graceful_monitor_exit import send_exit

root=Path(__file__).resolve().parents[2];study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
folder=study/'runs/HBPSN-02'/('attempt_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(parents=True,exist_ok=False)
tools=Path(__file__).resolve().parent
(tools/'active_hbpsn02_path.txt').write_text(str(folder))
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(folder/name).write_text(json.dumps(x,indent=2),encoding='utf-8')
idfpython=Path('C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe')
profile=root/'profiles/tcp_tls_wifi_ps_none_20261104';build=profile/'build'
old=study/'runs/HBPSN-01/attempt_20261104T002840Z'
try:
    plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';manifest=json.loads((study/'freeze_manifest.json').read_text())
    assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
    rows=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
    assert rows[0]['status']=='FAILED_SETTINGS'
    assert [rows[1][k] for k in ('run_id','transport','condition','status')]==['HBPSN-02','TCP_TLS','LAG100_OUT','NOT_RUN']
    protected=[p for p in (study/'runs/HBPSN-01').rglob('*') if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts]
    save('hbpsn01_preservation_before.json',[dict(path=str(p),sha256=sha(p)) for p in protected])
    shutil.copy2(study/'run_register.csv',folder/'before_run_register.csv')
    shutil.copy2(root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',folder/'before_run_register.xlsx')
    artifacts=[x for x in manifest['artifacts'] if x['transport']=='TCP_TLS']
    assert all(sha(Path(x['path']))==x['sha256'] for x in artifacts)
    validation=json.loads((profile/'validation.json').read_text())
    for name in ['flash_args','flasher_args.json']:assert sha(build/name)==validation['artifacts'][name]['sha256']
    original_image=root/'results/preflights/HBPSN02_PRE_RESET_20261104T115926536Z/HBPSN-02_Clumsy_PRE_RESET.jpg'
    assert sha(original_image)=='7c376f1aeab829828f5687cc3fe2d00cf379315b847bf4e260108e817a453517'
    shutil.copy2(original_image,folder/'verified_prior_pre_reset.jpg')
    shutil.copy2(original_image.parent/'capture_metadata.json',folder/'verified_prior_pre_reset_metadata.json')
    configpaths=[profile/'sdkconfig',build/'config/sdkconfig.json',build/'CMakeCache.txt',build/'flash_args',build/'flasher_args.json',root/'dependencies.lock',root/'tcp_tls_server.py',root/'quic_server.py',root/'server-cert.pem']
    smoke=root/'results/pilots/HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_20261104T000343Z'
    server_sources=dict(stdout=str(smoke/'tcp_tls_server.stdout.log'),stderr=str(smoke/'tcp_tls_server.stderr.log'),sensor_csv=str(root/'logs/sensor_tcp_tls_20261104T000344_550740Z_xly3omnb.csv'))
    expected=dict(filter='tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)',capture='RUNNING',Lag=dict(enabled=True,delay_ms=100,inbound=False,outbound=True),other_main_effects={n:False for n in ['Drop','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']})
    preflight=dict(status='PASS',run_id='HBPSN-02',transport='TCP_TLS',condition='LAG100_OUT',checked_utc=utc(),plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),firmware_artifacts=artifacts,configuration=[dict(path=str(p),sha256=sha(p)) for p in configpaths],server_log_sources=server_sources,server_sensor_source=server_sources['sensor_csv'],expected_clumsy_settings=expected,prior_verified_pre_reset=dict(source=str(original_image),sha256=sha(original_image),capture_started_utc='2026-11-04T11:59:26.536Z',capture_completed_utc='2026-11-04T11:59:26.994Z'),observer_policy='Fresh actual pre-run image required by broker; end image/operator statement must be reviewed. Missing end image remains flagged, never a fabricated PASS.',validity_status='NOT_APPROVED')
    save('preflight.json',preflight)
    for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']:shutil.copy2(tools/n,folder/n)
    save('collector_version.json',dict(version='repaired-v2-manual-review-gate',files=[dict(path=n,sha256=sha(folder/n)) for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']]))
    print(json.dumps(dict(stage='READY_TO_CLOSE_OLD_MONITOR',folder=str(folder))),flush=True)
    process_script="Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -in 33972,26296,26228,36520} | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Depth 3"
    p=subprocess.run(['powershell','-NoProfile','-Command',process_script],capture_output=True,text=True,timeout=30)
    processes=json.loads(p.stdout);save('processes_before_setup.json',processes)
    monitor=next(x for x in processes if x['ProcessId']==26296)
    assert monitor['ParentProcessId']==1776 and '--port COM6' in monitor['CommandLine'] and 'HBPSN-01' in monitor['CommandLine']
    assert any(x['ProcessId']==26228 and '.quic-venv' in x['CommandLine'] and 'tcp_tls_server.py' in x['CommandLine'] for x in processes)
    closed=send_exit(33972,26296);closed['command_sent_utc']=utc();save('previous_monitor_close_request.json',closed)
    for _ in range(40):
        check=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process -Id 26296,1776 -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True,timeout=10)
        if check.stdout.strip()=='0':break
        time.sleep(.25)
    else:raise RuntimeError('Only targeted old monitor did not exit; no force kill or flash retry')
    save('previous_monitor_closed.json',dict(closed_utc=utc(),method=closed,old_monitor_exit_record=str(old/'monitor_exit.json')))
    env=os.environ.copy();env['PYTHONUTF8']='1'
    identify=[str(idfpython),'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','flash-id']
    started=utc();p=subprocess.run(identify,cwd=build,env=env,capture_output=True,text=True,timeout=40)
    (folder/'identification.log').write_text(p.stdout+p.stderr,encoding='utf-16')
    save('identification_reset.json',dict(started_utc=started,completed_utc=utc(),command=identify,exit_code=p.returncode,setup_only=True,reset_note='Espressif default-reset into ROM; after=no-reset. Outside designated measurement window.'))
    assert p.returncode==0 and '40:4c:ca:56:bb:b0' in p.stdout and 'ESP32-C6' in p.stdout and '8MB' in p.stdout,'Identification failed; no retry/flash'
    args=json.loads((build/'flasher_args.json').read_text());extra=args['extra_esptool_args']
    command=[str(idfpython),'-m','esptool','--chip',extra['chip'],'--port','COM6','--baud','460800','--before',extra['before'],'--after',extra['after'],'write-flash','@flash_args']
    started=utc();save('flash_started.json',dict(started_utc=started,command=command,cwd=str(build),setup_only=True))
    print(json.dumps(dict(stage='FLASHING_ONCE',started_utc=started)),flush=True)
    p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180)
    (folder/'flash.log').write_text(' '.join(command)+'\n'+p.stdout+p.stderr,encoding='utf-16')
    save('flash_result.json',dict(exit_code=p.returncode,ended_utc=utc(),artifact_directory=str(build),setup_only='Flash resets precede designated controlled startup',verified_image_count=p.stdout.count('Hash of data verified.')))
    assert p.returncode==0 and p.stdout.count('Hash of data verified.')==3,'Flash failed; no automatic retry'
    assert all(sha(Path(x['path']))==x['sha256'] for x in artifacts)
    assert all(sha(Path(x['path']))==x['sha256'] for x in json.loads((folder/'hbpsn01_preservation_before.json').read_text()))
    save('setup_complete.json',dict(utc=utc(),flash_verification='PASS_3_OF_3',identified_home_board=True,hbpsn01_original_files_unchanged=True,designated_start_not_yet_issued=True))
    print(json.dumps(dict(stage='FLASH_VERIFIED_READY_FOR_COLLECTOR',folder=str(folder))),flush=True)
except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),traceback=traceback.format_exc(),automatic_retry=False))
    raise
