"""Preserve failure and create a successor; never modify historical run files."""
from pathlib import Path
import datetime as dt,hashlib,json,shutil,py_compile

root=Path(__file__).resolve().parents[2]
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
a=study/'runs/HBPSN-01/attempt_20261104T002840Z'
tools=Path(__file__).resolve().parent
out=root/'results/recorder_tests'/('TEST_ONLY_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
preserved=out/'preserved_failure';preserved.mkdir()
for name in ['collector.py','collector_failure.json','heartbeat.json','heartbeat.json.tmp','monitor_instrumented.py']:
    shutil.copy2(a/name,preserved/name)
live={'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'}
originals=[p for p in (study/'runs/HBPSN-01').rglob('*') if p.is_file() and p.name not in live and '__pycache__' not in p.parts]
originals += [study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'freeze_manifest.json',study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx']
(out/'protected_original_hashes.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in originals],indent=2))
code=(a/'collector.py').read_text()
def change(old,new):
    global code
    assert code.count(old)==1,old[:80]
    code=code.replace(old,new)
change('folder=Path(__file__).resolve().parent', '''import argparse
from reliability import Reports, SettingsEvidence, arm_deadline
parser=argparse.ArgumentParser(description='Preserved-image recorder; explicit fresh run directory required')
parser.add_argument('--run-dir',type=Path,required=True)
args=parser.parse_args()
folder=args.run_dir.resolve()
assert not (folder/'serial.raw.log').exists(), 'Never overwrite/reuse a historical run directory'
reports=Reports(folder)''')
change("preflight=json.loads((folder/'preflight.json').read_text())", """preflight=json.loads((folder/'preflight.json').read_text())
run_id=preflight['run_id']; transport=preflight['transport']; condition=preflight['condition']
assert transport in ('QUIC','TCP_TLS')
assert preflight['plan_sha256']==hashlib.sha256((study/'EXPERIMENT_PLAN_PROPOSED_V1.md').read_bytes()).hexdigest()
evidence=SettingsEvidence(reports,preflight['expected_clumsy_settings'],timeout=30)
finalization_done=threading.Event()
startup_state=None;interruption_state=[]""")
change("    p=folder/name;t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)","    return reports.save(name,value)")
beg=code.index('def register(');end=code.index('\nstream=',beg)
code=code[:beg]+'''def register(patch,final=False):
    # Emit a reviewable request only. Never call the historical HBPSN-01-only updater.
    save('register_final_request.json' if final else 'register_running_request.json',
         dict(run_id=run_id,patch=patch,final=final,automatic_register_apply=False))

'''+code[end:]
change("'quic_firmware':'Starting ESP32-C6 DHT11 over QUIC' in text", "'transport_firmware':f'Starting ESP32-C6 DHT11 over {transport}' in text")
change("'quic_connected':'QUIC connection established' in text", "'transport_connected':('QUIC connection established' in text if transport=='QUIC' else 'TCP_NODELAY=1' in text)")
change("'mqtt_connected':'MQTT connected over QUIC' in text", "'mqtt_connected':f'MQTT connected over {transport}' in text")
change("'QUIC negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256' in text", "f'{transport} negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256' in text")
code=code.replace("'HBPSN-01'",'run_id').replace("'HBPSN-01/'", "run_id+'/'")
code=code.replace("transport='QUIC',condition='CONTROL'",'transport=transport,condition=condition')
code=code.replace("# HBPSN-01 QUIC CONTROL",'# {run_id} {transport} {condition}')
change("    global monitor\n    assert preflight", "    global monitor,startup_state,interruption_state\n    assert preflight")
change("    assert '40:4c:ca:56:bb:b0' in (folder/'identification.log').read_text(encoding='utf-16')", """    assert '40:4c:ca:56:bb:b0' in (folder/'identification.log').read_text(encoding='utf-16')
    before=evidence.capture('pre_run')
    if before['status']!='PASS':
        save('PREFLIGHT_BLOCKED.json',dict(reason='Missing/mismatched actual pre-reset settings evidence',evidence=before))
        raise RuntimeError('Settings preflight failed; no monitor/reset started')""")
change("str(root/'profiles/wifi_ps_none_20261103/build/quic_demo.elf')", "next(x['path'] for x in preflight['firmware_artifacts'] if x['path'].endswith('quic_demo.elf'))")
change("str(folder/'monitor_instrumented.py')", "str(Path(__file__).with_name('monitor_instrumented_v2.py'))")
change("env.update(PYTHONUNBUFFERED='1',PYTHONUTF8='1',IDF_PATH='C:/esp/v6.1/esp-idf')", "env.update(PYTHONUNBUFFERED='1',PYTHONUTF8='1',IDF_PATH='C:/esp/v6.1/esp-idf',RECORDER_RUN_DIR=str(folder))")
change("    start=event();startup=None;registered=False;interruption=[]", """    start=event();startup=None;registered=False;interruption=[]
    def finish(start,post):
        try:finalize(start,startup_state,interruption_state)
        finally:finalization_done.set()
    def save_post(post):save('post_recording_settings_check.json',post)
    cutoff,deadline_thread=arm_deadline(start,reports,evidence,finish,save_post)""")
change("        control_exit()\n        save('heartbeat.json'", "        startup_state=startup;interruption_state=interruption\n        control_exit()\n        save('heartbeat.json'")
change("    save('recording_cutoff_observed.json',dict(fixed_deadline_utc=start['deadline_utc'],observed_utc=utc(),lateness_ms=max(0,(time.monotonic()-start['deadline_monotonic'])*1000)))\n    finalize(start,startup,interruption)", "    deadline_thread.join()  # Deadline/settings/finalization worker is independent of heartbeat")
change("    stats['p90_ms']=percentile(.90);stats['p95_ms']=percentile(.95);stats['p99_ms']=percentile(.99)", "    stats['p90_ms']=percentile(.90);stats['p95_ms']=ordered[__import__('math').ceil(.95*len(ordered))-1] if ordered else None;stats['p99_ms']=percentile(.99)\n    stats['p95_method']='nearest rank ceil(0.95*N); P90/P99 retain type 7'")
# A reporting failure must not skip the manifest and final completion stage.
old="    (folder/'SUMMARY.md').write_text(text,encoding='utf-8')"
change(old,"    try:(folder/'SUMMARY.md').write_text(text,encoding='utf-8')\n    except Exception as error:reports.error('summary_report',error)")
change("    save('metadata.json',dict(**stats,collector_pid=os.getpid(),monitor_pid=monitor.pid,source_plan_sha256=preflight['plan_sha256']))", "    stats['reporting_errors']=reports.errors\n    save('metadata.json',dict(**stats,collector_pid=os.getpid(),monitor_pid=monitor.pid,source_plan_sha256=preflight['plan_sha256']))")
# Never claim that merely emitting a request applied a register update.
code=code.replace('Other 17 register entries unchanged.','Register update request emitted; application is a separate review step.')
(tools/'collector_v2.py').write_text(code,encoding='utf-8')
wrapper=(a/'monitor_instrumented.py').read_text().replace('import time','import time\nimport os').replace('folder=Path(__file__).resolve().parent',"folder=Path(os.environ['RECORDER_RUN_DIR'])")
# Immutable reset anchor: unique file creation instead of a replace susceptible to sharing locks.
wrapper=wrapper.replace('import os','import os\nfrom reliability import Reports')
wrapper=wrapper.replace("        (folder/'reset_event.tmp').write_text(json.dumps(event,indent=2))\n        (folder/'reset_event.tmp').replace(folder/'reset_event.json')", "        if not Reports(folder).save('reset_event.json',event):\n            raise RuntimeError('Reset already issued but anchor report failed; preserve fallback; never reset again')")
(tools/'monitor_instrumented_v2.py').write_text(wrapper,encoding='utf-8')
py_compile.compile(str(tools/'collector_v2.py'),doraise=True)
py_compile.compile(str(tools/'monitor_instrumented_v2.py'),doraise=True)
(tools/'test_output_path.txt').write_text(str(out))
print(out)
