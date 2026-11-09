"""One authorized HBPSN-03 setup. Never retries identification, flash or reset."""
from pathlib import Path
import csv, datetime as dt, hashlib, json, os, shutil, subprocess, time, traceback

root=Path(__file__).resolve().parents[2]
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
tools=Path(__file__).resolve().parent
folder=study/'runs/HBPSN-03'/('attempt_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(parents=True,exist_ok=False)
(tools/'active_hbpsn03_path.txt').write_text(str(folder))
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(folder/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def ps(s):
    p=subprocess.run(['powershell','-NoProfile','-Command',s],capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout)
try:
    plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md'
    assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
    rows=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
    assert [r['status'] for r in rows[:3]]==['FAILED_SETTINGS','COMPLETE','NOT_RUN']
    assert [rows[2][k] for k in ('run_id','transport','condition')]==['HBPSN-03','QUIC','DROP1_OUT']
    old=study/'runs/HBPSN-02/attempt_20261104T121332Z'
    assert json.loads((old/'FINALIZED.json').read_text())['processing_status']=='FINALIZED'
    protected=[]
    for rid in ['HBPSN-01','HBPSN-02']:
        for p in (study/'runs'/rid).rglob('*'):
            if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts:
                protected.append(dict(path=str(p),sha256=sha(p)))
    save('earlier_runs_preservation_before.json',protected)
    shutil.copy2(study/'run_register.csv',folder/'before_run_register.csv')
    shutil.copy2(root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',folder/'before_run_register.xlsx')
    manifest=json.loads((study/'freeze_manifest.json').read_text())
    artifacts=[x for x in manifest['artifacts'] if x['transport']=='QUIC']
    assert len(artifacts)==4 and all(sha(x['path'])==x['sha256'] for x in artifacts)
    prior=json.loads((study/'runs/HBPSN-01/attempt_20261104T002840Z/preflight.json').read_text())
    assert all(sha(x['path'])==x['sha256'] for x in prior['configuration'])
    prior_image=root/'results/preflights/HBPSN03_PRE_RESET_20261104T134654170Z/HBPSN-03_Clumsy_PRE_RESET.jpg'
    assert sha(prior_image)=='6f476841c8d10f8d2ef12d03a4fcd276097ec894f4a0dc801a2e140d70186142'
    shutil.copy2(prior_image,folder/'verified_prior_pre_reset.jpg')
    shutil.copy2(prior_image.parent/'capture_metadata.json',folder/'verified_prior_pre_reset_metadata.json')
    system=ps("@{utc=[DateTime]::UtcNow.ToString('o');port=@(Get-CimInstance Win32_SerialPort | Where-Object DeviceID -eq 'COM6');listener=@(Get-NetUDPEndpoint -LocalPort 14567);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -in 23100,35072,30024,33192});wifi=(netsh wlan show interfaces)} | ConvertTo-Json -Depth 5")
    save('system_preflight.json',system)
    assert len(system['port'])==1 and 'FABA8DF9808FED11A981E817B96CE6F8' in system['port'][0]['PNPDeviceID']
    assert any(x['OwningProcess']==23100 for x in system['listener'])
    processes=system['processes']
    assert any(x['ProcessId']==23100 and 'quic_server.py' in x['CommandLine'] and '.quic-venv' in x['CommandLine'] for x in processes)
    assert any(x['ProcessId']==30024 and x['ParentProcessId']==35072 and '--port COM6' in x['CommandLine'] and 'HBPSN-02' in x['CommandLine'] for x in processes)
    sources=dict(prior['server_log_sources'],sensor_csv=prior['server_sensor_source'])
    assert all(Path(p).exists() for p in sources.values())
    expected=dict(filter='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)',capture='RUNNING',Drop=dict(enabled=True,chance_percent=1.0,inbound=False,outbound=True),other_main_effects={n:False for n in ['Lag','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']})
    save('preflight.json',dict(status='PASS',checked_utc=utc(),run_id='HBPSN-03',transport='QUIC',condition='DROP1_OUT',protocol_id=manifest['protocol_id'],plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),firmware_artifacts=artifacts,configuration=prior['configuration'],server_log_sources=sources,server_sensor_source=prior['server_sensor_source'],expected_clumsy_settings=expected,prior_verified_pre_reset=dict(source=str(prior_image),sha256=sha(prior_image),capture_started_utc='2026-11-04T13:46:54.170Z',capture_completed_utc='2026-11-04T13:46:54.650Z'),validity_status='NOT_APPROVED',observer_policy='Fresh nonce-linked actual pre-reset image; actual post-recording image and operator confirmation require review. Missing evidence stays flagged. No scientific validity auto-approval.',clumsy_executable_sha256=sha('C:/Users/newsh/Downloads/clumsy-0.3-win64-a/clumsy.exe')))
    for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']:shutil.copy2(tools/n,folder/n)
    save('collector_version.json',dict(version='repaired-v2-manual-review-gate',files=[dict(path=n,sha256=sha(folder/n)) for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']]))
    # The existing collector provides a graceful SDK monitor-exit channel.
    (old/'monitor_control.txt').write_text('exit\n')
    save('previous_monitor_close_request.json',dict(utc=utc(),target_collector_pid=35072,target_monitor_pids=[30024,33192],method='Existing collector control file -> SDK monitor exit; no force kill'))
    for _ in range(30):
        remaining=ps('@(Get-Process -Id 30024,33192 -ErrorAction SilentlyContinue).Count | ConvertTo-Json')
        if remaining==0:break
        time.sleep(.2)
    else:raise RuntimeError('Previous COM6 monitor did not exit; no flash or forced termination')
    save('previous_monitor_closed.json',dict(utc=utc(),remaining_monitor_processes=0))
    build=root/'profiles/wifi_ps_none_20261103/build'
    python='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
    env=os.environ.copy();env['PYTHONUTF8']='1'
    command=[python,'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','flash-id']
    started=utc();p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=40)
    (folder/'identification.log').write_text(p.stdout+p.stderr,encoding='utf-16')
    save('identification_reset.json',dict(started_utc=started,completed_utc=utc(),command=command,exit_code=p.returncode,setup_only=True,reset_note='Default-reset into ROM; after=no-reset. Outside formal window.'))
    assert p.returncode==0 and '40:4c:ca:56:bb:b0' in p.stdout and 'ESP32-C6' in p.stdout and '8MB' in p.stdout,'Identification failed; no retry'
    a=json.loads((build/'flasher_args.json').read_text())['extra_esptool_args']
    command=[python,'-m','esptool','--chip',a['chip'],'--port','COM6','--baud','460800','--before',a['before'],'--after',a['after'],'write-flash','@flash_args']
    save('flash_started.json',dict(started_utc=utc(),command=command,cwd=str(build),setup_only=True))
    print(json.dumps(dict(stage='FLASHING_ONCE',folder=str(folder))),flush=True)
    p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180)
    (folder/'flash.log').write_text(' '.join(command)+'\n'+p.stdout+p.stderr,encoding='utf-16')
    save('flash_result.json',dict(exit_code=p.returncode,ended_utc=utc(),artifact_directory=str(build),verified_image_count=p.stdout.count('Hash of data verified.'),setup_only=True))
    assert p.returncode==0 and p.stdout.count('Hash of data verified.')==3,'Flash failed; no retry'
    assert all(sha(x['path'])==x['sha256'] for x in artifacts)
    assert all(sha(x['path'])==x['sha256'] for x in protected),'Earlier frozen result file changed'
    save('setup_complete.json',dict(utc=utc(),flash_verification='PASS_3_OF_3',identified_home_board=True,earlier_original_files_unchanged=True,designated_start_not_yet_issued=True))
    print(json.dumps(dict(stage='FLASH_VERIFIED_READY_FOR_COLLECTOR',folder=str(folder))),flush=True)
except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),traceback=traceback.format_exc(),automatic_retry=False))
    raise
