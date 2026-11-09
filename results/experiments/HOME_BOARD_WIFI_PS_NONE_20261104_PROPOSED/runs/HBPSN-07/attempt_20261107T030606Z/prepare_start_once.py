"""One authorized HBPSN-07 setup; no measured reset and no retry."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,os,shutil,subprocess,time,traceback,zipfile,xml.etree.ElementTree as E
folder=Path(__file__).resolve().parent;study=folder.parents[2];root=study.parents[2]
profile=root/'profiles/tcp_tls_wifi_ps_none_20261104';build=profile/'build';tools=root/'tools/run_recorder'
python='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
old=study/'runs/HBPSN-06/attempt_20261107T015952Z'
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
    assert [r['status'] for r in rows[:7]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','COMPLETE','COMPLETE','NOT_RUN'] and not any(r['status']=='RUNNING' for r in rows)
    assert [rows[6][k] for k in ['run_id','transport','condition']]==['HBPSN-07','TCP_TLS','DROP1_OUT']
    xlsx=root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx';ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(xlsx) as z:
        rr=E.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//x:sheetData/x:row',ns)
        for i in range(7):
            c=next(c for c in rr[i+1] if c.get('r')=='G'+str(i+2));v=''.join(c.find('x:is',ns).itertext()) if c.get('t')=='inlineStr' else c.find('x:v',ns).text;assert v==rows[i]['status']
    shutil.copy2(study/'run_register.csv',folder/'before_run_register.csv');shutil.copy2(xlsx,folder/'before_run_register.xlsx')
    manifest=json.loads((study/'freeze_manifest.json').read_text());artifacts=[x for x in manifest['artifacts'] if x['transport']=='TCP_TLS'];assert len(artifacts)==4 and all(sha(x['path'])==x['sha256'] for x in artifacts)
    validation=json.loads((profile/'validation.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in validation['artifacts'].values())
    prior=json.loads((study/'runs/HBPSN-02/attempt_20261104T121332Z/preflight.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in prior['configuration'])
    source=json.loads((root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json').read_text());assert all(sha(root/p)==h for p,h in source.items())
    image=json.loads((folder/'clumsy_actual_pre_flash_metadata.json').read_text());assert image['status']=='PASS' and sha(folder/image['screenshot'])==image['sha256'];assert dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(image['capture_started_utc'])<dt.timedelta(minutes=10)
    expected=dict(filter='tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)',capture='RUNNING',Drop=dict(enabled=True,chance_percent=1.0,inbound=False,outbound=True),other_main_effects={k:False for k in ['Lag','Throttle','Duplicate','Out of order','Tamper','Set TCP RST','Bandwidth']});assert image['observed']==expected
    system=ps("$p=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile();$m=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($p);@{utc=[DateTime]::UtcNow.ToString('o');hotspot=$m.TetheringOperationalState.ToString();band=$m.GetCurrentAccessPointConfiguration().Band.ToString();ssid=$m.GetCurrentAccessPointConfiguration().Ssid;ips=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias);port=@(Get-CimInstance Win32_SerialPort | Where-Object DeviceID -eq 'COM6' | Select-Object DeviceID,Name,PNPDeviceID);tcp=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'LocalPort = 14568' | Select-Object LocalAddress,LocalPort,State,OwningProcess);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object ProcessId,ParentProcessId,CommandLine);cpu=@(Get-CimInstance Win32_Processor | Select-Object LoadPercentage);os=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber} | ConvertTo-Json -Depth 5")
    save('system_preflight.json',system);assert system['hotspot']=='On' and system['band']=='TwoPointFourGigahertz' and any(x['IPAddress']=='192.168.137.1' for x in system['ips'])
    assert len(system['port'])==1 and 'FABA8DF9808FED11A981E817B96CE6F8' in system['port'][0]['PNPDeviceID']
    assert any(x['ProcessId']==36536 and '.quic-venv' in x['CommandLine'] and 'tcp_tls_server.py' in x['CommandLine'] for x in system['processes'])
    assert any(x['OwningProcess']==36536 for x in system['tcp'])
    assert any(x['ProcessId']==7680 and x['ParentProcessId']==16072 and 'HBPSN-06' in x['CommandLine'] and '--port COM6' in x['CommandLine'] for x in system['processes'])
    assert json.loads((old/'FINALIZED.json').read_text())['processing_status']=='FINALIZED'
    for x in system['processes']:
        if 'collector_v2.py' in (x['CommandLine'] or ''):assert 'HBPSN-06/attempt_20261107T015952Z' in x['CommandLine'].replace('\\','/'),'Unexpected collector'
    sources=json.loads((study/'runs/HBPSN-04/attempt_20261106T020052Z_host_preflight_continuation/preflight.json').read_text())['server_log_sources'];assert all(Path(p).exists() for p in sources.values())
    assert 'READY | TCP+TLS port 14568 | ALPN=mqtt' in Path(sources['stdout']).read_text()
    probe_boundaries={}
    for name,path in sources.items():
        data=Path(path).read_bytes();(folder/f'pre_probe_{name}.snapshot.log').write_bytes(data);probe_boundaries[name]=dict(source=path,byte_offset=len(data),sha256=hashlib.sha256(data).hexdigest())
    save('probe_boundaries_before.json',dict(utc=utc(),streams=probe_boundaries))
    p=subprocess.run([str(root/'.quic-venv/Scripts/python.exe'),'-B',str(folder/'host_tls_probe_once.py')],cwd=root,capture_output=True,text=True,timeout=12)
    (folder/'host_tls_probe.stdout.log').write_text(p.stdout);(folder/'host_tls_probe.stderr.log').write_text(p.stderr);save('host_tls_probe_exit.json',dict(utc=utc(),exit_code=p.returncode,one_attempt=True));assert p.returncode==0,'Functional server probe failed; no retry'
    time.sleep(.5)
    save('probe_boundaries_after.json',dict(utc=utc(),streams={n:dict(source=p,byte_offset=Path(p).stat().st_size,sha256=sha(p)) for n,p in sources.items()},scope='Host-local probe-associated; not formal-run evidence; all subsequent measured boundaries refresh at reset'))
    protected=[]
    for rid in ['HBPSN-01','HBPSN-02','HBPSN-03','HBPSN-04','HBPSN-05','HBPSN-06']:
        for p in (study/'runs'/rid).rglob('*'):
            if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts:protected.append(dict(path=str(p),sha256=sha(p)))
    save('earlier_runs_preservation_before.json',protected)
    save('preflight.json',dict(status='PASS',run_id='HBPSN-07',transport='TCP_TLS',condition='DROP1_OUT',checked_utc=utc(),plan_sha256=sha(plan),freeze_manifest_sha256=sha(study/'freeze_manifest.json'),protocol_id=manifest['protocol_id'],firmware_artifacts=artifacts,configuration=prior['configuration'],server_log_sources=sources,server_sensor_source=sources['sensor_csv'],expected_clumsy_settings=expected,validity_status='NOT_APPROVED',observer_policy='Actual nonce-linked pre-reset image; validity pending actual post-recording image and NEW operator confirmation specific toHBPSN-07',server_readiness=dict(pid=36536,functional_probe=str(folder/'host_tls_probe.json'),prior_windows_reporting_discrepancy_retained=True,ready_after_listen_source_evidence=str(root/'results/diagnostics/HOST_ONLY_TCP14568_20261106T014632766Z/REPORT.md')),clumsy_executable_sha256=sha('C:/Users/newsh/Downloads/clumsy-0.3-win64-a/clumsy.exe'),host_activity='Chrome Remote Desktop operator-reported; physical setup retained per experiment context, not independently reinspected',unresolved_quic_crash=True))
    for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']:assert sha(tools/n)==sha(old/n);shutil.copy2(tools/n,folder/n)
    save('collector_version.json',dict(version='repaired-v2-manual-review-gate',files=[dict(path=n,sha256=sha(folder/n)) for n in ['collector_v2.py','reliability.py','monitor_instrumented_v2.py']]))
    (old/'monitor_control.txt').write_text('exit\n');save('monitor_handover_request.json',dict(utc=utc(),old_collector_pid=16072,monitor_pids=[7680,16988],method='Verified completed HBPSN-06 monitor exit via collector channel'))
    for _ in range(25):
        if ps('@(Get-Process -Id 7680,16988 -ErrorAction SilentlyContinue).Count | ConvertTo-Json')==0:break
        time.sleep(.2)
    else:raise RuntimeError('Previous monitor did not exit; no force kill or flash')
    # No board identification/reset/flash: preserved verified image is reused.
    previous_startup=json.loads((old/'startup_checks.json').read_text());assert previous_startup['pass_all'] and previous_startup['reported_elf_prefix']=='1f661a4f7'
    monitor_data=(old/'monitor_stream.log').read_bytes();after_data=(old/'monitor_after_run.log').read_bytes()
    assert b'TEST_ONLY QUIC HEAP DIAGNOSTIC' not in monitor_data
    import re
    prefixes=re.findall(rb'ELF file SHA256:\s*([a-f0-9]+)',monitor_data)
    assert prefixes and all(artifacts[1]['sha256'].startswith(x.decode()) for x in prefixes)
    assert b'ESP-ROM:esp32c6' not in after_data, 'Unexpected later boot; stop before measured reset'
    previous_flash=json.loads((old/'flash_result.json').read_text());assert previous_flash['exit_code']==0 and previous_flash['verified_image_count']==3
    assert (old/'flash.log').read_text(encoding='utf-16').count('Hash of data verified.')==3
    for n in ['flash.log','flash_result.json','identification.log','identification_reset.json','flash_started.json']:shutil.copy2(old/n,folder/n)
    reuse=dict(utc=utc(),reflash_performed=False,board_identification_reset_performed=False,provenance='HBPSN-06 verified formal flash and startup; same COM6 monitor lineage retained until graceful handover; no later ROM boot observed in after-run log',previous_attempt=str(old),previous_flash_result=previous_flash,previous_startup=previous_startup,observed_elf_prefixes=[x.decode() for x in prefixes],monitor_source=dict(path=str(old/'monitor_stream.log'),bytes=len(monitor_data),sha256=hashlib.sha256(monitor_data).hexdigest()),after_source=dict(path=str(old/'monitor_after_run.log'),bytes=len(after_data),sha256=hashlib.sha256(after_data).hexdigest()),measurement_limit='Full on-device image hash not re-read; preserved flash verification plus runtime prefix/provenance. Actual new measured startup independently checked.')
    save('firmware_reuse_verification.json',reuse)
    assert all(sha(x['path'])==x['sha256'] for x in artifacts) and all(sha(x['path'])==x['sha256'] for x in protected)
    save('setup_complete.json',dict(utc=utc(),flash_verification='REUSED_HBPSN06_PASS_3_OF_3',reflash_performed=False,earlier_runs_unchanged=True,designated_measured_reset_not_yet_issued=True));print('READY_FOR_COLLECTOR_NO_REFLASH',flush=True)

except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),error=traceback.format_exc(),automatic_retry=False));raise
