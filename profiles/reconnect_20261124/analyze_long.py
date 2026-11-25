"""12 h run: raw serial log + server CSV -> RTT CSV, heap CSV, summary.
Usage: python -I analyze_long.py <raw_log> <server_csv> <out_dir> <label>
Sessions: a new boot marker starts a new session (sequence numbers restart at 1 after a reboot).
Hours are counted from RESET_RELEASED_BY_HOST in the raw log."""
import csv, json, re, statistics, sys, datetime as dt
from pathlib import Path

raw, server_csv, outdir, label = sys.argv[1:5]
outdir = Path(outdir)
TS = re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z (.*)$')
parse = lambda s: dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
lines = []
for l in Path(raw).read_text(encoding='utf-8', errors='replace').splitlines():
    m = TS.match(l)
    if m: lines.append((parse(m.group(1)), m.group(2)))
t_reset = next((t for t, l in lines if l.startswith('RESET_RELEASED_BY_HOST')), lines[0][0])
t_end = next((t for t, l in reversed(lines) if l.startswith('CAPTURE_CLOSE')), lines[-1][0])
duration = (t_end - t_reset).total_seconds()
BOOT = re.compile(r'ESP-IDF v[0-9.]+ 2nd stage bootloader|Starting ESP32-C6 DHT11 over')
PANIC = re.compile(r'Guru Meditation|Load access fault|Store access fault|abort\(\)|Backtrace:|CORRUPT HEAP|Task watchdog', re.I)
session = 0; sessions = [dict(index=0, start=t_reset)]
rtt = []; heap = []; panics = []; disc = []; boots = []; setup = {}
for t, l in lines:
    if 'ESP-IDF v' in l and '2nd stage bootloader' in l or l.startswith('ESP-ROM:'):
        if t - sessions[-1]['start'] > dt.timedelta(seconds=5) or session == 0 and False:
            pass
    if re.search(r'rst:0x|ESP-ROM:esp32c6', l) and (not boots or (t - boots[-1]).total_seconds() > 5):
        boots.append(t)
        if len(boots) > 1:
            session += 1; sessions.append(dict(index=session, start=t))
    m = re.search(r'APP_RTT seq=(\d+) app_rtt_ms=([0-9.]+)', l)
    if m: rtt.append(dict(session=session, seq=int(m.group(1)), rtt_ms=float(m.group(2)), utc=t.isoformat(), elapsed_s=(t - t_reset).total_seconds()))
    m = re.search(r'HEAPLOG uptime_s=(\d+) free=(\d+) min_free=(\d+)', l)
    if m: heap.append(dict(session=session, uptime_s=int(m.group(1)), free=int(m.group(2)), min_free=int(m.group(3)), utc=t.isoformat(), elapsed_s=(t - t_reset).total_seconds()))
    if PANIC.search(l): panics.append((t.isoformat(), l[:160]))
    if re.search(r'Task stopped\. Restart board|TLS read / peer disconnected|MQTT process returned|process returned an error|QUIC .*(failed|closed)|Cleaning up .* connection', l):
        disc.append((t.isoformat(), l[:160]))
    m = re.search(r'\((\d+)\) quic_demo_main: (Connecting to .* server|\w+ connection established|MQTT connected over)', l)
    if m and session == 0:
        key = 'connecting' if m.group(2).startswith('Connecting') else ('established' if 'established' in m.group(2) else 'mqtt_connected')
        setup.setdefault(key, int(m.group(1)))
