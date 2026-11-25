"""Long run with reconnect: raw serial log + server CSV -> CSV tables + SUMMARY.md.
Usage: python -I analyze_reconnect.py <raw_log> <server_csv> <out_dir> <label>
Reads the lines of the reconnect_20261124 profile: APP_RTT, HEAPLOG, DIAG, STALL, FAIL_DIAG, CONNECTION_FAILED,
RECONNECT_START, RECONNECT_ATTEMPT, RECONNECT, APP_RTT_LOST, WIFI_EVENT, WIFI_KICK, APP_RX_DROP, QUIC_TIMEOUT.
Sequence numbers continue across reconnects (one boot = one sequence). Hours are counted from RESET_RELEASED_BY_HOST.
Server CSV rows are limited to the capture window (reset release .. capture close)."""
import csv, re, statistics, sys, datetime as dt
from pathlib import Path

raw, server_csv, outdir, label = sys.argv[1:5]
outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
TS = re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z (.*)$')
KV = re.compile(r'(\w+)=(\S+)')
ANSI = re.compile(r'\x1b\[[0-9;]*m')
parse = lambda s: dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
lines = []
for l in Path(raw).read_text(encoding='utf-8', errors='replace').splitlines():
    m = TS.match(l)
    if m: lines.append((parse(m.group(1)), ANSI.sub('', m.group(2))))
t_reset = next((t for t, l in lines if l.startswith('RESET_RELEASED_BY_HOST')), lines[0][0])
t_end = next((t for t, l in reversed(lines) if l.startswith('CAPTURE_CLOSE')), lines[-1][0])
duration = (t_end - t_reset).total_seconds()
el = lambda t: (t - t_reset).total_seconds()
PANIC = re.compile(r'Guru Meditation|Load access fault|Store access fault|abort\(\)|Backtrace:|CORRUPT HEAP|Task watchdog', re.I)


def kv(l):
    d = {}
    for k, v in KV.findall(l):
        try: d[k] = int(v)
        except ValueError:
            try: d[k] = float(v)
            except ValueError: d[k] = v
    return d


rtt, heap, diag, stalls, fails, recon, attempts, lost, wifi, kicks, drops, qto, panics, boots, connect0 = ([] for _ in range(15))
for t, l in lines:
    base = dict(utc=t.isoformat(), elapsed_s=round(el(t), 3))
    if re.search(r'rst:0x|ESP-ROM:esp32c6', l) and (not boots or (t - boots[-1]).total_seconds() > 5): boots.append(t)
    if PANIC.search(l): panics.append((t.isoformat(), l[:160]))
    m = re.search(r'APP_RTT seq=(\d+) app_rtt_ms=([0-9.]+)', l)
    if m: rtt.append(dict(seq=int(m.group(1)), rtt_ms=float(m.group(2)), **base)); continue
    m = re.search(r'HEAPLOG uptime_s=(\d+) free=(\d+) min_free=(\d+)', l)
    if m: heap.append(dict(uptime_s=int(m.group(1)), free=int(m.group(2)), min_free=int(m.group(3)), **base)); continue
    for key, store in (('DIAG ', diag), ('STALL ', stalls), ('FAIL_DIAG ', fails), ('RECONNECT_ATTEMPT ', attempts),
                       ('RECONNECT ', recon), ('APP_RTT_LOST ', lost), ('WIFI_EVENT ', wifi), ('WIFI_KICK ', kicks),
                       ('APP_RX_DROP ', drops), ('QUIC_TIMEOUT ', qto), ('CONNECTION_FAILED ', fails), ('CONNECT session=0', connect0)):
        if l.startswith(key):
            d = dict(kind=key.strip().split()[0], **base, **kv(l))
            if key == 'WIFI_EVENT ': d['event'] = l.split()[1]
            store.append(d); break

srv = []
if server_csv and Path(server_csv).exists():
    for r in csv.DictReader(Path(server_csv).open(encoding='utf-8')):
        try:
            ts = r.get('server_receive_utc') or ''
            if ts:
                tt = dt.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if tt.tzinfo is None: tt = tt.replace(tzinfo=dt.timezone.utc)
                if not (t_reset <= tt <= t_end): continue
            srv.append(int(r['seq']))
        except (ValueError, TypeError, KeyError): pass


