"""Graceful HBPSN-09 monitor close through the collector control file. Never opens COM6, never force-stops."""
import datetime as dt, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

A = Path(r'C:\Users\newsh\Desktop\ESP32_QUIC_Trial\results\experiments\HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED\runs\HBPSN-09\attempt_20261109T183955Z')
PIDS = [37648, 9492, 32352, 9592]
utc = lambda: dt.datetime.now(dt.timezone.utc).isoformat()


def ps(cmd):
    return subprocess.run(['powershell.exe', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=60).stdout


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def procs():
    out = ps("Get-CimInstance Win32_Process -Filter \"ProcessId=37648 OR ProcessId=9492 OR ProcessId=32352 OR ProcessId=9592\" | ForEach-Object { [string]$_.ProcessId + '|' + $_.CommandLine }")
    return {int(l.split('|', 1)[0]): l.split('|', 1)[1] for l in out.splitlines() if '|' in l}


# Step 1: pre-checks
p = procs()
print('pre: running', sorted(p))
if sorted(p) != sorted(PIDS):
    sys.exit('STOP: the four PIDs are not all present')
for pid in (37648, 9492):
    assert str(A / 'collector_v2.py') in p[pid] and '--run-dir' in p[pid], p[pid]
for pid in (32352, 9592):
    assert str(A / 'monitor_instrumented_v2.py') in p[pid] and '--no-reset' in p[pid] and 'COM6' in p[pid], p[pid]
control = A / 'monitor_control.txt'
assert not control.exists() and not (A / 'monitor_exit.json').exists() and not list(A.glob('monitor_exit_requested_*'))
assert b'ESP-ROM' not in (A / 'monitor_after_run.log').read_bytes(), 'ROM banner in after-run log'
assert sh(A / 'SHA256SUMS.json') == 'b71d8ab6bd7836a4b2a8ef41c9e63ac1c9a695ece3bb62e0def4f6b3ded25ded', 'manifest changed'
print('pre-checks pass', utc())

# Step 2: the only action
tmp = A / 'monitor_control.txt.tmp'
tmp.write_bytes(b'exit\r\n')
os.replace(tmp, control)
print('request written', utc())

# Step 3: wait up to 30 s
until = time.monotonic() + 30
left = PIDS
while time.monotonic() < until:
    left = sorted(procs())
    if not left and (A / 'monitor_exit.json').exists():
        break
    time.sleep(0.5)
print('after wait', utc(), 'still running', left, 'monitor_exit.json', (A / 'monitor_exit.json').exists(), 'control file still present', control.exists())
if left or not (A / 'monitor_exit.json').exists():
    sys.exit('STOP: monitor chain did not finish within 30 s; nothing force-stopped and manifest not touched')

# Step 4: checks after close
stream, after = (A / 'monitor_stream.log').read_bytes(), (A / 'monitor_after_run.log').read_bytes()
print('monitor_exit.json', (A / 'monitor_exit.json').read_text(encoding='utf-8'))
print('stream tail', stream[-170:])
print('after-run tail', after[-170:])
print("exit command in stream", b"Command: 'exit'" in stream, 'in after-run', b"Command: 'exit'" in after)
print('ROM banners after-run', after.count(b'ESP-ROM'), 'Guru', after.count(b'Guru Meditation'))
print('processes naming COM6:', ps("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'COM6' -and $_.ProcessId -ne $PID } | ForEach-Object { [string]$_.ProcessId + ' ' + $_.Name }").strip() or 'none')

# Step 5: manifest
requested = sorted(A.glob('monitor_exit_requested_*'))
assert len(requested) == 1
ts = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
mf = A / 'SHA256SUMS.json'
bak = mf.with_name(mf.name + '.bak_' + ts)
assert not bak.exists()
shutil.copy2(mf, bak)
assert sh(bak) == sh(mf)
items = json.loads(mf.read_text(encoding='utf-8'))
files = [A / 'monitor_stream.log', A / 'monitor_after_run.log', A / 'monitor_exit.json', requested[0], bak]
add = [dict(path=f.name, bytes=f.stat().st_size, sha256=sh(f)) for f in files]
assert not {e['path'] for e in items} & {e['path'] for e in add}
mf.write_text(json.dumps(items + add, indent=2), encoding='utf-8')
print('manifest entries', len(items) + len(add))
for e in add:
    print(e['path'], e['bytes'], e['sha256'])
print('SHA256SUMS.json', sh(mf))
final = json.loads(mf.read_text(encoding='utf-8'))
print('entries in attempt folder matching:', sum(1 for e in final if (A / e['path']).exists() and sh(A / e['path']) == e['sha256']), 'of', len(final), '(4 register entries live outside the folder)')
