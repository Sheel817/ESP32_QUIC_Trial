import datetime as dt
import hashlib
import json
from pathlib import Path
import re

folder = Path(__file__).resolve().parent
root = folder.parents[2]
profile = root/'profiles/wifi_ps_none_20261103'
build = profile/'build'
reference = root/'results/pilots/HOME_BOARD_PS_DEFAULT_20261103T225407Z'
checkpoint = Path('C:/Users/newsh/Desktop/ESP32_QUIC_Checkpoints/pre_wifi_ps_none_20261103T162643Z')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
report = json.loads((profile/'validation.json').read_text())
assert sha(build/'quic_demo.bin') == report['image_sha256']
assert (build/'quic_demo.bin').stat().st_size == report['image_bytes']
def config(p):
    return dict(line.split('=',1) for line in p.read_text().splitlines() if line.startswith('CONFIG_') and '=' in line)
assert config(profile/'sdkconfig') == config(root/'sdkconfig')
assert json.loads((build/'config/sdkconfig.json').read_text()) == json.loads((root/'build/config/sdkconfig.json').read_text())
for lang in ('C','CXX'):
    a = (build/f'CMakeFiles/4.0.3/CMake{lang}Compiler.cmake').read_text()
    b = (root/f'build/CMakeFiles/4.0.3/CMake{lang}Compiler.cmake').read_text()
    for key in (f'CMAKE_{lang}_COMPILER', f'CMAKE_{lang}_COMPILER_VERSION'):
        pattern = re.compile(r'set\('+key+r' "([^"]+)"\)')
        assert pattern.search(a)[1] == pattern.search(b)[1]
projects = [json.loads((x/'project_description.json').read_text()) for x in (root/'build',build)]
assert projects[0]['idf_path'] == projects[1]['idf_path'] == 'C:/esp/v6.1/esp-idf'
assert projects[0]['git_revision'] == projects[1]['git_revision'] == 'v6.1'
source = (root/'main/quic_demo_main.c').read_text()
without = source.replace('#include "esp_wifi.h"\n','')
without = re.sub(r'#if DEMO_WIFI_PS_NONE\n.*?#endif\n\n','',without,flags=re.S)
assert without == (reference/'preserved_original_quic_demo_main.c.txt').read_text(), 'Unexpected app/timing changes'
cache = (build/'CMakeCache.txt').read_text()
assert 'DEMO_TRANSPORT:STRING=QUIC' in cache and 'DEMO_WIFI_PS_NONE:BOOL=ON' in cache
commands = json.loads((build/'compile_commands.json').read_text())
main_commands = [x['command'] for x in commands if x['file'].replace('\\','/').endswith('/main/quic_demo_main.c')]
assert main_commands and all('-DDEMO_WIFI_PS_NONE=1' in x and '-DDEMO_TRANSPORT_TCP_TLS=0' in x for x in main_commands)
manifest = json.loads((checkpoint/'manifest.json').read_text())
changes = []
for name, entry in manifest.items():
    if name.startswith(('build/','profiles/')) or name in ('main/CMakeLists.txt','main/quic_demo_main.c'):
        continue
    if name.startswith(('main/','components/','managed_components/')) or name in ('sdkconfig','dependencies.lock'):
        p = root/name
        if not p.exists() or sha(p) != entry['sha256']:
            changes.append(name)
assert not changes, changes
artifacts = {str(p.relative_to(build)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in [build/'bootloader/bootloader.bin',build/'partition_table/partition-table.bin',build/'quic_demo.bin',build/'quic_demo.elf',build/'flash_args',build/'flasher_args.json']}
result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),condition='HOME_BOARD WIFI_PS_NONE; Clumsy stopped',result='PASS',sdk='ESP-IDF v6.1, same SDK path',compiler='GCC/G++ 15.2.0, same executable paths',effective_sdkconfig_equal=True,compiled_sdkconfig_equal=True,transport='QUIC',wifi_ps_none=1,app_source_after_removing_intended_block_matches_original=True,unexpected_preserved_source_config_changes=changes,artifacts=artifacts,python_environment='C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env; documented host tooling change; monitor 1.10.0; esptool 5.6.0',warnings=['Missing ESP_ROM_ELF_DIR: GDB ROM symbol initialization only; build completed','Component include/dependency validation notices','wolfSSL not selected for generic ESP-TLS; QUIC uses its own wolfSSL integration, same effective SDK config','ngtcp2_acktr.c:292 ent may be used uninitialized; underlying preserved dependency source unchanged; no rebuild or fix performed'],material_unintended_difference_found=False)
(folder/'preflash_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
