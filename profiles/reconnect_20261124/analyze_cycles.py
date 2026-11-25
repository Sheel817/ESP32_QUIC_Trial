"""Analysis of one controlled reconnect test (reconnect_cycles.ps1).
Usage: python -I analyze_cycles.py <test_dir> <label>
Per cycle (host UTC times from cycles.jsonl, board lines from serial_raw.log with host timestamps):
  kill -> CONNECTION_FAILED (detection), server READY (restart) -> handshake done -> MQTT CONNACK, attempts.
Board uptime is mapped to host time at the RECONNECT line (printed right after the subscribe, i.e. at connected_uptime_ms):
  handshake_done_host = line_utc - (connected_uptime_ms - (last_start_uptime_ms + handshake_ms))
  connack_host        = handshake_done_host + connack_ms
Writes cycles.csv and SUMMARY.md into <test_dir>."""
import sys, json, re, csv, math, statistics, datetime as dt
from pathlib import Path

d = Path(sys.argv[1]); label = sys.argv[2]


def ts(s):
    s = s.strip()
    if s.endswith('Z'): s = s[:-1]
    if '+' in s[19:]: s = s[:s.rindex('+')]
    if '.' in s:
        a, b = s.split('.'); s = a + '.' + (b + '000000')[:6]
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)


