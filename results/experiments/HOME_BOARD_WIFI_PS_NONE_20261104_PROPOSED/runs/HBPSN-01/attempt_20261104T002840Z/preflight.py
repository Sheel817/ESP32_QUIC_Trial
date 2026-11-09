import csv,datetime as dt,hashlib,json,shutil
from pathlib import Path
folder=Path(__file__).resolve().parent
study=folder.parents[2];root=study.parents[2]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
freeze=study/'freeze_manifest.json';manifest=json.loads(freeze.read_text())
for e in manifest['files']:assert sha(Path(e['path']))==e['sha256'],e['path']
artifacts=[e for e in manifest['artifacts'] if e['transport']=='QUIC']
for e in artifacts:assert sha(Path(e['path']))==e['sha256'],e['path']
with(study/'run_register.csv').open(newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==18 and all(r['status']=='NOT_RUN' for r in rows)
assert [rows[0][k] for k in ('run_id','transport','condition')]==['HBPSN-01','QUIC','CONTROL']
source_manifest=root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json'
for name,h in json.loads(source_manifest.read_text()).items():assert sha(root/name)==h,name
config_paths=['profiles/wifi_ps_none_20261103/sdkconfig','profiles/wifi_ps_none_20261103/build/config/sdkconfig.json','profiles/wifi_ps_none_20261103/build/CMakeCache.txt','profiles/wifi_ps_none_20261103/build/compile_commands.json','profiles/wifi_ps_none_20261103/build/flash_args','profiles/wifi_ps_none_20261103/build/flasher_args.json','dependencies.lock','quic_server.py','server-cert.pem']
old=study/'runs/HBPSN-01'
failed=[p for p in old.glob('*') if p.is_file() and p.name in ('metadata.json','preflight_attempt_20261104T001824Z.json','PREFLIGHT_BLOCKED.md','preflight_clumsy_20261104T001824Z.jpg')]
checks=json.loads((folder/'system_preflight.json').read_text(encoding='utf-8-sig'))
assert checks['port']['DeviceID']=='COM6' and checks['server']['OwningProcess']==23100
result=dict(status='PASS',run_id='HBPSN-01',transport='QUIC',condition='CONTROL',checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),protocol_id=manifest['protocol_id'],plan_path=str(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),plan_sha256=sha(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),freeze_manifest_path=str(freeze),freeze_manifest_sha256=sha(freeze),firmware_artifacts=artifacts,configuration=[dict(path=str(root/p),sha256=sha(root/p)) for p in config_paths],source_manifest_path=str(source_manifest),source_manifest_sha256=sha(source_manifest),failed_preflight_preserved=[dict(path=str(p),sha256=sha(p)) for p in failed],clumsy=dict(operator_report='User reports corrected frozen QUIC filter; CONTROL capture running, effects off required',observed_filter='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)',capture='RUNNING; Stop button',effects='All function checkboxes unchecked',evidence='clumsy_preflight.jpg',evidence_sha256=sha(folder/'clumsy_preflight.jpg')),server_log_sources={'stdout':str(root/'logs/quic_server_start_20261103T163259.stdout.log'),'stderr':str(root/'logs/quic_server_start_20261103T163259.stderr.log')},server_sensor_source=str(root/'logs/sensor_20261103T143300_220342Z_c7ett8c2.csv'),system=checks)
for p in result['server_log_sources'].values():assert Path(p).exists()
for name in ('run_register.csv',):shutil.copyfile(study/name,folder/('before_'+name))
shutil.copyfile(root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',folder/'before_run_register.xlsx')
(folder/'preflight.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(status='PASS',plan_sha256=result['plan_sha256'],firmware_sha256=artifacts[0]['sha256'],failed_preflight_preserved=len(failed)),indent=2))
