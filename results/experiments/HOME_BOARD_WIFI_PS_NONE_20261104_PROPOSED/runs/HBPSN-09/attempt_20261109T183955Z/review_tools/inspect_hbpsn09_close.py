"""Read-only inspection for the HBPSN-09 closure draft. Writes nothing. cwd = study dir."""
import csv, datetime as dt, hashlib, io, json, math, re, statistics, zipfile
from pathlib import Path

study = Path.cwd()
assert (study / 'EXPERIMENT_PLAN_PROPOSED_V1.md').exists()
root = study.parents[2]
A = study / 'runs/HBPSN-09/attempt_20261109T183955Z'
A7 = study / 'runs/HBPSN-07/attempt_20261107T030606Z'
A4 = study / 'runs/HBPSN-04/attempt_20261106T020052Z_host_preflight_continuation'


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


print('=== manifest verification')
items = json.loads((A / 'SHA256SUMS.json').read_text(encoding='utf-8'))
bad = [e['path'] for e in items if not (A / e['path']).exists() or sh(A / e['path']) != e['sha256']]
print('entries', len(items), 'mismatched or missing', bad)
listed = {e['path'] for e in items}
print('not in manifest:', sorted(p.relative_to(A).as_posix() for p in A.rglob('*') if p.is_file() and p.relative_to(A).as_posix() not in listed and '__pycache__' not in p.parts))

print('=== statistics without values')
s = json.loads((A / 'statistics.json').read_text(encoding='utf-8'))
print(json.dumps({k: v for k, v in s.items() if k != 'all_values_ms'}, indent=1)[:3500])

print('=== recompute')
rows = list(csv.DictReader((A / 'selected_first_415.csv').open(encoding='utf-8-sig', newline='')))
print('columns', list(rows[0]))
col = next(c for c in rows[0] if 'rtt' in c.lower() and 'ms' in c.lower())
v = [float(r[col]) for r in rows]
o = sorted(v)
print('column', col, 'N', len(v), 'mean', statistics.fmean(v), 'sd', statistics.stdev(v), 'min', o[0], 'median', statistics.median(v), 'p95 rank', math.ceil(.95 * len(v)), o[math.ceil(.95 * len(v)) - 1], 'max', o[-1])

print('=== metadata keys')
m = json.loads((A / 'metadata.json').read_text(encoding='utf-8'))
print(json.dumps(m, indent=1)[:2500])
print('raw serial lines', len((A / 'serial.raw.log').read_bytes().splitlines()))

print('=== collector connection-error logic')
for i, line in enumerate((A / 'collector_v2.py').read_text(encoding='utf-8').splitlines(), 1):
    if re.search(r'connection_error|errors\b|ERROR', line):
        print(i, line.strip()[:220])

print('=== server stdout near stderr line')
rec = [json.loads(x) for x in (A / 'server.stdout.receipts.jsonl').read_text(encoding='utf-8').splitlines()]
raw = (A / 'server.stdout.raw.log').read_bytes()
for r in rec:
    if '2026-11-09T18:59:00' <= r['utc'] <= '2026-11-09T18:59:07':
        print(r['utc'], raw[r['offset']:r['offset'] + r['length']].decode('utf-8', 'replace')[:300].rstrip())
print('=== serial around uptime 57 s, error words anywhere')
text = (A / 'serial.raw.log').read_bytes().decode('utf-8', 'replace').splitlines()
words = re.compile(r'error|fail|disconnect|timeout|reconnect', re.I)
hits = [(i, l[:160]) for i, l in enumerate(text, 1) if words.search(l)]
print(len(hits), hits[:15])

print('=== precedents')
for name, d in [('07', A7), ('04', A4)]:
    for f in ('register_final_request.json',):
        p = d / f
        print(name, f, p.exists() and json.loads(p.read_text(encoding='utf-8'))['patch'].get('connection_error_count'))
    st = json.loads((d / 'statistics.json').read_text(encoding='utf-8'))
    print(name, {k: v for k, v in st.items() if 'error' in k.lower() or 'gap' in k.lower()})
    print(name, 'stderr bytes', (d / 'server.stderr.raw.log').read_bytes()[:200])
print(json.dumps(json.loads((A7 / 'manual_review.json').read_text(encoding='utf-8')), indent=1)[:3500])

print('=== xlsx rows')
XL = root / 'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
with zipfile.ZipFile(XL) as z:
    x = z.read('xl/worksheets/sheet1.xml')
    print('testzip', z.testzip())
for n in (8, 10):
    m = re.search(rb'<(?:\w+:)?row\b[^>]*\br="%d"[^>]*>.*?</(?:\w+:)?row>' % n, x, re.S)
    print('row', n, len(m.group()))
    print(m.group().decode('utf-8')[:6000 if n == 10 else 5000])

print('=== csv')
raw = (study / 'run_register.csv').read_bytes()
lines = raw.splitlines(keepends=True)
print('physical lines', len(lines), 'line[9] startswith', lines[9][:40], 'ends', lines[9][-4:])