def write(name, rows):
    if not rows: (outdir / name).write_text('', encoding='utf-8'); return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with (outdir / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)


write('rtt.csv', rtt); write('heap.csv', heap); write('diag.csv', diag); write('reconnects.csv', recon)
write('reconnect_attempts.csv', attempts); write('stalls.csv', stalls); write('failures.csv', fails)
write('wifi_events.csv', wifi + kicks); write('lost_seq.csv', lost)


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; lo = int(k); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def st(xs, f='.2f'):
    if not xs: return 'n=0'
    return (f'n={len(xs)} median={statistics.median(xs):{f}} mean={statistics.fmean(xs):{f}} P95={pct(xs, .95):{f}} '
            f'min={min(xs):{f}} max={max(xs):{f}}')


def ranges(nums):
    out = []
    for n in sorted(nums):
        if out and n == out[-1][1] + 1: out[-1][1] = n
        else: out.append([n, n])
    return ', '.join(f'{a}' if a == b else f'{a}-{b}' for a, b in out) or 'none'


echoed = {r['seq'] for r in rtt}
sent = max(echoed | set(srv) | {d.get('seq', 0) for d in lost}, default=0)
missing = [q for q in range(1, sent + 1) if q not in echoed]
srvset = set(srv)
miss_reached = [q for q in missing if q in srvset]; miss_not = [q for q in missing if q not in srvset]
S = [f'# Long run with reconnect: {label}', '',
     f'Capture duration from reset release to capture close: {duration:.0f} s ({duration / 3600:.2f} h).',
     f'Boots seen: {len(boots)} (1 = no reboot); panic/fault markers: {len(panics)}.', '',
     '## Messages', '',
     f'- sent (highest seq seen in serial log, server CSV or APP_RTT_LOST): {sent}',
     f'- echoed with APP_RTT: {len(echoed)}; missing: {len(missing)}',
     f'- missing seq that reached the server (echo lost on the way back or session closed first): {len(miss_reached)} ({ranges(miss_reached)})',
     f'- missing seq not in the server CSV (never arrived): {len(miss_not)} ({ranges(miss_not)})',
     f'- server CSV rows in capture window: {len(srv)}; unique seq: {len(srvset)}',
     f'- RTT ms overall: {st([r["rtt_ms"] for r in rtt])}', '']
S += ['## Connection failures, stalls and reconnects', '',
      f'- first connection: {connect0[0] if connect0 else "not found"}',
      f'- connection failures (CONNECTION_FAILED): {len([f for f in fails if f["kind"] == "CONNECTION_FAILED"])}; '
      f'reasons: {dict((r, sum(1 for f in fails if f.get("reason") == r)) for r in sorted({f.get("reason") for f in fails if f["kind"] == "CONNECTION_FAILED"}))}',
      f'- STALL lines (no echo for 15 s): {len(stalls)}',
      f'- reconnects completed: {len(recon)}; failed attempts: {len(attempts)}; attempts per reconnect: {[r.get("attempts") for r in recon]}',
      f'- reconnect handshake ms (transport setup): {st([r["handshake_ms"] for r in recon if isinstance(r.get("handshake_ms"), float)], ".1f")}',
      f'- reconnect MQTT CONNECT->CONNACK ms: {st([r["connack_ms"] for r in recon if isinstance(r.get("connack_ms"), float)], ".1f")}',
      f'- reconnect attempt total ms (attempt start -> subscribed): {st([r["attempt_total_ms"] for r in recon if isinstance(r.get("attempt_total_ms"), float)], ".1f")}',
      f'- downtime ms (failure detected -> connected again, includes 1 s backoff): {st([r["downtime_ms"] for r in recon if isinstance(r.get("downtime_ms"), float)], ".1f")}',
      '', '| # | failure UTC | reason | fail uptime ms | reconnect start uptime ms | connected uptime ms | handshake ms | CONNACK ms | attempts | downtime ms |',
      '|---|---|---|---|---|---|---|---|---|---|']
