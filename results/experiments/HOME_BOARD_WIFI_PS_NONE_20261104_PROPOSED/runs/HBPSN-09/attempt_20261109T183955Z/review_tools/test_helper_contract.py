"""Scratch-only contract test: real reliability.py, stubbed screen grab. No screen capture, no COM6."""
import datetime as dt, importlib.util, json, os, subprocess, sys, tempfile, threading, time
from pathlib import Path

attempt = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(attempt))
from reliability import Reports, SettingsEvidence

spec = importlib.util.spec_from_file_location('helper', attempt / 'operator_settings_helper.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

# Declaration gate
try:
    helper.load_observed(attempt)
    print('gate FAILED: unconfirmed declaration accepted')
except SystemExit as e:
    print('gate refuses unconfirmed declaration:', e)

expected = json.loads((attempt / 'preflight.json').read_text())['expected_clumsy_settings']
declared = json.loads((attempt / 'clumsy_declaration.json').read_text())['observed']
print('declaration equals preflight expected:', declared == expected)


def stub():
    w, h = 64, 48
    return w, h, bytes((x * 3) % 256 for x in range(w * h * 4))


with tempfile.TemporaryDirectory(dir=os.environ.get('SCRATCH')) as t:
    run = Path(t) / 'run'
    run.mkdir()
    ev = SettingsEvidence(Reports(run), expected, timeout=30)
    for phase in ('pre_run', 'end_of_run'):
        nb = dt.datetime.now(dt.timezone.utc)
        th = threading.Thread(target=helper.service, args=(run, phase, declared, nb, 20, stub))
        th.start()
        time.sleep(0.2)
        result = ev.capture(phase)
        th.join()
        print(phase, 'broker status', result['status'], 'reason', result.get('reason'), 'source', result.get('evidence', {}).get('source_type'))
    png = (run / 'clumsy_operator_pre_run.png').read_bytes()
    print('png signature ok', png[:8] == b'\x89PNG\r\n\x1a\n', 'bytes', len(png))
    bad = dict(declared, filter='udp')
    nb = dt.datetime.now(dt.timezone.utc)
    run2 = Path(t) / 'run2'
    run2.mkdir()
    ev2 = SettingsEvidence(Reports(run2), expected, timeout=30)
    th = threading.Thread(target=helper.service, args=(run2, 'pre_run', bad, nb, 20, stub))
    th.start(); time.sleep(0.2)
    r = ev2.capture('pre_run'); th.join()
    print('wrong declaration gives', r['status'])

snippet = 'import time;print(time.monotonic())'
a = float(subprocess.run([sys.executable, '-c', snippet], capture_output=True, text=True).stdout)
here = time.monotonic()
b = float(subprocess.run([sys.executable, '-c', snippet], capture_output=True, text=True).stdout)
print('monotonic cross-process ordered:', a <= here <= b, 'span_s', round(b - a, 3), 'python', sys.executable)
