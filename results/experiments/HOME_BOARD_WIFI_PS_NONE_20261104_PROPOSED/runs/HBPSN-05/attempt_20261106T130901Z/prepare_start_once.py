"""One authorized scheduled HBPSN-05 setup. No silent retries or measured reset."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,os,shutil,subprocess,time,traceback,zipfile,xml.etree.ElementTree as E
folder=Path(__file__).resolve().parent;study=folder.parents[2];root=study.parents[2]
build=root/'profiles/wifi_ps_none_20261103/build';tools=root/'tools/run_recorder'
python='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
old=study/'runs/HBPSN-04/attempt_20261106T020052Z_host_preflight_continuation'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
    with (folder/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def ps(s):
    p=subprocess.run(['powershell','-NoProfile','-Command',s],capture_output=True,text=True,timeout=40);assert p.returncode==0,p.stderr
    return json.loads(p.stdout)
try:
    assert not (folder/'SETUP_STARTED.json').exists();save('SETUP_STARTED.json',dict(utc=utc(),automatic_retry=False))
    plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
    rows=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
    assert [r['status'] for r in rows[:5]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','NOT_RUN']
    assert [rows[4][k] for k in ['run_id','transport','condition']]==['HBPSN-05','QUIC','LAG100_OUT']
    xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx';ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(xlsx) as z:
        rr=E.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//x:sheetData/x:row',ns)
        for i in range(5):
            c=next(c for c in rr[i+1] if c.get('r')=='G'+str(i+2));v=''.join(c.find('x:is',ns).itertext()) if c.get('t')=='inlineStr' else c.find('x:v',ns).text
            assert v==rows[i]['status']
    shutil.copy2(study/'run_register.csv',folder/'before_run_register.csv');shutil.copy2(xlsx,folder/'before_run_register.xlsx')
    manifest=json.loads((study/'freeze_manifest.json').read_text());artifacts=[x for x in manifest['artifacts'] if x['transport']=='QUIC']
    assert len(artifacts)==4 and all(sha(x['path'])==x['sha256'] for x in artifacts)
    prior=json.loads((study/'runs/HBPSN-01/attempt_20261104T002840Z/preflight.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in prior['configuration'])
    source=json.loads((root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json').read_text());assert all(sha(root/p)==h for p,h in source.items())
    image=json.loads((folder/'clumsy_actual_pre_flash_metadata.json').read_text());assert image['status']=='PASS' and sha(folder/image['screenshot'])==image['sha256']
    assert dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(image['capture_started_utc'])<dt.timedelta(minutes=10)
    expected=dict(filter='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)',capture='RUNNING',Lag=dict(enabled=True,delay_ms=100,inbound=False,outbound=True),other_main_effects={k:False for k in ['Drop','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']});assert image['observed']==expected
    system=ps("$p=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile();$m=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($p);@{utc=[DateTime]::UtcNow.ToString('o');hotspot=$m.TetheringOperationalState.ToString();band=$m.GetCurrentAccessPointConfiguration().Band.ToString();ssid=$m.GetCurrentAccessPointConfiguration().Ssid;ips=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias);port=@(Get-CimInstance Win32_SerialPort | Where-Object DeviceID -eq 'COM6' | Select-Object DeviceID,Name,PNPDeviceID);udp=@(Get-NetUDPEndpoint -LocalPort14567 -ErrorAction Stop);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object ProcessId,ParentProcessId,CommandLine);cpu=@(Get-CimInstance Win32_Processor | Select-Object LoadPercentage);os=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber} | ConvertTo-Json -Depth 5".replace('-LocalPort14567','-LocalPort 14567'))
    save('system_preflight.json',system)
    assert system['hotspot']=='On' and system['band']=='TwoPointFourGigahertz' and any(x['IPAddress']=='192.168.137.1' for x in system['ips'])
    assert len(system['port'])==1 and 'FABA8DF9808FED11A981E817B96CE6F8' in system['port'][0]['PNPDeviceID']
    assert any(x['OwningProcess']==23100 for x in system['udp'])
    assert any(x['ProcessId']==23100 and '.quic-venv' in x['CommandLine'] and 'quic_server.py' in x['CommandLine'] for x in system['processes'])
    assert any(x['ProcessId']==16080 and x['ParentProcessId']==28020 and 'HBPSN-04' in x['CommandLine'] and '--port COM6' in x['CommandLine'] for x in system['processes'])
    assert json.loads((old/'FINALIZED.json').read_text())['processing_status']=='FINALIZED'
    protected=[]
    for rid in ['HBPSN-01','HBPSN-02','HBPSN-03','HBPSN-04']:
        for p in (study/'runs'/rid).rglob('*'):
            if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts:protected.append(dict(path=str(p),sha256=sha(p)))
    save('earlier_runs_preservation_before.json',protected)
    sources=dict(prior['server_log_sources'],sensor_csv=prior['server_sensor_source']);assert all(Path(p).exists() for p in sources.values())
    save('preflight.json',dict(status='PASS',run_id='HBPSN-05',transport='QUIC',condition='LAG100_OUT',checked_utc=utc(),plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),protocol_id=manifest['protocol_id'],firmware_artifacts=artifacts,configuration=prior['configuration'],server_log_sources=sources,server_sensor_source=sources['sensor_csv'],expected_clumsy_settings=expected,validity_status='NOT_APPROVED',observer_policy='Actual nonce-linked pre-reset image; final validity pending actual post-recording image and operator review',clumsy_executable_sha256=sha('C:/Users/newsh/Downloads/clumsy-0.3-win64-a/clumsy.exe'),source_manifest_sha256=sha(root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json'),host_activity='Chrome Remote Desktop operator-reported; existing host applications remain; unchanged physical board/sensor setup per experiment context',unresolved_quic_crash=True))
    for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']:
        assert sha(tools/n)==sha(old/n);shutil.copy2(tools/n,folder/n)
    save('collector_version.json',dict(version='repaired-v2-manual-review-gate',files=[dict(path=n,sha256=sha(folder/n)) for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']]))
    (old/'monitor_control.txt').write_text('exit\n');save('monitor_handover_request.json',dict(utc=utc(),old_collector_pid=28020,monitor_pids=[16080,5148],method='Verified completed HBPSN-04 monitor exit via existing collector control channel'))
    for _ in range(25):
        if ps('@(Get-Process -Id 16080,5148 -ErrorAction SilentlyContinue).Count | ConvertTo-Json')==0:break
        time.sleep(.2)
    else:raise RuntimeError('Verified old monitor did not exit; no force kill or flash')
    env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    command=[python,'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','flash-id']
    began=utc();p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=40);(folder/'identification.log').write_text(p.stdout+p.stderr,encoding='utf-16')
    save('identification_reset.json',dict(started_utc=began,completed_utc=utc(),command=command,exit_code=p.returncode,setup_only=True))
    assert p.returncode==0 and '40:4c:ca:56:bb:b0' in p.stdout and '8MB' in p.stdout,'Identification failed; no retry'
    args=json.loads((build/'flasher_args.json').read_text());extra=args['extra_esptool_args'];command=[python,'-m','esptool','--chip',extra['chip'],'--port','COM6','--baud','460800','--before',extra['before'],'--after',extra['after'],'write-flash','@flash_args']
    save('flash_started.json',dict(utc=utc(),command=command,cwd=str(build),setup_only=True));print('FLASHING_FORMAL_QUIC_ONCE',flush=True)
    p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180);(folder/'flash.log').write_text(' '.join(command)+'\n'+p.stdout+p.stderr,encoding='utf-16')
    save('flash_result.json',dict(exit_code=p.returncode,ended_utc=utc(),verified_image_count=p.stdout.count('Hash of data verified.'),setup_only=True))
    assert p.returncode==0 and p.stdout.count('Hash of data verified.')==3,'Flash failed; no retry'
    assert all(sha(x['path'])==x['sha256'] for x in artifacts) and all(sha(x['path'])==x['sha256'] for x in protected)
    save('setup_complete.json',dict(utc=utc(),flash_verification='PASS_3_OF_3',earlier_runs_unchanged=True,designated_measured_reset_not_yet_issued=True));print('READY_FOR_COLLECTOR',flush=True)
except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),error=traceback.format_exc(),automatic_retry=False));raise
