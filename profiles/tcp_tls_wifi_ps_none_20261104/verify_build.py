import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

profile=Path(__file__).resolve().parent
root=profile.parents[1]
quic=root/'profiles/wifi_ps_none_20261103'
build=profile/'build'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(base):
    result={}
    for current,dirs,files in os.walk(base,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(current)/d).is_symlink() and not (Path(current)/d).is_junction() and d!='node_modules']
        for name in files:
            p=Path(current)/name
            if not p.is_symlink():result[p.relative_to(base).as_posix()]=sha(p)
    return result
before=json.loads((profile/'preservation_before.json').read_text())
preservation={}
for key,path in [('original_build',root/'build'),('quic_profile',quic)]:
    after=inventory(path)
    old=before[key]
    changes=[n for n in old if old[n]!=after.get(n)]
    additions=sorted(set(after)-set(old))
    preservation[key]=dict(files=len(old),changed_or_missing=changes,added=additions)
    assert not changes and not additions,preservation[key]
source=json.loads((profile/'source_before.json').read_text())
source_changed=[n for n,h in source.items() if not (root/n).exists() or sha(root/n)!=h]
assert not source_changed,source_changed
result=json.loads((profile/'build_result.json').read_text(encoding='utf-8-sig'))
assert result['exit_code']==0
log=(profile/'build.log').read_text(encoding='utf-16')
assert 'Project build complete.' in log and 'Linking CXX executable quic_demo.elf' in log
def config(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if s.startswith('CONFIG_') and '=' in s)
qconfig=config(quic/'sdkconfig')
tconfig=config(profile/'sdkconfig')
config_diff={n:dict(quic=qconfig.get(n),tcp_tls=tconfig.get(n)) for n in qconfig.keys()|tconfig.keys() if qconfig.get(n)!=tconfig.get(n)}
assert not config_diff,config_diff
qgenerated=json.loads((quic/'build/config/sdkconfig.json').read_text())
tgenerated=json.loads((build/'config/sdkconfig.json').read_text())
assert qgenerated==tgenerated
qproject=json.loads((quic/'build/project_description.json').read_text())
tproject=json.loads((build/'project_description.json').read_text())
assert qproject['idf_path']==tproject['idf_path'] and qproject['git_revision']==tproject['git_revision']
assert qproject['project_version']==tproject['project_version']
for language in ('C','CXX'):
    a=(quic/f'build/CMakeFiles/4.0.3/CMake{language}Compiler.cmake').read_text()
    b=(build/f'CMakeFiles/4.0.3/CMake{language}Compiler.cmake').read_text()
    for key in (f'CMAKE_{language}_COMPILER',f'CMAKE_{language}_COMPILER_VERSION'):
        pattern=re.compile(r'set\('+key+r' "([^"]+)"\)')
        assert pattern.search(a)[1]==pattern.search(b)[1]
