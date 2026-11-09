"""TEST_ONLY host orchestration. One diagnostic application reset release only.
No firmware source edits/builds/settings changes. Dedicated raw UART, no decoding.
"""
from pathlib import Path
import csv,datetime as dt,hashlib,json,os,subprocess,threading,time,traceback
import serial
from esp_pylib.serial_reset import set_rts,PIN_LOW,PIN_HIGH

out=Path(__file__).resolve().parent
root=out.parents[2];profile=root/'profiles/test_only_heap_20261106';build=profile/'build'
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
old=study/'runs/HBPSN-03/attempt_20261105T202314Z'
python=Path('C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe')
port=None;start=None;reader=None;reader_error=None
lock=threading.RLock();capture_done=threading.Event()
raw=None;receipts=None;after=None
core_starts=[];core_ends=[];partial=b'';total_bytes=0;release_requested=False
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(out/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def ps(s):
    p=subprocess.run(['powershell','-NoProfile','-Command',s],capture_output=True,text=True,timeout=40)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout)
def serial_reader():
    global partial,total_bytes,reader_error
    try:
        while True:
            data=port.read(max(1,min(port.in_waiting,4096)))
            if not data:continue
            stamp=utc();mono=time.monotonic()
            with lock:
                if capture_done.is_set():after.write(data);continue
                offset=raw.tell();raw.write(data);total_bytes+=len(data)
                receipts.write(json.dumps(dict(utc=stamp,monotonic=mono,offset=offset,length=len(data)))+'\n')
                partial+=data
                while b'\n' in partial:
                    line,partial=partial.split(b'\n',1)
                    if b'CORE DUMP START' in line:core_starts.append(dict(utc=stamp,monotonic=mono,raw_offset=offset))
                    if b'CORE DUMP END' in line:core_ends.append(dict(utc=stamp,monotonic=mono,raw_offset=offset))
    except Exception:
        reader_error=dict(utc=utc(),error=traceback.format_exc());save('SERIAL_READER_FAILURE.json',reader_error)

