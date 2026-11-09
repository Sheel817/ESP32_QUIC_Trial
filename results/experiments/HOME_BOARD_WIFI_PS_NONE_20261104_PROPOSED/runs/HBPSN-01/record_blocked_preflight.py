"""Read-only preflight evidence; no reset, flash, monitor or register mutation."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

run=Path(__file__).resolve().parent
study=run.parents[1]
root=study.parents[2]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
frozen_path=study/'freeze_manifest.json'
frozen=json.loads(frozen_path.read_text(encoding='utf-8'))
file_checks=[dict(path=e['path'],expected_sha256=e['sha256'],actual_sha256=sha(Path(e['path'])),match=sha(Path(e['path']))==e['sha256']) for e in frozen['files']]
artifacts=[dict(**e,actual_sha256=sha(Path(e['path'])),match=sha(Path(e['path']))==e['sha256']) for e in frozen['artifacts'] if e['transport']=='QUIC']
paths=['profiles/wifi_ps_none_20261103/sdkconfig','profiles/wifi_ps_none_20261103/build/config/sdkconfig.json','profiles/wifi_ps_none_20261103/build/CMakeCache.txt','profiles/wifi_ps_none_20261103/build/compile_commands.json','profiles/wifi_ps_none_20261103/build/flash_args','profiles/wifi_ps_none_20261103/build/flasher_args.json','main/quic_demo_main.c','main/CMakeLists.txt','dependencies.lock','quic_server.py']
configuration=[dict(path=str(root/p),bytes=(root/p).stat().st_size,sha256=sha(root/p)) for p in paths]
with (study/'run_register.csv').open(encoding='utf-8',newline='') as f:register=list(csv.DictReader(f))
assert len(register)==18 and all(r['status']=='NOT_RUN' for r in register)
first=register[0]
assert (first['run_id'],first['transport'],first['condition'])==('HBPSN-01','QUIC','CONTROL')
source_log=root/'results/pilots/HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_20261104T000343Z/HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_serial.log'
raw=source_log.read_bytes()
source_text=raw.decode('utf-8',errors='replace')
board_mac_evidence=[line for line in source_text.splitlines() if 'wifi:mode : sta (40:4c:ca:56:bb:b0)' in line]
expected='udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)'
observed='(udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)) or (tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568))'
result=dict(run_id='HBPSN-01',transport='QUIC',condition='CONTROL',status='PREFLIGHT_BLOCKED',registered_status='NOT_RUN',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),protocol_id=frozen['protocol_id'],plan_path=str(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),plan_sha256=sha(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),freeze_manifest_path=str(frozen_path),freeze_manifest_sha256=sha(frozen_path),frozen_file_checks=file_checks,quic_artifact_checks=artifacts,firmware_configuration_hashes=configuration,operator_reported_settings='CONTROL requested: capture running, all effects disabled; no operator-provided filter text in this request',observed_gui=dict(capture='RUNNING (Stop button and Started filtering status)',all_effects='OFF (all function checkboxes unchecked)',filter=observed,evidence_file='preflight_clumsy_20261104T001824Z.jpg',evidence_sha256=sha(run/'preflight_clumsy_20261104T001824Z.jpg')),required_filter=expected,preflight_failure='Current capture filter contains additional TCP 14568 branch; it does not match the frozen QUIC-only filter. No filter change or retry performed.',board_evidence=dict(serial_port='COM6',adapter='Silicon Labs CP210x USB to UART Bridge',usb_pnp_id='USB\\VID_10C4&PID_EA60\\FABA8DF9808FED11A981E817B96CE6F8',expected_mac='40:4c:ca:56:bb:b0',existing_monitor_log=str(source_log),existing_startup_mac_lines=board_mac_evidence,live_log_prefix_bytes=len(raw),live_log_prefix_sha256=hashlib.sha256(raw).hexdigest(),limitation='No fresh Espressif identification/reset performed because preflight was blocked before loading the profile'),actual_start_utc=None,deadline_utc=None,collector_started=False,formal_samples=0,register_modified=False,actions='Read existing files/processes/serial-port metadata and observe GUI only. No flash/reset/build/ping; current monitor, servers, Clumsy filter/effects preserved.')
result['other_hash_failures']=[x['path'] for x in file_checks+artifacts if not x['match']]
(run/'preflight_attempt_20261104T001824Z.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(run/'metadata.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
summary=f'''# HBPSN-01 QUIC CONTROL — blocked preflight

**NOT STARTED. Registered status remains NOT_RUN.** No controlled reset, recording start, deadline or formal sample exists for this attempt. The current TCP_TLS monitor and both servers remain untouched.

The frozen protocol `{frozen['protocol_id']}` requires this exact QUIC capture filter:

```text
{expected}
```

The current GUI instead shows:

```text
{observed}
```

Capture is running and all effects are unchecked. The additional TCP 14568 branch differs from the frozen transport-specific filter. Per the user's instruction to report failed checks rather than retry, no filter change, flash or reset was performed. The intended correction before a future start is the exact frozen UDP-only filter above; the run has not been silently adapted to the combined filter.

[GUI screenshot evidence](./preflight_clumsy_20261104T001824Z.jpg). The requested CONTROL/effects-off state is recorded as operator-reported; the actual filter/capture/effect-checkbox state was independently observed in the GUI.

Plan SHA-256: `{result['plan_sha256']}`. Freeze-manifest SHA-256: `{result['freeze_manifest_sha256']}`. Frozen-file checks and all four preserved QUIC firmware artifact checks match: **{not result['other_hash_failures']}**. Application SHA-256 is `6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198`. Configuration/source/flash-argument hashes and absolute paths are in [preflight evidence](./preflight_attempt_20261104T001824Z.json).

COM6 enumerates as the expected CP210x adapter; the existing monitor's startup log contains the expected HOME_BOARD MAC. A fresh Espressif identification or profile startup was not attempted after the filter check failed. Both run-register files are unchanged and all 18 rows remain NOT_RUN.

No 37-minute timer or collection was started, and no RUNNING status or finish time is claimed. This is setup-failure evidence, not a failed measured boot or a replacement run.
'''
(run/'PREFLIGHT_BLOCKED.md').write_text(summary,encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','registered_status','plan_sha256','freeze_manifest_sha256','other_hash_failures','actual_start_utc','deadline_utc','register_modified')},indent=2))