commands=json.loads((build/'compile_commands.json').read_text())
main=[r['command'] for r in commands if r['file'].replace('\\','/').endswith('/main/quic_demo_main.c')]
assert main and all('-DDEMO_TRANSPORT_TCP_TLS=1' in s and '-DDEMO_WIFI_PS_NONE=1' in s for s in main)
cache=(build/'CMakeCache.txt').read_text()
assert 'DEMO_TRANSPORT:STRING=TCP_TLS' in cache and 'DEMO_WIFI_PS_NONE:BOOL=ON' in cache
artifacts={n:dict(path=str(build/n),bytes=(build/n).stat().st_size,sha256=sha(build/n)) for n in ('quic_demo.bin','quic_demo.elf','bootloader/bootloader.bin','partition_table/partition-table.bin','flash_args','flasher_args.json')}
app_size=artifacts['quic_demo.bin']['bytes']
assert app_size<=1740800
python='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
image_info=subprocess.check_output([python,'-m','esptool','image-info',str(build/'quic_demo.bin')],text=True)
(profile/'image_info.txt').write_text(image_info)
assert 'Checksum:' in image_info and '(valid)' in image_info and artifacts['quic_demo.elf']['sha256'] in image_info
validation=dict(result='PASS',build_exit_code=0,link='PASS',application_partition_check='PASS',app_partition_bytes=1740800,app_free_bytes=1740800-app_size,bootloader_partition_check='PASS' if re.search(r'Bootloader binary size .*free',log) else 'NOT_FOUND',image_integrity='PASS',artifacts=artifacts,preservation=preservation,source_config_changes=source_changed,dependency_lock_unchanged=True,effective_sdkconfig_differences=config_diff,generated_sdkconfig_equal=True,sdk='ESP-IDF v6.1',compiler='GCC/G++ 15.2.0; same executable paths as validated QUIC',project_version=tproject['project_version'],compile_definitions=dict(DEMO_TRANSPORT_TCP_TLS=1,DEMO_WIFI_PS_NONE=1),intended_differences=['DEMO_TRANSPORT: QUIC -> TCP_TLS','DEMO_TRANSPORT_TCP_TLS: 0 -> 1','Existing transport branch: UDP 14567 QUIC -> TCP 14568 TLS; existing TCP_NODELAY and TLS path','Separate SDKCONFIG/build paths; build timestamps and resulting binaries differ'],warnings=[s for s in log.splitlines() if re.search(r'warning:|WARNING:|OSError:|Error while generating',s,re.I)],flashed=False,runtime_verified=False)
assert validation['bootloader_partition_check']=='PASS'
(profile/'validation.json').write_text(json.dumps(validation,indent=2))
command=(profile/'build_profile.ps1').read_text()
artifact_table='\n'.join(f"| {n} | {v['bytes']} | `{v['sha256']}` |" for n,v in artifacts.items())
report=f'''# TCP_TLS WIFI_PS_NONE matching build

Built only. Not flashed or reset; runtime behavior is not yet verified.

Build/link, bootloader/application partition checks and offline image checksum/digest verification **PASS**. Application partition 1,740,800 bytes; free {1740800-app_size:,} bytes. Same modified source revision as validated QUIC: Git HEAD 3c8c7a30b7b32ae3feaa07788b74eec637be37fc, project version {tproject['project_version']}; source content hashes are authoritative because the tree is modified.

| Artifact under build/ | Bytes | SHA-256 |
|---|---:|---|
{artifact_table}

[Image](./build/quic_demo.bin), [ELF](./build/quic_demo.elf), [build log](./build.log), [full validation/preservation report](./validation.json), [source identity](./source_identity.json), [image descriptor](./image_info.txt).

## Exact command and environment

Run the following lines from the project root. The host's Restricted PowerShell script policy did not execute the first script-file invocation; no build ran in that attempt. The successful build executed these same environment assignments and idf.py command inline without changing that policy. The retained build_profile.ps1 records the command for reproducibility.

```powershell
{command}
```

## Differences from validated QUIC PS_NONE

- DEMO_TRANSPORT=TCP_TLS instead of QUIC; DEMO_TRANSPORT_TCP_TLS=1 instead of 0. DEMO_WIFI_PS_NONE stays ON / 1.
- Separate profile sdkconfig and output paths. Effective CONFIG_ entries and generated sdkconfig JSON are identical. ESP-IDF v6.1 and GCC/G++ 15.2.0 executable paths match. Dependency lock and preserved source/configuration inputs are unchanged.
- The existing transport branch selects TCP+TLS at port 14568 instead of QUIC UDP 14567. Existing TLS 1.3 / AES-128-GCM / ALPN mqtt requirements and TCP_NODELAY checks apply. No firmware logic was edited. DHT11 GPIO4, payload, topic/client ID, QoS 0, five-second sampling, APP_RTT timing, loop cadence and quiet logging remain shared and unchanged.
- Build timestamps and transport-specific link contents cause different BIN/ELF sizes/hashes. No dependency upgrade was performed.

All {preservation['original_build']['files']} inventoried original-build files and {preservation['quic_profile']['files']} QUIC-profile files remain hash-identical, with no added/missing files in those inventories. Linked node_modules directories were excluded. All {len(source)} recorded source/config inputs remain unchanged.

Warnings are preserved in validation.json and build.log. They include the established missing ESP_ROM_ELF_DIR GDB-symbol setup warning, SDK Kconfig/component notices, generic ESP-TLS/wolfSSL notice and ngtcp2 maybe-uninitialized warning where emitted. The inline invocation used forward-slash IDF_PYTHON_ENV_PATH spelling, producing a venv-path string comparison warning; the invoked interpreter is the same installed idf6.1_py3.14_env. No packages/environment were upgraded to address warnings. Firmware linking and partition validation succeeded.
'''
(profile/'README.md').write_text(report,encoding='utf-8')
print(json.dumps(validation,indent=2))