try:
    assert not (out/'flash_started.json').exists() and not (out/'reset_release.json').exists()
    finalized=json.loads((old/'FINALIZED.json').read_text());assert finalized['processing_status']=='FINALIZED' and finalized['status']=='FAILED_STARTUP'
    rows=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
    assert [r['status'] for r in rows[:3]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP'] and not any(r['status']=='RUNNING' for r in rows)
    report=json.loads((profile/'BUILD_REPORT.json').read_text())
    assert report['build_link']=='PASS' and all(sha(x['path'])==x['sha256'] for x in report['artifacts'])
    image=json.loads((out/'clumsy_preflight.json').read_text());assert image['status']=='PASS' and sha(out/image['image'])==image['sha256']
    assert image['filter']=='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)' and image['capture']=='RUNNING' and image['Drop']==dict(enabled=True,chance_percent=1.0,inbound=False,outbound=True) and not any(image['other_main_effects'].values())
    system=ps("$p=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile();$m=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($p);@{utc=[DateTime]::UtcNow.ToString('o');hotspot=$m.TetheringOperationalState.ToString();band=$m.GetCurrentAccessPointConfiguration().Band.ToString();ssid=$m.GetCurrentAccessPointConfiguration().Ssid;ips=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias);port=@(Get-CimInstance Win32_SerialPort | Where-Object DeviceID -eq 'COM6' | Select-Object DeviceID,Name,PNPDeviceID);listener=@(Get-NetUDPEndpoint -LocalPort 14567 | Select-Object LocalAddress,LocalPort,OwningProcess);processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object ProcessId,ParentProcessId,CommandLine)}|ConvertTo-Json -Depth 5")
    save('system_preflight.json',system)
    assert system['hotspot']=='On' and any(x['IPAddress']=='192.168.137.1' for x in system['ips'])
    assert len(system['port'])==1 and 'FABA8DF9808FED11A981E817B96CE6F8' in system['port'][0]['PNPDeviceID']
    assert any(x['OwningProcess']==23100 for x in system['listener'])
    proc=system['processes'];assert any(x['ProcessId']==23100 and 'quic_server.py' in x['CommandLine'] and '.quic-venv' in x['CommandLine'] for x in proc)
    for x in proc:
        if 'collector_v2.py' in (x['CommandLine'] or ''):assert 'HBPSN-03/attempt_20261105T202314Z' in x['CommandLine'].replace('\\','/'),'Unexpected collector; stop before board access'
    assert any(x['ProcessId']==32192 and x['ParentProcessId']==16148 and '--port COM6' in x['CommandLine'] for x in proc)
    protected=[study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'freeze_manifest.json']
    manifest=json.loads((root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json').read_text())
    for rel,expected in manifest.items():assert sha(root/rel)==expected,rel
    protected.extend(root/rel for rel in manifest)
    for rid in ['HBPSN-01','HBPSN-02','HBPSN-03']:
        for p in (study/'runs'/rid).rglob('*'):
            if p.is_file() and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'} and '__pycache__' not in p.parts:protected.append(p)
    frozen=[dict(path=str(p),sha256=sha(p)) for p in set(protected)]
    save('protected_before.json',frozen)
    save('preflight.json',dict(label='TEST_ONLY',status='PASS',utc=utc(),formal_collection_active=False,formal_finalization=finalized,diagnostic_artifacts=report['artifacts'],clumsy=image,host_activity='Chrome Remote Desktop operator-reported; host apps may remain active. Not a formal RTT experiment.',observation_seconds=180,max_core_recovery_extension_seconds=120,override_from_proposed_120s='Current user instruction sets180s plus at most120s for core already active at180s',one_application_boot_policy='Identify into ROM without stub, flash with before=no-reset/after=no-reset. Logger opens with EN held low, then releases it once. No normal post-flash application boot precedes recording.'))
    # Graceful release of only the verified obsolete monitor. No force kill.
    (old/'monitor_control.txt').write_text('exit\n')
    save('old_monitor_exit_request.json',dict(utc=utc(),collector=16148,monitors=[32192,36012],method='Existing post-finalization collector exit channel'))
    for _ in range(25):
        remaining=ps('@(Get-Process -Id 32192,36012 -ErrorAction SilentlyContinue).Count|ConvertTo-Json')
        if not remaining:break
        time.sleep(.2)
    else:raise RuntimeError('Old COM6 monitor did not close; no retry or flash')
    env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    identify=[str(python),'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','--no-stub','flash-id']
    began=utc();r=subprocess.run(identify,cwd=build,env=env,capture_output=True,text=True,timeout=40)
    (out/'identification.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    save('identification.json',dict(started_utc=began,ended_utc=utc(),command=identify,exit_code=r.returncode,reset='ROM-loader entry only, no diagnostic application start'))
    assert r.returncode==0 and '40:4c:ca:56:bb:b0' in r.stdout and '8MB' in r.stdout,'Identification failed; no retry'
    args=json.loads((build/'flasher_args.json').read_text());command=[str(python),'-m','esptool','--chip',args['extra_esptool_args']['chip'],'--port','COM6','--baud','460800','--before','no-reset','--after','no-reset','write-flash','@flash_args']
    save('flash_started.json',dict(utc=utc(),command=command,cwd=str(build),reset_override='Matching image/offset/mode/size/frequency arguments unchanged. Suppress before/after reset to keep ROM and capture first application startup.'))
    print('TEST_ONLY FLASHING_ONCE',flush=True)
    r=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180)
    (out/'flash.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    save('flash_result.json',dict(utc=utc(),exit_code=r.returncode,verified_image_count=r.stdout.count('Hash of data verified.'),after='no-reset'))
    assert r.returncode==0 and r.stdout.count('Hash of data verified.')==3,'Flash failed; no retry'
    assert all(sha(x['path'])==x['sha256'] for x in report['artifacts'])
    # Create all output files BEFORE opening serial. .open() clears the driver
    # buffer while EN is held low, before the designated application release.
    raw=(out/'TEST_ONLY_uart.raw.log').open('ab',buffering=0)
    receipts=(out/'TEST_ONLY_uart_receipts.jsonl').open('a',encoding='utf-8',buffering=1)
    after=(out/'TEST_ONLY_after_capture.raw.log').open('ab',buffering=0)
    port=serial.Serial(port=None,baudrate=115200,timeout=.05,write_timeout=1)
    port.dtr=PIN_HIGH;port.rts=PIN_LOW;port.port='COM6';port.open()
    save('serial_open.json',dict(utc=utc(),pid=os.getpid(),port='COM6',baud=115200,dtr=port.dtr,rts=port.rts,EN='held low before release',raw_logger='Byte-exact pyserial; no addr2line/core decoding; no post-open input flush',driver_open_clear='pyserial Windows purges buffers at open while application reset held; first application startup follows later explicit release'))
    reader=threading.Thread(target=serial_reader,daemon=True);reader.start();time.sleep(.3)
    assert reader_error is None
    assert b'TEST_ONLY QUIC HEAP DIAGNOSTIC' not in (out/'TEST_ONLY_uart.raw.log').read_bytes(),'Unexpected diagnostic boot before designated release; do not issue another reset'
    # One application boot starts HERE; no subsequent agent reset is permitted.
    request=utc();release_requested=True;set_rts(port,PIN_HIGH)
    mono=time.monotonic();stamp=dt.datetime.now(dt.timezone.utc)
    start=dict(label='TEST_ONLY',reset_request_utc=request,reset_release_utc=stamp.isoformat(),reset_release_monotonic=mono,observation_deadline_utc=(stamp+dt.timedelta(seconds=180)).isoformat(),observation_deadline_monotonic=mono+180,maximum_core_end_utc=(stamp+dt.timedelta(seconds=300)).isoformat(),maximum_core_end_monotonic=mono+300,method='Espressif set_rts(PIN_HIGH) after logger ready and EN held low. Host anchor after successful API return, not physical-edge measurement.',server_boundaries={n:dict(path=str(root/'logs'/f),bytes=(root/'logs'/f).stat().st_size) for n,f in [('stdout','quic_server_start_20261103T163259.stdout.log'),('stderr','quic_server_start_20261103T163259.stderr.log')]})
    save('reset_release.json',start);print(json.dumps(start),flush=True)
    extension_id=None;decision=False
    while True:
        now=time.monotonic()
        if reader_error:raise RuntimeError('Serial reader failed; no reconnect/reset')
        with lock:
            if now>=start['observation_deadline_monotonic'] and not decision:
                decision=True
                # Only a core START observed before the original deadline qualifies.
                active=[i+1 for i,x in enumerate(core_starts) if x['monotonic']<=start['observation_deadline_monotonic'] and i>=len(core_ends)]
                extension_id=active[-1] if active else None
                save('deadline_decision.json',dict(utc=utc(),core_starts=core_starts,core_ends=core_ends,extension_core_id=extension_id,max_extension_seconds=120,deadline_unchanged=True))
            done=decision and (extension_id is None or len(core_ends)>=extension_id or now>=start['maximum_core_end_monotonic'])
            if done:
                capture_done.set();raw.flush();receipts.flush();break
        save('heartbeat.json',dict(utc=utc(),elapsed_seconds=now-mono,bytes=total_bytes,core_starts=len(core_starts),core_ends=len(core_ends),extension_core_id=extension_id))
        time.sleep(.05 if now>=start['observation_deadline_monotonic']-1 else .25)
    raw.close();receipts.close()
    save('CAPTURE_COMPLETE.json',dict(label='TEST_ONLY',utc=utc(),start=start,observed_elapsed_seconds=time.monotonic()-mono,core_starts=core_starts,core_ends=core_ends,extension_core_id=extension_id,core_incomplete=len(core_starts)>len(core_ends),raw_bytes=(out/'TEST_ONLY_uart.raw.log').stat().st_size,raw_sha256=sha(out/'TEST_ONLY_uart.raw.log'),note='Raw logger read chunks may straddle cutoff; receipt times retain primary180s versus recovery tail provenance. Later bytes route to separate after-capture file. No manual retry/reset.',firmware_remaining='TEST_ONLY diagnostic BIN '+report['artifacts'][0]['sha256']))
    assert all(sha(x['path'])==x['sha256'] for x in frozen)
    save('protection_after.json',dict(utc=utc(),count=len(frozen),all_unchanged=True,formal_registers_unchanged=True))
    print('TEST_ONLY CAPTURE_COMPLETE',flush=True)
    # Keep serial line states and logger stable; no automatic firmware restoration.
    while reader.is_alive():time.sleep(1)
except Exception:
    save('HOST_FAILURE.json',dict(utc=utc(),error=traceback.format_exc(),release_requested=release_requested,start=start,automatic_retry=False,firmware_may_have_changed=(out/'flash_started.json').exists()))
    print(traceback.format_exc(),flush=True)
    # An already-open UART stays at its current line levels; never retry/reset.
    if port and port.is_open:
        while True:time.sleep(1)
    raise
