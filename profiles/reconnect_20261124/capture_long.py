"""Long-run serial capture for COM6 (fixed profile, normal network).
Usage: python -I capture_long.py <out_prefix> --seconds N [--reset] [--port COMx] [--stop-after-line TEXT]
 - Logs every received line as '<UTC host timestamp> <line>'. One board reset by RTS pulse at start (optional). NEVER resets again.
 - Runs for N seconds measured from the reset release (monotonic clock). No stop on silence; a crash or disconnect of the board is only
   recorded (events file) and logging continues. Serial errors: the port is reopened every second, nothing is sent to the board.
 - Writes <prefix>.status.json every 30 s (for the operator), <prefix>.events.log for boot/panic markers.
 - Stops early only if '<prefix>.stop' exists or --stop-after-line text is seen. Closes the port gracefully at the end."""
import sys, time, json, datetime as dt, re
from pathlib import Path
import serial

prefix = Path(sys.argv[1]); do_reset = '--reset' in sys.argv
PORT = sys.argv[sys.argv.index('--port') + 1] if '--port' in sys.argv else 'COM6'  # RECONNECT PROFILE: two boards
seconds = int(sys.argv[sys.argv.index('--seconds') + 1])
stop_text = sys.argv[sys.argv.index('--stop-after-line') + 1].encode() if '--stop-after-line' in sys.argv else None
log = open(str(prefix) + '.log', 'ab', buffering=0)
ev = open(str(prefix) + '.events.log', 'ab', buffering=0)
stopf = Path(str(prefix) + '.stop'); statusf = Path(str(prefix) + '.status.json')
stamp = lambda: dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
PANIC = re.compile(rb'Guru Meditation|Load access fault|Store access fault|abort\(\)|Backtrace:|CORRUPT HEAP|Task watchdog|panic', re.I)
BOOT = re.compile(rb'ESP-IDF v[0-9.]+ 2nd stage bootloader|rst:0x|Starting ESP32-C6 DHT11 over')
DISC = re.compile(rb'Task stopped\. Restart board|Cleaning up .* connection|TLS read / peer disconnected|process returned an error|connection (lost|closed)|Wi-Fi disconnected|Disconnected', re.I)
counts = dict(lines=0, boots=0, panics=0, disconnect_markers=0, rtt_lines=0, serial_errors=0)
last_line = ''; last_rx = time.time()


def note(kind, line=b''):
    ev.write(f'{stamp()} {kind} {line.decode("utf-8", "replace")[:200]}\n'.encode())


def open_port():
    s = serial.Serial(PORT, 115200, timeout=0.2, dsrdtr=False, rtscts=False)
    s.dtr = False; s.rts = False
    return s


s = open_port()
log.write(f'{stamp()} CAPTURE_OPEN reset={do_reset}\n'.encode())
if do_reset:
    s.rts = True; time.sleep(0.15); s.rts = False
    log.write(f'{stamp()} RESET_RELEASED_BY_HOST\n'.encode()); note('RESET_RELEASED_BY_HOST')
t0 = time.monotonic(); buf = b''; reason = 'duration_reached'; next_status = 0
while time.monotonic() - t0 < seconds:
    if stopf.exists(): reason = 'stop_file'; break
    try:
        d = s.read(1024)
    except (serial.SerialException, OSError) as e:
        counts['serial_errors'] += 1; note('SERIAL_ERROR', str(e).encode())
        try: s.close()
        except Exception: pass
        time.sleep(1)
        try: s = open_port(); note('SERIAL_REOPENED')
        except Exception as e2: note('SERIAL_REOPEN_FAILED', str(e2).encode())
        continue
    if d:
        last_rx = time.time(); buf += d
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1); line = line.rstrip(b'\r')
            log.write(stamp().encode() + b' ' + line + b'\n')
            counts['lines'] += 1; last_line = line.decode('utf-8', 'replace')[:160]
            if b'APP_RTT seq=' in line and b'app_rtt_ms=' in line: counts['rtt_lines'] += 1
            if BOOT.search(line): counts['boots'] += 1; note('BOOT_MARKER', line)
            if PANIC.search(line): counts['panics'] += 1; note('PANIC_MARKER', line)
            if DISC.search(line): counts['disconnect_markers'] += 1; note('DISCONNECT_MARKER', line)
            if stop_text and stop_text in line: reason = 'stop_line'; t0 = -1e12
    if t0 == -1e12: break
    el = time.monotonic() - t0
    if el >= next_status:
        next_status = el + 30
        statusf.write_text(json.dumps(dict(utc=stamp(), elapsed_s=round(el, 1), seconds=seconds, silent_s=round(time.time() - last_rx, 1),
                                           last_line=last_line, **counts)))
if buf: log.write(stamp().encode() + b' ' + buf + b'\n')
log.write(f'{stamp()} CAPTURE_CLOSE reason={reason} counts={json.dumps(counts)}\n'.encode())
statusf.write_text(json.dumps(dict(utc=stamp(), finished=True, reason=reason, **counts)))
try: s.close()
except Exception: pass
log.close(); ev.close(); print('closed', reason, counts)