with (outdir / 'rtt.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['session', 'seq', 'rtt_ms', 'utc', 'elapsed_s']); w.writeheader(); w.writerows(rtt)
with (outdir / 'heap.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['session', 'uptime_s', 'free', 'min_free', 'utc', 'elapsed_s']); w.writeheader(); w.writerows(heap)
srv = []
if server_csv and Path(server_csv).exists():
    for r in csv.DictReader(Path(server_csv).open(encoding='utf-8')):
        try: srv.append(int(r['seq']))
        except (ValueError, TypeError, KeyError): pass


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; lo = int(k); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def st(xs):
    if not xs: return 'n=0'
    return f'n={len(xs)} median={statistics.median(xs):.2f} mean={statistics.fmean(xs):.2f} P95={pct(xs, .95):.2f} min={min(xs):.2f} max={max(xs):.2f}'


def ranges(nums):
    out = []; nums = sorted(nums)
    for n in nums:
        if out and n == out[-1][1] + 1: out[-1][1] = n
        else: out.append([n, n])
    return ', '.join(f'{a}' if a == b else f'{a}-{b}' for a, b in out) or 'none'


S = [f'# 12 h run summary: {label}', '', f'Capture duration from reset release to capture close: {duration:.0f} s ({duration / 3600:.2f} h).',
     f'Boot markers seen (initial boot included): {len(boots)}; sessions: {len(sessions)}; panic/fault markers: {len(panics)}; disconnect markers: {len(disc)}.', '']
sent_total = echoed_total = 0
for s in sessions:
    rs = [r for r in rtt if r['session'] == s['index']]
    echoed = {r['seq'] for r in rs}
    max_seq = max(echoed | (set(srv) if len(sessions) == 1 else set()), default=0)
    sent = max_seq  # highest sequence number seen anywhere (serial echo or server CSV); sequence starts at 1
    missing = [q for q in range(1, sent + 1) if q not in echoed]
    sent_total += sent; echoed_total += len(echoed)
    S += [f'## Session {s["index"]} (start {s["start"].isoformat()})', '', f'- messages sent (highest seq seen): {sent}; echoed with APP_RTT: {len(echoed)}; missing seq: {len(missing)}',
          f'- missing sequence numbers: {ranges(missing)}', f'- RTT ms overall: {st([r["rtt_ms"] for r in rs])}', '']
if len(sessions) == 1 and srv:
    S += [f'Server CSV rows: {len(srv)}; unique seq: {len(set(srv))}; highest seq: {max(srv)}.', '']
S += ['## RTT per hour (ms, elapsed from reset release)', '', '| hour | n | median | mean | P95 | min | max |', '|---|---|---|---|---|---|---|']
for h in range(int(duration // 3600) + 1):
    xs = [r['rtt_ms'] for r in rtt if h * 3600 <= r['elapsed_s'] < (h + 1) * 3600]
    if xs: S.append(f'| {h}-{h + 1} | {len(xs)} | {statistics.median(xs):.2f} | {statistics.fmean(xs):.2f} | {pct(xs, .95):.2f} | {min(xs):.2f} | {max(xs):.2f} |')
S += ['', f'Overall (all sessions): sent {sent_total}, echoed {echoed_total}.', '', '## Connection setup at start (board uptime ms, first session)', '', f'`{json.dumps(setup)}`']
if 'connecting' in setup and 'established' in setup:
    S.append(f'- transport setup (connecting -> connection established): {setup["established"] - setup["connecting"]} ms (board log time stamps, 1 ms resolution)')
if 'connecting' in setup and 'mqtt_connected' in setup:
    S.append(f'- connecting -> MQTT connected (includes the fixed 1,000 ms application delay of the formal firmware): {setup["mqtt_connected"] - setup["connecting"]} ms')
S += ['', '## Free heap trend (HEAPLOG every 60 s)', '']
if heap:
    f0, f1 = heap[0], heap[-1]
    xs = [h['free'] for h in heap]; ys = [h['min_free'] for h in heap]
    hours = max((f1['elapsed_s'] - f0['elapsed_s']) / 3600, 1e-9)
    S += [f'- samples: {len(heap)}; first free {f0["free"]} B, last free {f1["free"]} B, change {f1["free"] - f0["free"]} B ({(f1["free"] - f0["free"]) / hours:.0f} B/h)',
          f'- free min/max over run: {min(xs)} / {max(xs)} B; minimum-free-heap first/last/overall: {f0["min_free"]} / {f1["min_free"]} / {min(ys)} B']
else:
    S.append('- no HEAPLOG lines found')
S += ['', '## Crash / disconnect markers (first 20)', ''] + [f'- {a} {b}' for a, b in (panics + disc)[:20]]
(outdir / 'SUMMARY.md').write_text('\n'.join(S) + '\n', encoding='utf-8')
print('\n'.join(S[:14]))
