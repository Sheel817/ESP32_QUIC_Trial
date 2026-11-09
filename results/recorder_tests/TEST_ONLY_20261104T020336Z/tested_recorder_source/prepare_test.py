"""Create isolated evidence directory and freeze exact host code under test."""
from pathlib import Path
import datetime as dt,hashlib,json,shutil

tools=Path(__file__).resolve().parent;root=tools.parents[1]
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
a=study/'runs/HBPSN-01/attempt_20261104T002840Z'
out=root/'results/recorder_tests'/('TEST_ONLY_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=tools/'test_output_path.txt'
previous=old.read_text().strip() if old.exists() else None
preserved=out/'preserved_failure';preserved.mkdir()
for name in ['collector.py','collector_failure.json','heartbeat.json','heartbeat.json.tmp','monitor_instrumented.py']:
    shutil.copy2(a/name,preserved/name)
live={'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'}
originals=[p for p in (study/'runs/HBPSN-01').rglob('*') if p.is_file() and p.name not in live and '__pycache__' not in p.parts]
originals += [study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'freeze_manifest.json',study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx']
(out/'protected_original_hashes.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in originals],indent=2))
snapshot=out/'tested_recorder_source';snapshot.mkdir()
code=[p for p in tools.iterdir() if p.suffix in ('.py','.md')]
for p in code:shutil.copy2(p,snapshot/p.name)
(out/'tested_code_hashes.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in code],indent=2))
(out/'TEST_ONLY_metadata.json').write_text(json.dumps(dict(test_only=True,created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),previous_test=previous,source='synthetic only; actual read-only Clumsy screenshots',formal_register_write=False),indent=2))
old.write_text(str(out))
print(out)
