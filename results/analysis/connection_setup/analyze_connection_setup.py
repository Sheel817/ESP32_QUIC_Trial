"""Connection setup timing for HBPSN-01 to HBPSN-18, first boot only.

Reads (never modifies) for each run, using the attempt named by raw_serial_path in run_register.csv:
  serial.raw.log, serial_receipts.jsonl, reset_event.json
Writes next to this script:
  connection_setup_events.csv, connection_setup_per_run.csv, connection_setup_summary.csv

Run:  python -I analyze_connection_setup.py [STUDY_DIR]
Clock A: ESP log uptime in ms (the number in "I (ms)"), taken as time since reset release.
Clock B: host receipt time of the log line minus reset_release_utc, in ms.
"""
import bisect, csv, datetime as dt, hashlib, json, re, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parents[1] / 'experiments' / 'HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
REGISTER = STUDY / 'run_register.csv'
rows = list(csv.DictReader(REGISTER.open(encoding='utf-8', newline='')))

LINE = re.compile(rb'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) (.*)$')
UP = re.compile(rb'^[IWE] \((\d+)\) ([\w\-\.]+): ?(.*)$')
# event key -> (log tag, message prefix). The first matching line of the first boot is used.
EV = {
    'wifi_associated': (rb'wifi', rb'connected with '),
    'wifi_ip': (rb'esp_netif_handlers', rb'example_netif_sta ip: '),
    'quic_handshake_completed': (rb'QUIC', rb'QUIC handshake completed callback triggered'),
    'quic_connection_established_app': (rb'quic_demo_main', rb'QUIC connection established'),
    'tcp_tls_negotiated': (rb'TLS', rb'TCP_TLS negotiated'),
    'tcp_tls_connected': (rb'TCP_TLS', rb'Connected to '),
    'tcp_tls_connection_established_app': (rb'quic_demo_main', rb'TCP_TLS connection established'),
    'mqtt_connected': (rb'quic_demo_main', rb'MQTT connected over'),
    'subscription_acknowledged': (rb'quic_demo_main', rb'Subscription acknowledged'),
}
TRANSPORT_EVENT = {'QUIC': 'quic_handshake_completed', 'TCP_TLS': 'tcp_tls_connected'}
APP_EVENT = {'QUIC': 'quic_connection_established_app', 'TCP_TLS': 'tcp_tls_connection_established_app'}


