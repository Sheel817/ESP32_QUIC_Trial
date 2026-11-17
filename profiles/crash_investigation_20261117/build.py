"""Build one DIAGNOSTIC image. Usage: python -I build.py <tag> <mode 0|1|2> <run_id> <checkpoints 0|1> [cycles]
No serial/flash/reset actions."""
from pathlib import Path
import datetime as dt, hashlib, json, os, shutil, subprocess, sys
tag, mode, run_id, cps = sys.argv[1:5]
cycles = sys.argv[5] if len(sys.argv) > 5 else '30'
p = Path(__file__).resolve().parent; src = p / 'src'
python = Path('C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe')
env = os.environ.copy()
env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', ESP_IDF_VERSION='6.1.0', IDF_PATH='C:/esp/v6.1/esp-idf', IDF_TOOLS_PATH='C:/Users/newsh/.espressif',
           IDF_PYTHON_ENV_PATH=str(python.parents[1]), IDF_COMPONENT_CHECK_NEW_VERSION='0', IDF_COMPONENT_MANAGER='0', ESP_ROM_ELF_DIR='C:/Users/newsh/.espressif/tools/esp-rom-elfs/20241011')
env['PATH'] = ';'.join([str(python.parent), 'C:/Espressif/tools/cmake/4.0.3/bin', 'C:/Espressif/tools/ninja/1.12.1',
                        'C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin', env['PATH']])
cfg = p / f'sdkconfig_{tag}'
shutil.copy2(p / 'sdkconfig', cfg)
command = [str(python), 'C:/esp/v6.1/esp-idf/tools/idf.py', '-B', str(p / f'build_{tag}'), '-DSDKCONFIG=' + str(cfg),
           '-DDEMO_TRANSPORT=QUIC', '-DDEMO_WIFI_PS_NONE=ON', '-DCCACHE_ENABLE=False', f'-DDIAG_MODE={mode}', f'-DDIAG_RUN_ID={run_id}',
           f'-DDIAG_CHECKPOINTS={cps}', f'-DDIAG_CYCLES={cycles}', 'build']
stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); log = p / f'build_{tag}_{stamp}.log'
rec = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), command=command, cwd=str(src), log=str(log))
with log.open('wb') as f:
    r = subprocess.run(command, cwd=src, env=env, stdout=f, stderr=subprocess.STDOUT)
rec.update(ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(), exit_code=r.returncode)
b = p / f'build_{tag}' / 'quic_demo.bin'
if b.exists():
    rec['bin'] = dict(path=str(b), bytes=b.stat().st_size, sha256=hashlib.sha256(b.read_bytes()).hexdigest())
(p / f'build_result_{tag}_{stamp}.json').write_text(json.dumps(rec, indent=2))
print(json.dumps({k: rec[k] for k in ('exit_code', 'bin') if k in rec}))
