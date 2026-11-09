"""Keep ESP-IDF monitor and its stdin alive; one logged startup reset only."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

folder = Path(__file__).resolve().parent
root = folder.parents[2]
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
env = os.environ.copy()
env.update(PYTHONUNBUFFERED='1', PYTHONUTF8='1', IDF_PATH='C:/esp/v6.1/esp-idf')
command = [sys.executable, '-u', '-m', 'esp_idf_monitor', '--port', 'COM6',
           '--baud', '115200', '--target', 'esp32c6', '--no-reset',
           '--disable-auto-color', '--timestamps', '--timestamp-format',
           '%Y-%m-%dT%H:%M:%S%z', str(root / 'profiles/wifi_ps_none_20261103/build/quic_demo.elf')]
metadata = dict(label='HOME_BOARD experimental WIFI_PS_NONE firmware; Clumsy stopped',
                started_utc=utc(), wrapper_pid=os.getpid(), command=command,
                clumsy_evidence='UI observed Start button and Stopped status; Lag unchecked before startup')
with (folder / 'HOME_BOARD_WIFI_PS_NONE_serial.log').open('ab', buffering=0) as output:
    proc = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.PIPE,
                            stdout=output, stderr=subprocess.STDOUT)
    metadata['monitor_pid'] = proc.pid
    time.sleep(2)
    if proc.poll() is not None:
        raise RuntimeError(f'monitor exited {proc.returncode}')
    metadata['controlled_reset_requested_utc'] = utc()
    proc.stdin.write(b'reset\n')
    proc.stdin.flush()
    (folder / 'monitor_session.json').write_text(json.dumps(metadata, indent=2))
    while proc.poll() is None:
        control = folder / 'monitor_control.txt'
        if control.exists():
            request = control.read_text().strip()
            control.unlink()
            if request == 'exit':
                proc.stdin.write(b'exit\n')
                proc.stdin.flush()
        time.sleep(0.25)
    metadata.update(ended_utc=utc(), exit_code=proc.returncode)
    (folder / 'monitor_session.json').write_text(json.dumps(metadata, indent=2))

