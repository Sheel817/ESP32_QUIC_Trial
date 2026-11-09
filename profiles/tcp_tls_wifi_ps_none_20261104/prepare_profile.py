"""Audit source identity and preserve existing builds before isolated build."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

profile=Path(__file__).resolve().parent
root=profile.parents[1]
quic=root/'profiles/wifi_ps_none_20261103'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
refs=json.loads((root/'results/pilots/HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/source_references.json').read_text())
for entry in refs:
    p=Path(entry['path'])
    if p in (root/'main/quic_demo_main.c',root/'main/CMakeLists.txt'):
        assert sha(p)==entry['sha256'],f'Validated QUIC source changed: {p}'
assert sha(quic/'build/quic_demo.bin')=='6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198'
manifest=json.loads(Path('C:/Users/newsh/Desktop/ESP32_QUIC_Checkpoints/pre_wifi_ps_none_20261103T162643Z/manifest.json').read_text())
for name,entry in manifest.items():
    if name in ('main/CMakeLists.txt','main/quic_demo_main.c'):continue
    if name.startswith(('main/','components/','managed_components/')) or name in ('CMakeLists.txt','sdkconfig','dependencies.lock','sdkconfig.defaults','partitions.csv'):
        p=root/name
        assert p.exists() and sha(p)==entry['sha256'],f'Unexpected preserved source/config change: {name}'
def inventory(base):
    result={}
    for current,dirs,files in os.walk(base,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(current)/d).is_symlink() and not (Path(current)/d).is_junction() and d!='node_modules']
        for name in files:
            p=Path(current)/name
            if p.is_symlink():continue
            result[p.relative_to(base).as_posix()]=sha(p)
    return result
preserved={'original_build':inventory(root/'build'),'quic_profile':inventory(quic)}
(profile/'preservation_before.json').write_text(json.dumps(preserved,indent=2))
source={}
for directory in ('main','components','managed_components'):
    for name,digest in inventory(root/directory).items():source[f'{directory}/{name}']=digest
for name in ('CMakeLists.txt','sdkconfig','sdkconfig.defaults','dependencies.lock','partitions.csv','quic_server.py','tcp_tls_server.py','server-cert.pem'):
    source[name]=sha(root/name)
(profile/'source_before.json').write_text(json.dumps(source,indent=2))
shutil.copyfile(quic/'sdkconfig',profile/'sdkconfig')
script=(quic/'build_profile.ps1').read_text().replace('profiles/wifi_ps_none_20261103','profiles/tcp_tls_wifi_ps_none_20261104').replace('-DDEMO_TRANSPORT=QUIC','-DDEMO_TRANSPORT=TCP_TLS')
(profile/'build_profile.ps1').write_text(script)
identity=dict(git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),project_version='3c8c7a3-dirty',source_identity='Current modified tree; validated QUIC application/CMake hashes and preserved source/dependency entries verified',original_build_files=len(preserved['original_build']),quic_profile_files=len(preserved['quic_profile']),source_files=len(source),sdk='C:/esp/v6.1/esp-idf',compiler='GCC/G++ 15.2.0; esp-15.2.0_20251204',python_environment='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env',packages_upgraded=False)
(profile/'source_identity.json').write_text(json.dumps(identity,indent=2))
print(json.dumps(identity,indent=2))
