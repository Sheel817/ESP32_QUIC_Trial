"""Build isolated TEST_ONLY profile. No serial/flash/reset actions."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess
root=Path(__file__).resolve().parents[1];p=root/'profiles/test_only_heap_20261106';src=p/'src'
assert (p/'identity.json').exists()
python=Path('C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe')
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',ESP_IDF_VERSION='6.1.0',IDF_PATH='C:/esp/v6.1/esp-idf',IDF_TOOLS_PATH='C:/Users/newsh/.espressif',IDF_PYTHON_ENV_PATH=str(python.parents[1]),IDF_COMPONENT_CHECK_NEW_VERSION='0',IDF_COMPONENT_MANAGER='0',ESP_ROM_ELF_DIR='C:/Users/newsh/.espressif/tools/esp-rom-elfs/20241011')
env['PATH']=';'.join([str(python.parent),'C:/Espressif/tools/cmake/4.0.3/bin','C:/Espressif/tools/ninja/1.12.1','C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin',env['PATH']])
command=[str(python),'C:/esp/v6.1/esp-idf/tools/idf.py','-B',str(p/'build'),'-DSDKCONFIG='+str(p/'sdkconfig'),'-DDEMO_TRANSPORT=QUIC','-DDEMO_WIFI_PS_NONE=ON','-DCCACHE_ENABLE=False','build']
stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ');log=p/('build_'+stamp+'.log')
record=dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),command=command,cwd=str(src),environment={k:env[k] for k in ['PYTHONUTF8','PYTHONDONTWRITEBYTECODE','ESP_IDF_VERSION','IDF_PATH','IDF_TOOLS_PATH','IDF_PYTHON_ENV_PATH','IDF_COMPONENT_CHECK_NEW_VERSION','IDF_COMPONENT_MANAGER','ESP_ROM_ELF_DIR','PATH']},log=str(log))
(p/('build_command_'+stamp+'.json')).write_text(json.dumps(record,indent=2))
with log.open('wb') as f:r=subprocess.run(command,cwd=src,env=env,stdout=f,stderr=subprocess.STDOUT)
record.update(ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),exit_code=r.returncode)
(p/('build_result_'+stamp+'.json')).write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2));raise SystemExit(r.returncode)
