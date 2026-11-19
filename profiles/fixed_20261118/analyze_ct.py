"""Connection-time test: raw serial log -> CSV + summary.
Usage: python -I analyze_ct.py <raw_log> <out_csv> <out_summary_md> <protocol label>
Times are microseconds from esp_timer_get_time() on the board; summary is in milliseconds.
Percentile method: linear interpolation between closest ranks (numpy default, 'type 7')."""
import csv, re, statistics, sys
from pathlib import Path

raw, out_csv, out_md, label = sys.argv[1:5]
cols = ['attempt', 'proto', 'status', 'tcp_connect_us', 'tls_handshake_us', 'tcp_tls_total_us', 'quic_init_us',
        'quic_handshake_cb_us', 'quic_ready_seen_us', 'mqtt_connect_to_connack_us', 'connack_from_start_us', 'reason']
rows = []; heap = []; complete = None
for line in Path(raw).read_text(encoding='utf-8', errors='replace').splitlines():
    m = re.search(r' CT (\d+),(TCP_TLS|QUIC),(OK|FAIL),([^ ]*)$', line)
    if m:
        v = (m.group(1) + ',' + m.group(2) + ',' + m.group(3) + ',' + m.group(4)).split(',')
        if len(v) == len(cols): rows.append(dict(zip(cols, v)))
    m = re.search(r' CT HEAP attempt=(\d+) free=(\d+) min_free=(\d+)', line)
    if m: heap.append(m.groups())
    if ' CT COMPLETE ' in line: complete = line.split(' CT COMPLETE ', 1)[1]
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; lo = int(k); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def stats(xs):
    if not xs: return None
    return dict(n=len(xs), median=statistics.median(xs), mean=statistics.fmean(xs), min=min(xs), max=max(xs), p95=pct(xs, 0.95))


metrics = ['tcp_connect_us', 'tls_handshake_us', 'tcp_tls_total_us', 'quic_init_us', 'quic_handshake_cb_us', 'quic_ready_seen_us',
           'mqtt_connect_to_connack_us', 'connack_from_start_us']
ok = [r for r in rows if r['status'] == 'OK']; fail = [r for r in rows if r['status'] != 'OK']
out = [f'# Connection-time summary: {label}', '', f'Attempts logged: {len(rows)}; OK: {len(ok)}; failed: {len(fail)}.',
       f'Board final line: `{complete}`' if complete else 'Board final line CT COMPLETE not found.', '',
       'Times in milliseconds (board esp_timer_get_time, microsecond resolution), successful attempts only. P95 = linear interpolation.', '']
for title, subset in (('All successful attempts', ok), ('Excluding attempt 1 (first-connection effects)', [r for r in ok if r['attempt'] != '1'])):
    out += [f'## {title}', '', '| metric | n | median | mean | min | max | P95 |', '|---|---|---|---|---|---|---|']
    for k in metrics:
        xs = [int(r[k]) / 1000 for r in subset if r[k] not in ('-1', '')]
        s = stats(xs)
        if s: out.append(f"| {k[:-3]} | {s['n']} | {s['median']:.3f} | {s['mean']:.3f} | {s['min']:.3f} | {s['max']:.3f} | {s['p95']:.3f} |")
    out.append('')
if fail:
    out += ['## Failures', ''] + [f"- attempt {r['attempt']}: {r['reason']}" for r in fail] + ['']
out += ['## Heap (every 10 attempts)', '', '| after attempt | free bytes | min free bytes |', '|---|---|---|'] + [f'| {a} | {b} | {c} |' for a, b, c in heap]
Path(out_md).write_text('\n'.join(out) + '\n', encoding='utf-8')
print('rows', len(rows), 'ok', len(ok), 'fail', len(fail))
