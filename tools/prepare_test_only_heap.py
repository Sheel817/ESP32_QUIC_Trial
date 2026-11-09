"""Prepare private TEST_ONLY source copies; no device or process operations."""
from pathlib import Path
import datetime as dt,hashlib,json,shutil,os
root=Path(__file__).resolve().parents[1]
profile=root/'profiles/test_only_heap_20261106';src=profile/'src'
profile.mkdir(exist_ok=True);src.mkdir(exist_ok=True)
assert not (profile/'identity.json').exists(), 'Do not reuse completed preparation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(profile/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
manifest_path=root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json'
manifest=json.loads(manifest_path.read_text())
assert sha(manifest_path)=='fab4baf0273fbe485e6c73566cd57ff130834152c991867822df91e4e3ceb8cd'
for rel,expected in manifest.items():assert sha(root/rel)==expected,rel
save('baseline_source_manifest.json',manifest)
protected=set(root/r for r in manifest)
for base in [root/'build',root/'profiles/wifi_ps_none_20261103',root/'profiles/tcp_tls_wifi_ps_none_20261104']:
    for directory,dirs,files in os.walk(base,followlinks=False):
        dirs[:]=[d for d in dirs if d not in {'node_modules','__pycache__'} and not (Path(directory)/d).is_symlink() and not (Path(directory)/d).is_junction()]
        protected.update(Path(directory)/n for n in files)
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
for directory,dirs,files in os.walk(study,followlinks=False):
    dirs[:]=[d for d in dirs if d not in {'node_modules','__pycache__'} and not (Path(directory)/d).is_symlink()]
    protected.update(Path(directory)/n for n in files if n not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log'})
protected.add(root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx')
save('protected_before.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(protected)])
for rel in manifest:
    target=src/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,target)
shutil.copy2(root/'profiles/wifi_ps_none_20261103/sdkconfig',profile/'sdkconfig')
shutil.copy2(root/'profiles/wifi_ps_none_20261103/sdkconfig',profile/'sdkconfig.baseline')
shutil.copy2(root/'profiles/wifi_ps_none_20261103/build/compile_commands.json',profile/'formal_compile_commands.snapshot.json')
save('identity.json',dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),label='TEST_ONLY',baseline_manifest=str(manifest_path),baseline_files=len(manifest),all_baseline_hashes_match=True,source=str(src),build=str(profile/'build'),board_action='NONE',private_dependency_copies=True))
print(profile)
