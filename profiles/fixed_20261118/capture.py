"""Serial capture (FIXED profile test runs) for COM6. Usage: python -I capture.py <out_prefix> [--reset] [--max-seconds N]
Logs every received line with a host UTC timestamp. Optional single board reset by RTS pulse at start.
Stops (gracefully, closes the port) on 'TEST COMPLETE', a stop file '<out_prefix>.stop', max seconds, or 180 s without any output."""
import sys, time, datetime as dt
from pathlib import Path
import serial
prefix = Path(sys.argv[1]); do_reset = '--reset' in sys.argv
mx = int(sys.argv[sys.argv.index('--max-seconds') + 1]) if '--max-seconds' in sys.argv else 3600
log = open(str(prefix) + '.log', 'ab', buffering=0)
def stamp(): return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
s = serial.Serial('COM6', 115200, timeout=0.2, dsrdtr=False, rtscts=False)
s.dtr = False; s.rts = False
log.write(f'{stamp()} CAPTURE_OPEN reset={do_reset}\n'.encode())
if do_reset:
    s.rts = True; time.sleep(0.15); s.rts = False
    log.write(f'{stamp()} RESET_RELEASED_BY_HOST\n'.encode())
buf = b''; t0 = time.time(); last = time.time(); reason = 'max_seconds'
stopf = Path(str(prefix) + '.stop')
while time.time() - t0 < mx:
    if stopf.exists(): reason = 'stop_file'; break
    d = s.read(512)
    if d:
        last = time.time(); buf += d
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            log.write(stamp().encode() + b' ' + line.rstrip(b'\r') + b'\n')
            if b'TEST COMPLETE' in line: reason = 'test_complete'; t0 = -1e9
    elif time.time() - last > 180: reason = 'silent_180s'; break
    if t0 == -1e9: break
if buf: log.write(stamp().encode() + b' ' + buf + b'\n')
log.write(f'{stamp()} CAPTURE_CLOSE reason={reason}\n'.encode())
s.close(); log.close(); print('closed', reason)
