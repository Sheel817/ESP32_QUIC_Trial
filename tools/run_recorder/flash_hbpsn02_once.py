"""Continue the existing authorized setup after its old monitor exited; flash once."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,traceback
root=Path(__file__).resolve().parents[2]
folder=Path(Path(__file__).with_name('active_hbpsn02_path.txt').read_text().strip())
build=root/'profiles/tcp_tls_wifi_ps_none_20261104/build'
idfpython='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(n,x):(folder/n).write_text(json.dumps(x,indent=2))
try:
    assert not (folder/'flash_started.json').exists() and not (folder/'reset_event.json').exists()
    p=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process -Id 1776,26296 -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True,timeout=10)
    assert p.stdout.strip()=='0','Old COM6 monitor still running'
    save('previous_monitor_closed.json',dict(verified_utc=utc(),method='SDK exit command through unique collector-created client-end pipe handle 456 in PID33972; both monitor PIDs1776/26296 exited. No force kill/reset.',initial_helper_issue_preserved='initial_close_helper_failure.json',additional_pre_command_guard='Write-pipe count was initially ambiguous; no command sent until parent creator/client-end metadata identified exactly one pipe.'))
    pf=json.loads((folder/'preflight.json').read_text())
    for x in pf['firmware_artifacts']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256']
    env=os.environ.copy();env['PYTHONUTF8']='1'
    command=[idfpython,'-m','esptool','--chip','esp32c6','--port','COM6','--before','default-reset','--after','no-reset','flash-id']
    started=utc();p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=40)
    (folder/'identification.log').write_text(p.stdout+p.stderr,encoding='utf-16')
    save('identification_reset.json',dict(started_utc=started,completed_utc=utc(),command=command,exit_code=p.returncode,setup_only=True,reset_note='Default-reset into ROM, after=no-reset; before formal measured boot'))
    assert p.returncode==0 and '40:4c:ca:56:bb:b0' in p.stdout and 'ESP32-C6' in p.stdout and '8MB' in p.stdout
    a=json.loads((build/'flasher_args.json').read_text())['extra_esptool_args']
    command=[idfpython,'-m','esptool','--chip',a['chip'],'--port','COM6','--baud','460800','--before',a['before'],'--after',a['after'],'write-flash','@flash_args']
    started=utc();save('flash_started.json',dict(started_utc=started,command=command,cwd=str(build),setup_only=True))
    print(json.dumps(dict(stage='FLASHING_ONCE',started_utc=started)),flush=True)
    p=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=180)
    (folder/'flash.log').write_text(' '.join(command)+'\n'+p.stdout+p.stderr,encoding='utf-16')
    save('flash_result.json',dict(exit_code=p.returncode,ended_utc=utc(),artifact_directory=str(build),setup_only='Flash resets precede designated measured startup',verified_image_count=p.stdout.count('Hash of data verified.')))
    assert p.returncode==0 and p.stdout.count('Hash of data verified.')==3,'Flash failed; do not retry'
    original=json.loads((folder/'hbpsn01_preservation_before.json').read_text())
    assert all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in original)
    save('setup_complete.json',dict(utc=utc(),flash_verification='PASS_3_OF_3',identified_home_board=True,hbpsn01_original_files_unchanged=True,designated_start_not_yet_issued=True))
    print(json.dumps(dict(stage='FLASH_VERIFIED_READY_FOR_COLLECTOR',folder=str(folder))),flush=True)
except Exception:
    save('SETUP_FAILURE.json',dict(utc=utc(),traceback=traceback.format_exc(),automatic_retry=False))
    raise