ev = [json.loads(l.lstrip('﻿')) for l in (d / 'cycles.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()]
lines = []
for raw in (d / 'serial_raw.log').read_bytes().decode('utf-8', 'replace').splitlines():
    m = re.match(r'^(\d{4}-\d\d-\d\dT\S+Z) (.*)$', raw)
    if m: lines.append((ts(m.group(1)), m.group(2)))
kv = lambda s: dict(re.findall(r'(\w+)=(\S+)', s))

kills = {e['cycle']: ts(e['kill_utc']) for e in ev if e['event'] == 'SERVER_KILLED'}
ready = {e['cycle']: (ts(e['start_utc']), ts(e['ready_utc'])) for e in ev if e['event'] == 'SERVER_READY' and e.get('cycle')}
timeouts = {e['cycle'] for e in ev if e['event'] == 'RECONNECT_TIMEOUT'}
abort = [e for e in ev if e['event'] in ('ABORT', 'PRECHECK_FAILED')]
ended = any(e['event'] == 'TEST_END' for e in ev)
ms = lambda a, b: (b - a).total_seconds() * 1000.0

rows = []
for c in sorted(kills):
    k = kills[c]; nxt = kills.get(c + 1, dt.datetime.max.replace(tzinfo=dt.timezone.utc))
    seg = [(t, l) for t, l in lines if k <= t < nxt]
    fail = next(((t, l) for t, l in seg if l.startswith('CONNECTION_FAILED')), None)
    rec = next(((t, l) for t, l in seg if re.match(r'RECONNECT n=\d+ session=', l)), None)
    att_fail = [kv(l).get('stage') for t, l in seg if l.startswith('RECONNECT_ATTEMPT') and (rec is None or t <= rec[0])]
    r = dict(cycle=c, kill_utc=k.isoformat(), detect_ms=None, fail_reason=None, restart_utc=None, server_ready_lag_ms=None,
             ok=rec is not None, attempts=None, failed_attempt_stages='|'.join(att_fail), restart_to_handshake_ms=None,
             restart_to_connack_ms=None, board_handshake_ms=None, board_connack_ms=None, board_downtime_ms=None,
             first_attempt_before_restart=None, timeout=c in timeouts, recon_start_to_handshake_ms=None,
             recon_start_to_connack_ms=None, attempt_to_connack_ms=None, reconnect_start_before_restart=None)
    if fail:
        r['detect_ms'] = round(ms(k, fail[0]), 1); r['fail_reason'] = kv(fail[1]).get('reason')
    if c in ready:
        r['restart_utc'] = ready[c][1].isoformat(); r['server_ready_lag_ms'] = round(ms(*ready[c]), 1)
    if rec and c in ready:
        f = kv(rec[1]); hs = float(f['handshake_ms']); ca = float(f['connack_ms'])
        conn = int(f['connected_uptime_ms']); last = int(f['last_start_uptime_ms']); first = int(f['start_uptime_ms'])
        hs_host = rec[0] - dt.timedelta(milliseconds=conn - (last + hs))
        fail_up = int(f['fail_uptime_ms'])  # RECONNECT_START is printed at fail time (board clock, same for both protocols)
        r.update(recon_start_to_handshake_ms=round(last + hs - fail_up, 1), recon_start_to_connack_ms=round(last + hs + ca - fail_up, 1),
                 attempt_to_connack_ms=round(hs + ca, 1),
                 reconnect_start_before_restart=(rec[0] - dt.timedelta(milliseconds=conn - fail_up)) < ready[c][1])
        r.update(attempts=int(f['attempts']), board_handshake_ms=hs, board_connack_ms=ca, board_downtime_ms=float(f['downtime_ms']),
                 restart_to_handshake_ms=round(ms(ready[c][1], hs_host), 1),
                 restart_to_connack_ms=round(ms(ready[c][1], hs_host + dt.timedelta(milliseconds=ca)), 1),
                 first_attempt_before_restart=(rec[0] - dt.timedelta(milliseconds=conn - first)) < ready[c][1])
    rows.append(r)

with open(d / 'cycles.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ['cycle']); w.writeheader(); w.writerows(rows)


def stats(vals):
    v = sorted(x for x in vals if x is not None)
    if not v: return dict(n=0)
    p95 = v[max(0, math.ceil(0.95 * len(v)) - 1)]  # nearest-rank
    return dict(n=len(v), median=statistics.median(v), min=v[0], max=v[-1], p95=p95, mean=statistics.mean(v))


ok = [r for r in rows if r['ok']]
rtt = [l for t, l in lines if 'APP_RTT seq=' in l and 'app_rtt_ms=' in l]
seqs = sorted({int(re.search(r'seq=(\d+)', l).group(1)) for l in rtt})
lost = [l for t, l in lines if l.startswith('APP_RTT_LOST')]
panics = [l for t, l in lines if re.search(r'Guru Meditation|abort\(\)|Backtrace:|CORRUPT HEAP|Task watchdog', l)]
boots = [l for t, l in lines if 'rst:0x' in l]
stalls = [l for t, l in lines if l.startswith('STALL ')]
reasons = {}
for r in rows:
    if r['fail_reason']: reasons[r['fail_reason']] = reasons.get(r['fail_reason'], 0) + 1
first = next((l for t, l in lines if l.startswith('CONNECT session=0')), '')
fmt = lambda x: '' if x is None else (f'{x:,.1f}' if isinstance(x, float) else str(x))

out = [f'# Controlled reconnect test — {label}', '',
       f'Cycles run: {len(rows)} (test {"completed" if ended else "NOT completed"}{"; " + "; ".join(e.get("reason", str(e.get("reasons"))) for e in abort) if abort else ""}). '
       f'Reconnected: {len(ok)}/{len(rows)}; reconnect timeouts: {len(timeouts)}; failed attempts before success: '
       f'{sum((r["attempts"] or 1) - 1 for r in ok)}; reboots during test (rst lines after the start reset): {max(0, len(boots) - 1)}; panics: {len(panics)}.', '',
       f'First connection: `{first}`', '',
       '## Headline: (2) reconnect duration, board clock', '',
       'Reconnect start = the board gives up the old connection (RECONNECT_START, same instant as CONNECTION_FAILED); '
       'the duration includes the 1 s backoff and any failed attempts while the server was still down.', '',
       '| metric (ms) | n | median | min | max | P95 | mean |', '|---|---|---|---|---|---|---|']
def table(items):
    res = []
    for name, key in items:
        s = stats(r[key] for r in rows)
        res.append(f'| {name} | {s["n"]} | ' + (' | '.join(fmt(float(s[k])) for k in ('median', 'min', 'max', 'p95', 'mean')) if s['n'] else ' |  |  |  | ') + ' |')
    return res
hdr = ['| metric (ms) | n | median | min | max | P95 | mean |', '|---|---|---|---|---|---|---|']
out += table([('(2a) reconnect start -> handshake done', 'recon_start_to_handshake_ms'),
              ('(2b) reconnect start -> MQTT CONNACK', 'recon_start_to_connack_ms'),
              ('successful attempt only: attempt start -> handshake done', 'board_handshake_ms'),
              ('successful attempt only: attempt start -> MQTT CONNACK', 'attempt_to_connack_ms'),
              ('successful attempt only: CONNECT -> CONNACK', 'board_connack_ms')])
out += ['', '## (1) Detection: server stop -> board notices (host clock)', ''] + hdr + table([('(1) server kill -> CONNECTION_FAILED', 'detect_ms')])
out += ['', '## (3) Reference: server restart (READY) -> board connected (host clock, includes detection when it ends after the restart)', ''] + hdr + \
       table([('(3a) server READY -> handshake done', 'restart_to_handshake_ms'), ('(3b) server READY -> MQTT CONNACK', 'restart_to_connack_ms'),
              ('board downtime (failure -> subscribed)', 'board_downtime_ms')])
s = stats(r['attempts'] for r in ok)
out += ['', f'Attempts per reconnect: ' + (f'median {s["median"]}, min {s["min"]}, max {s["max"]}' if s['n'] else 'n/a') +
        f'. Failure detection reasons: {reasons or "none"}. Cycles whose reconnect started before the server was READY: '
        f'{sum(1 for r in ok if r["reconnect_start_before_restart"])}/{len(ok)}.',
        f'Echo: {len(rtt)} APP_RTT lines (seq {seqs[0] if seqs else "-"}..{seqs[-1] if seqs else "-"}), {len(lost)} APP_RTT_LOST, {len(stalls)} STALL lines.', '',
        'Per cycle (ms):', '', '| cycle | ok | attempts | (1) detect | (2a) start→handshake | (2b) start→CONNACK | (3b) READY→CONNACK | attempt handshake | CONNECT→CONNACK | start before READY | fail reason | failed attempt stages |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|']
for r in rows:
    out.append(f'| {r["cycle"]} | {"yes" if r["ok"] else "NO"} | {fmt(r["attempts"])} | {fmt(r["detect_ms"])} | {fmt(r["recon_start_to_handshake_ms"])} | '
               f'{fmt(r["recon_start_to_connack_ms"])} | {fmt(r["restart_to_connack_ms"])} | {fmt(r["board_handshake_ms"])} | {fmt(r["board_connack_ms"])} | '
               f'{"" if r["reconnect_start_before_restart"] is None else ("yes" if r["reconnect_start_before_restart"] else "no")} | {r["fail_reason"] or ""} | {r["failed_attempt_stages"]} |')
(d / 'SUMMARY.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print('\n'.join(out[:14]))