for r in recon:
    S.append(f'| {r.get("n")} | {r["utc"]} | {r.get("reason")} | {r.get("fail_uptime_ms")} | {r.get("start_uptime_ms")} | '
             f'{r.get("connected_uptime_ms")} | {r.get("handshake_ms")} | {r.get("connack_ms")} | {r.get("attempts")} | {r.get("downtime_ms")} |')
S += ['', '### State at each stall / failure (STALL and FAIL_DIAG lines, first 30)', '']
for d in sorted(stalls + [f for f in fails if f['kind'] == 'FAIL_DIAG'], key=lambda d: d['utc'])[:30]:
    S.append(f'- {d["utc"]} {d["kind"]}: ' + ' '.join(f'{k}={v}' for k, v in d.items() if k not in ('kind', 'utc', 'elapsed_s')))
S += ['', '## Wi-Fi', '',
      f'- RSSI dBm from DIAG (every 60 s): {st([d["rssi"] for d in diag if isinstance(d.get("rssi"), int) and d["rssi"] != 0], ".0f")}',
      f'- Wi-Fi events: {len(wifi)} ({dict((e, sum(1 for w in wifi if w["event"] == e)) for e in sorted({w["event"] for w in wifi}))}); WIFI_KICK: {len(kicks)}']
for w in wifi:
    if w['event'] != 'start': S.append(f'  - {w["utc"]} {w["event"]} ' + ' '.join(f'{k}={v}' for k, v in w.items() if k not in ('kind', 'utc', 'elapsed_s', 'event')))
S += ['', '## Transport-level diagnostics', '',
      f'- APP_RX_DROP (QUIC receive buffer full, data discarded): {len(drops)}',
      f'- QUIC_TIMEOUT (ngtcp2 expiry error): {len(qto)}']
for key in ('in_flight', 'pto_count', 'lost_pending', 'tx_loss_count', 'unacked', 'unsent', 'nrtx', 'app_buf_len', 'rx_avail'):
    xs = [d[key] for d in diag if isinstance(d.get(key), int)]
    if xs: S.append(f'- DIAG {key}: max {max(xs)}, samples > 0: {sum(1 for x in xs if x > 0)} of {len(xs)}')
S += ['', '## RTT per hour (ms, elapsed from reset release)', '', '| hour | n | median | mean | P95 | min | max |', '|---|---|---|---|---|---|---|']
for h in range(int(duration // 3600) + 1):
    xs = [r['rtt_ms'] for r in rtt if h * 3600 <= r['elapsed_s'] < (h + 1) * 3600]
    if xs: S.append(f'| {h}-{h + 1} | {len(xs)} | {statistics.median(xs):.2f} | {statistics.fmean(xs):.2f} | {pct(xs, .95):.2f} | {min(xs):.2f} | {max(xs):.2f} |')
S += ['', '## Free heap trend (HEAPLOG every 60 s)', '']
if heap:
    f0, f1 = heap[0], heap[-1]
    xs = [h['free'] for h in heap]; ys = [h['min_free'] for h in heap]
    hours = max((f1['elapsed_s'] - f0['elapsed_s']) / 3600, 1e-9)
    S += [f'- samples: {len(heap)}; first free {f0["free"]} B, last free {f1["free"]} B, change {f1["free"] - f0["free"]} B ({(f1["free"] - f0["free"]) / hours:.0f} B/h)',
          f'- free min/max over run: {min(xs)} / {max(xs)} B; minimum-free-heap first/last/overall: {f0["min_free"]} / {f1["min_free"]} / {min(ys)} B',
          f'- free heap after each reconnect (RECONNECT free=): {[r.get("free") for r in recon]}']
else:
    S.append('- no HEAPLOG lines found')
S += ['', '## Panic / fault markers', ''] + ([f'- {a} {b}' for a, b in panics] or ['- none'])
(outdir / 'SUMMARY.md').write_text('\n'.join(S) + '\n', encoding='utf-8')
print('\n'.join(S[:30]))