def mask(text):
    """Mask the Wi-Fi network name and the access point MAC in raw log text before it is written to a result file."""
    text = re.sub(r'(connected with ).+?(, aid = )', r'\1<SSID>\2', text)
    text = re.sub(r'(bssid = )[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}', r'\1<BSSID>', text)
    return text


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def analyze(r):
    d = STUDY / Path(r['raw_serial_path']).parent
    serial = d / 'serial.raw.log'
    raw = serial.read_bytes()
    rec = [json.loads(l) for l in (d / 'serial_receipts.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    anchor = dt.datetime.fromisoformat(json.loads((d / 'reset_event.json').read_text(encoding='utf-8'))['reset_release_utc'])
    by_line = {x['line_no']: x for x in rec} if 'line_no' in rec[0] else None  # HBPSN-08 uses one receipt per line
    offs = None if by_line else [x['offset'] for x in rec]

    def receipt(o, lineno):
        if by_line is not None:
            return dt.datetime.fromisoformat(by_line[lineno]['utc'])
        x = rec[bisect.bisect_right(offs, o) - 1]
        assert x['offset'] <= o < x['offset'] + x['length'], (r['run_id'], o, x)
        return dt.datetime.fromisoformat(x['utc'])

    events, pos, boots, ended_by_second_banner = {}, 0, 0, False
    for lineno, ln in enumerate(raw.split(b'\n'), 1):
        start = pos
        pos += len(ln) + 1
        t = ln.rstrip(b'\r')
        m = LINE.match(t)
        body = m.group(2) if m else t
        if b'ESP-ROM:' in body:
            boots += 1
            if boots == 2:
                ended_by_second_banner = True
                break
        if boots != 1:
            continue
        u = UP.match(body)
        if not u:
            continue
        up_ms, tag, msg = int(u.group(1)), u.group(2), u.group(3)
        for k, (tg, pre) in EV.items():
            if k not in events and tag == tg and msg.startswith(pre):
                last = min(start + len(ln), len(raw) - 1)
                events[k] = dict(line_no=lineno, uptime_ms=up_ms, host_utc=receipt(last, lineno), host_ms=(receipt(last, lineno) - anchor).total_seconds() * 1000,
                                 raw=mask(t.decode('utf-8', 'replace')))
    return dict(r=r, dir=d, events=events, ended=ended_by_second_banner, anchor=anchor, serial_sha=sha(serial), boots_seen=boots)


results = [analyze(r) for r in rows]
rel = lambda p: Path(p).relative_to(STUDY).as_posix()

with (HERE / 'connection_setup_events.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['run_id', 'transport', 'condition', 'event', 'serial_raw_log_line_no', 'esp_uptime_ms_clock_A', 'host_receipt_utc', 'host_ms_from_reset_release_clock_B', 'raw_line'])
    for x in results:
        for k in EV:
            if k in x['events']:
                e = x['events'][k]
                w.writerow([x['r']['run_id'], x['r']['transport'], x['r']['condition'], k, e['line_no'], e['uptime_ms'], e['host_utc'].isoformat(), round(e['host_ms']), e['raw']])

COLS = ['run_id', 'transport', 'condition', 'register_status', 'attempt_dir', 'reset_release_utc', 'first_boot_ended_by_second_rom_banner',
        'wifi_associated_ms_A', 'wifi_ip_ms_A', 'transport_connected_ms_A', 'mqtt_connected_ms_A', 'ip_to_mqtt_ms_A', 'ip_to_transport_ms_A', 'transport_to_mqtt_ms_A', 'app_connection_established_ms_A',
        'wifi_ip_ms_B', 'transport_connected_ms_B', 'mqtt_connected_ms_B', 'ip_to_mqtt_ms_B', 'serial_raw_log_sha256', 'note']
per = []
for x in results:
    r, e = x['r'], x['events']
    tk, ak = TRANSPORT_EVENT[r['transport']], APP_EVENT[r['transport']]
    g = lambda k, c='uptime_ms': e[k][c] if k in e else None
    diff = lambda a, b, c='uptime_ms': (e[b][c] - e[a][c]) if a in e and b in e else None
    note = ''
    if 'mqtt_connected' not in e:
        note = 'MQTT not connected in the first boot; the first boot ended with a panic and reboot (see register row and serial log)' if x['ended'] else 'MQTT not connected in the first boot'
    per.append([r['run_id'], r['transport'], r['condition'], r['status'], rel(x['dir']), x['anchor'].isoformat(), x['ended'],
                g('wifi_associated'), g('wifi_ip'), g(tk), g('mqtt_connected'), diff('wifi_ip', 'mqtt_connected'), diff('wifi_ip', tk), diff(tk, 'mqtt_connected'), g(ak),
                None if 'wifi_ip' not in e else round(e['wifi_ip']['host_ms']), None if tk not in e else round(e[tk]['host_ms']), None if 'mqtt_connected' not in e else round(e['mqtt_connected']['host_ms']),
                None if not ('wifi_ip' in e and 'mqtt_connected' in e) else round(e['mqtt_connected']['host_ms'] - e['wifi_ip']['host_ms']), x['serial_sha'], note])
with (HERE / 'connection_setup_per_run.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(COLS)
    w.writerows([['' if v is None else v for v in row] for row in per])

idx = {c: i for i, c in enumerate(COLS)}
METRICS = [('wifi_ip', 'wifi_ip_ms'), ('transport_connected', 'transport_connected_ms'), ('mqtt_connected', 'mqtt_connected_ms'), ('ip_to_mqtt', 'ip_to_mqtt_ms'),
           ('ip_to_transport', 'ip_to_transport_ms'), ('transport_to_mqtt', 'transport_to_mqtt_ms')]
with (HERE / 'connection_setup_summary.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['transport', 'metric', 'clock', 'n', 'median_ms', 'min_ms', 'max_ms', 'runs_included'])
    for tr in ('QUIC', 'TCP_TLS'):
        for name, col in METRICS:
            for clock in ('A', 'B'):
                c = f'{col}_{clock}'
                if c not in idx:
                    continue
                pairs = [(row[0], row[idx[c]]) for row in per if row[1] == tr and row[idx[c]] is not None]
                vals = [v for _, v in pairs]
                w.writerow([tr, name, clock, len(vals), statistics.median(vals) if vals else '', min(vals) if vals else '', max(vals) if vals else '', ' '.join(p for p, _ in pairs)])
print('written', [p.name for p in sorted(HERE.glob('connection_setup_*.csv'))])
print('register sha256', sha(REGISTER))
