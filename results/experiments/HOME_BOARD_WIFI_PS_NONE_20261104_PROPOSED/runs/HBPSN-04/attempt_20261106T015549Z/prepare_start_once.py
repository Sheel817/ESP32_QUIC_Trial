"""Authorized HBPSN-04 setup, one identification/flash; no measured reset here."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,os,shutil,subprocess,time,traceback,zipfile,xml.etree.ElementTree as E
folder=Path(__file__).resolve().parent
study=folder.parents[2];root=study.parents[2]
profile=root/'profiles/tcp_tls_wifi_ps_none_20261104';build=profile/'build'
python='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
    with (folder/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def ps(s):
    p=subprocess.run(['powershell','-NoProfile','-Command',s],capture_output=True,text=True,timeout=40)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout)
try:
    assert not (folder/'SETUP_STARTED.json').exists(),'Never repeat setup'
    save('SETUP_STARTED.json',dict(utc=utc(),automatic_retry=False))
    plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md'
    assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
    rows=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
    assert [r['status'] for r in rows[:4]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','NOT_RUN']
    assert [rows[3][k] for k in ('run_id','transport','condition')]==['HBPSN-04','TCP_TLS','CONTROL']
    assert not any(r['status']=='RUNNING' for r in rows)
    xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
    assert sha(study/'run_register.csv')=='656b5c6a71cbe783c66b9fe14f74551776e09522a7354ab9b385fb1baa908aae'
    assert sha(xlsx)=='63980c1b51d42099f00867e52a48dec17d91c53eb4dc8d8e32e1f12f936d78ea'
    with zipfile.ZipFile(xlsx) as z:
        ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        xml=E.fromstring(z.read('xl/worksheets/sheet1.xml'))
        statuses=[]
        for row in xml.findall('.//x:sheetData/x:row',ns)[1:5]:
            c=next(c for c in row.findall('x:c',ns) if c.get('r').startswith('G'))
            statuses.append(''.join(c.find('x:is',ns).itertext()) if c.get('t')=='inlineStr' else c.find('x:v',ns).text)
        assert statuses==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','NOT_RUN'],statuses
    shutil.copy2(study/'run_register.csv',folder/'before_run_register.csv')
    shutil.copy2(xlsx,folder/'before_run_register.xlsx')
    manifest=json.loads((study/'freeze_manifest.json').read_text())
    artifacts=[a for a in manifest['artifacts'] if a['transport']=='TCP_TLS']
    assert len(artifacts)==4 and all(sha(a['path'])==a['sha256'] for a in artifacts)
    validation=json.loads((profile/'validation.json').read_text())
    assert all(sha(a['path'])==a['sha256'] for a in validation['artifacts'].values())
    prior=json.loads((study/'runs/HBPSN-02/attempt_20261104T121332Z/preflight.json').read_text())
    assert all(sha(a['path'])==a['sha256'] for a in prior['configuration'])
    image=json.loads((folder/'clumsy_actual_pre_flash_metadata.json').read_text())
    assert image['status']=='PASS' and sha(folder/image['screenshot'])==image['sha256']
    assert dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(image['capture_started_utc'])<dt.timedelta(minutes=10)
    expected=dict(filter='tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)',capture='RUNNING',Lag=dict(enabled=False,delay_ms=100,inbound=False,outbound=True),other_main_effects={k:False for k in ['Drop','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']})
    assert image['observed']==expected
    system=ps("$p=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile();$m=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($p);@{utc=[DateTime]::UtcNow.ToString('o');hotspot=$m.TetheringOperationalState.ToString();band=$m.GetCurrentAccessPointConfiguration().Band.ToString();ssid=$m.GetCurrentAccessPointConfiguration().Ssid;ips=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias);port=@(Get-CimInstance Win32_SerialPort | Where-Object DeviceID -eq 'COM6' | Select-Object DeviceID,Name,PNPDeviceID);endpoint=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'LocalPort = 14568' | Select-Object LocalAddress,LocalPort,State,OwningProcess);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object ProcessId,ParentProcessId,CommandLine);cpu=@(Get-CimInstance Win32_Processor | Select-Object LoadPercentage);os=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber} | ConvertTo-Json -Depth 5")
    save('system_preflight.json',system)
    assert system['hotspot']=='On' and system['band']=='TwoPointFourGigahertz'
    assert any(x['IPAddress']=='192.168.137.1' for x in system['ips'])
    assert len(system['port'])==1 and 'FABA8DF9808FED11A981E817B96CE6F8' in system['port'][0]['PNPDeviceID']
    proc=system['processes']
    assert any(x['ProcessId']==36536 and 'tcp_tls_server.py' in x['CommandLine'] and '.quic-venv' in x['CommandLine'] and 'ESP32_QUIC_Trial' in x['CommandLine'] for x in proc)
    assert any(x['OwningProcess']==36536 for x in system['endpoint'])
    diag=root/'results/diagnostics/TEST_ONLY_QUIC_HEAP_20261106T004758540Z'
    assert (diag/'CAPTURE_COMPLETE.json').exists()
    diag_manifest=json.loads((diag/'SHA256SUMS.json').read_text())
    assert all(sha(diag/x['path'])==x['sha256'] for x in diag_manifest['files'])
    assert any(x['ProcessId']==32104 and x['ParentProcessId']==32072 and str(diag/'run_host_capture.py').replace('\\','/') in x['CommandLine'].replace('\\','/') for x in proc)
    assert not any('collector_v2.py' in (x['CommandLine'] or '') for x in proc),'Unexpected formal collector process'
    probes=root/'results/diagnostics/HOST_ONLY_TCP14568_20261106T014632766Z'
    outcomes=json.loads((probes/'probe_results.json').read_text())
    assert len(outcomes)==2 and all(x['tcp']=='CONNECTED' and x['tls']=='NEGOTIATED' and x['certificate_matches_preserved'] for x in outcomes)
    server=root/'results/preflights/HBPSN04_START_20261106T013540465Z'
    sources=dict(stdout=str(server/'tcp_tls_server.stdout.log'),stderr=str(server/'tcp_tls_server.stderr.log'),sensor_csv=str(root/'logs/sensor_tcp_tls_20261106T013631_157099Z_mrgf6j6d.csv'))
    assert 'READY | TCP+TLS port 14568 | ALPN=mqtt' in Path(sources['stdout']).read_text()
    protected=[]
    for rid in ['HBPSN-01','HBPSN-02','HBPSN-03']:
        for p in (study/'runs'/rid).rglob('*'):
            if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts:protected.append(dict(path=str(p),sha256=sha(p)))
    save('earlier_runs_preservation_before.json',protected)
    config=prior['configuration']
    save('preflight.json',dict(status='PASS',run_id='HBPSN-04',transport='TCP_TLS',condition='CONTROL',checked_utc=utc(),protocol_id=manifest['protocol_id'],plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),firmware_artifacts=artifacts,configuration=config,server_log_sources=sources,server_sensor_source=sources['sensor_csv'],expected_clumsy_settings=expected,validity_status='NOT_APPROVED',observer_policy='Fresh nonce-linked actual pre-reset screenshot; post-recording screenshot and operator stability require manual review. No automatic approval.',server_readiness=dict(pid=36536,source_sha256=sha(root/'tcp_tls_server.py'),certificate_sha256=sha(root/'server-cert.pem'),functional_probes=str(probes/'probe_results.json'),ready_after_listen_source_evidence=str(probes/'REPORT.md'),windows_discrepancy_retained=True,plan_does_not_require_specific_windows_readout=True),host_activity='Chrome Remote Desktop operator-reported; existing host apps remain. Device/wiring/power/location inherited unchanged per experiment setup; no new physical inspection.',clumsy_executable_sha256=sha('C:/Users/newsh/Downloads/clumsy-0.3-win64-a/clumsy.exe'),unresolved_quic_crash=True))
    for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']:
        assert sha(root/'tools/run_recorder'/n)==sha(study/'runs/HBPSN-03/attempt_20261105T202314Z'/n)
        shutil.copy2(root/'tools/run_recorder'/n,folder/n)
    save('collector_version.json',dict(version='repaired-v2-manual-review-gate',files=[dict(path=n,sha256=sha(folder/n)) for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']]))
    save('diagnostic_logger_close.json',dict(utc=utc(),target_pid=32104,parent_pid=32072,identity_verified=True,stable_diagnostic_deliverables_verified=len(diag_manifest['files']),method='Terminate only verified completed raw logger; no exit/control channel exists. Serial handle closes outside formal measured window.'))
    result=subprocess.run(['powershell','-NoProfile','-Command',"$p=Get-CimInstance Win32_Process -Filter 'ProcessId=32104'; if($p.ParentProcessId -ne 32072 -or $p.CommandLine -notmatch 'TEST_ONLY_QUIC_HEAP_20261106T004758540Z.*run_host_capture.py'){throw 'Logger identity changed'}; Stop-Process -Id 32104 -ErrorAction Stop"],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    time.sleep(.5)
    assert ps('@(Get-Process -Id 32104 -ErrorAction SilentlyContinue).Count | ConvertTo-Json')==0
    save('diagnostic_preservation_after_close.json',dict(utc=utc(),all_stable_files_unchanged=all(sha(diag/x['path'])==x['sha256'] for x in diag_manifest['files']),separate_live_tail=dict(path=str(diag/'TEST_ONLY_after_capture.raw.log'),bytes=(diag/'TEST_ONLY_after_capture.raw.log').stat().st_size,sha256=sha(diag/'TEST_ONLY_after_capture.raw.log'))))
    env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    command=[python,'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','flash-id']
    began=utc();r=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=40)
    (folder/'identification.log').write_text(r.stdout+r.stderr,encoding='utf-16')
    save('identification_reset.json',dict(started_utc=began,completed_utc=utc(),command=command,exit_code=r.returncode,setup_only=True,reset_note='Espressif default-reset into ROM, after=no-reset; outside measured window'))
    assert r.returncode==0 and '40:4c:ca:56:bb:b0' in r.stdout and '8MB' in r.stdout,'Identification failed; no retry'
    args=json.loads((build/'flasher_args.json').read_text());extra=args['extra_esptool_args']
    command=[python,'-m','esptool','--chip',extra['chip'],'--port','COM6','--baud','460800','--before',extra['before'],'--after',extra['after'],'write-flash','@flash_args']
    save('flash_started.json',dict(utc=utc(),command=command,cwd=str(build),setup_only=True))
    print('FLASHING_FORMAL_PROFILE_ONCE',flush=True)
    r=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180)
    (folder/'flash.log').write_text(' '.join(command)+'\n'+r.stdout+r.stderr,encoding='utf-16')
    save('flash_result.json',dict(exit_code=r.returncode,ended_utc=utc(),verified_image_count=r.stdout.count('Hash of data verified.'),setup_only=True))
    assert r.returncode==0 and r.stdout.count('Hash of data verified.')==3,'Flash failed; no retry'
    assert all(sha(a['path'])==a['sha256'] for a in artifacts)
    assert all(sha(a['path'])==a['sha256'] for a in protected)
    save('setup_complete.json',dict(utc=utc(),flash_verification='PASS_3_OF_3',earlier_runs_unchanged=True,diagnostic_preserved=True,designated_measured_reset_not_yet_issued=True))
    print('FLASH_VERIFIED_READY_FOR_COLLECTOR',flush=True)
except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),error=traceback.format_exc(),automatic_retry=False))
    raise
