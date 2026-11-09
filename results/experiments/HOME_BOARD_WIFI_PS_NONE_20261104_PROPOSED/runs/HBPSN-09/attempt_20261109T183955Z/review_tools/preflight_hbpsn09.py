"""HBPSN-09 preflight. Usage: python preflight_hbpsn09.py probe | flash   (cwd = project root)."""
import datetime as dt, hashlib, json, re, subprocess, sys, time
from pathlib import Path

root = Path.cwd()
assert (root / 'HBPSN08_TASK.md').exists()
study = root / 'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
BUILD = root / 'profiles/tcp_tls_wifi_ps_none_20261104/build'
PY_IDF = 'C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe'
CMD = [PY_IDF, '-m', 'esptool', '--chip', 'esp32c6', '--port', 'COM6', '--baud', '460800', '--before', 'default-reset',
       '--after', 'hard-reset', 'write-flash', '@flash_args']
LOGS = {
    'stdout': root / 'results/preflights/HBPSN04_START_20261106T013540465Z/tcp_tls_server.stdout.log',
    'stderr': root / 'results/preflights/HBPSN04_START_20261106T013540465Z/tcp_tls_server.stderr.log',
    'sensor_csv': root / 'logs/sensor_tcp_tls_20261106T013631_157099Z_mrgf6j6d.csv',
}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_flash_args():
    manifest = json.loads((study / 'freeze_manifest.json').read_text(encoding='utf-8'))
    frozen = {Path(a['path']).resolve(): a for a in manifest['artifacts'] if a['artifact_id'] == 'TCP_TLS_PSN'}
    text = (BUILD / 'flash_args').read_text(encoding='utf-8')
    rows = []
    for offset, name in re.findall(r'^(0x[0-9a-fA-F]+)\s+(\S+)\s*$', text, re.M):
        p = (BUILD / name).resolve()
        a = frozen.get(p)
        actual = sh(p)
        rows.append(dict(offset=offset, file=name, path=str(p), bytes=p.stat().st_size, sha256=actual,
                         frozen_sha256=a and a['sha256'], frozen_bytes=a and a['bytes'],
                         match=bool(a) and a['sha256'] == actual and a['bytes'] == p.stat().st_size))
    return dict(flash_args_path=str(BUILD / 'flash_args'), flash_args_sha256=sh(BUILD / 'flash_args'), flash_args_text=text,
                freeze_manifest_sha256=sh(study / 'freeze_manifest.json'), artifact_id='TCP_TLS_PSN', files=rows,
                all_match=len(rows) == 3 and all(r['match'] for r in rows))


def dirs(ts):
    return [root / 'runs/HBPSN-09' / ('preflight_' + ts), study / 'runs/HBPSN-09' / ('preflight_' + ts)]


def save(ts, rec):
    for d in dirs(ts):
        (d / 'preflight_record.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')


def bounds():
    return {k: dict(source=str(p), byte_offset=p.stat().st_size) for k, p in LOGS.items()}


PROBE = '''"""One bounded preflight TLS connection to 127.0.0.1:14568. No MQTT bytes, no board or COM6 access."""
import datetime as dt, hashlib, json, socket, ssl, sys, time, traceback
from pathlib import Path
out = Path(__file__).resolve().parent
root = Path(sys.argv[1])
now = lambda: dt.datetime.now(dt.timezone.utc).isoformat()
r = dict(label='HOST_ONLY_PREFLIGHT_NOT_FORMAL', started_utc=now(), target=['127.0.0.1', 14568], timeout_seconds=5, mqtt_bytes_sent=0, exception=None)
begin = time.monotonic(); sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); tls = None
try:
    sock.settimeout(5); sock.connect(('127.0.0.1', 14568)); r['tcp'] = 'CONNECTED'
    r.update(local=sock.getsockname(), peer=sock.getpeername())
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); c.check_hostname = False; c.verify_mode = ssl.CERT_NONE
    c.minimum_version = ssl.TLSVersion.TLSv1_3; c.maximum_version = ssl.TLSVersion.TLSv1_3; c.set_alpn_protocols(['mqtt'])
    tls = c.wrap_socket(sock, server_hostname='127.0.0.1', do_handshake_on_connect=False); tls.settimeout(5); tls.do_handshake()
    fp = hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()
    exp = hashlib.sha256(ssl.PEM_cert_to_DER_cert((root / 'server-cert.pem').read_text())).hexdigest()
    r.update(tls='NEGOTIATED', tls_version=tls.version(), cipher=tls.cipher(), alpn=tls.selected_alpn_protocol(), peer_der_sha256=fp, preserved_der_sha256=exp, certificate_match=fp == exp)
except Exception as e:
    r.update(exception=dict(type=type(e).__name__, repr=repr(e), traceback=traceback.format_exc()))
finally:
    (tls or sock).close(); r.update(ended_utc=now(), elapsed_seconds=time.monotonic() - begin)
(out / 'host_tls_probe.json').write_text(json.dumps(r, indent=2), encoding='utf-8')
print(json.dumps(r))
sys.exit(0 if r.get('tcp') == 'CONNECTED' and r.get('tls') == 'NEGOTIATED' and r.get('certificate_match') and r.get('alpn') == 'mqtt' and r.get('tls_version') == 'TLSv1.3' else 1)
'''


def stage_probe():
    ts = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for d in dirs(ts):
        d.mkdir(parents=True, exist_ok=False)
    ver = verify_flash_args()
    proc = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                           '$p=Get-CimInstance Win32_Process -Filter "ProcessId=36536"; $p.CommandLine; $p.CreationDate.ToUniversalTime().ToString("o")'],
                          capture_output=True, text=True, timeout=30)
    rec = dict(run_id='HBPSN-09', transport='TCP_TLS', condition='CONTROL', order=9, block=2, label='SETUP_ONLY_NOT_FORMAL_NO_MEASURED_RESET',
               created_utc=utc(), protocol_plan_sha256=sh(study / 'EXPERIMENT_PLAN_PROPOSED_V1.md'),
               operator_decision_receipt_utc='2026-11-09T18:06:20.7522475Z',
               schedule_confirmation='Plan line 48, register row 9 and freeze_manifest order 9: HBPSN-09, TCP_TLS, CONTROL; configured lag 0, drop 0, direction none.',
               artifact_path_correction=dict(
                   wrong_path_in_HBPSN08_TASK='profiles\\wifi_ps_none_20261103\\build\\tcp_tls.bin',
                   finding='That file does not exist and no tcp_tls*.bin exists in the project.',
                   used='freeze_manifest.json artifact TCP_TLS_PSN: profiles\\tcp_tls_wifi_ps_none_20261104\\build\\ via flash_args',
                   authority='Operator decision 2026-11-09'),
               flash_args_verification=ver,
               server=dict(pid=36536, process_query=proc.stdout.strip().splitlines(),
                           socket_note='Get-NetTCPConnection shows 0.0.0.0:14568 owned by this PID with a blank state; netstat lists no LISTENING entry. Same reporting discrepancy recorded for HBPSN-04.'))
    save(ts, rec)
    print('folder', ts)
    print('flash_args all_match', ver['all_match'])
    for r in ver['files']:
        print(' ', r['offset'], r['file'], r['bytes'], r['sha256'], 'match', r['match'])
    if not ver['all_match']:
        rec['stopped'] = 'flash_args do not all match freeze_manifest.json'
        save(ts, rec)
        sys.exit('STOP: manifest mismatch')
    probe_path = dirs(ts)[0] / 'host_tls_probe_once.py'
    probe_path.write_text(PROBE, encoding='utf-8')
    (dirs(ts)[1] / 'host_tls_probe_once.py').write_text(PROBE, encoding='utf-8')
    before = bounds()
    cmd = [str(root / '.quic-venv/Scripts/python.exe'), '-B', str(probe_path), str(root)]
    started = utc()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    ended = utc()
    time.sleep(1.5)
    after = bounds()
    new = {}
    for k, src in LOGS.items():
        with src.open('rb') as f:
            f.seek(before[k]['byte_offset'])
            new[k] = f.read(after[k]['byte_offset'] - before[k]['byte_offset']).decode('utf-8', 'replace')
    result = json.loads((probe_path.parent / 'host_tls_probe.json').read_text(encoding='utf-8'))
    (dirs(ts)[1] / 'host_tls_probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    rec['tls_probe'] = dict(command=cmd, started_utc=started, ended_utc=ended, exit_code=p.returncode, stderr=p.stderr, result=result,
                            com6_touched=False, server_log_boundaries_before=before, server_log_boundaries_after=after, server_log_bytes_added_by_probe_window=new,
                            passed=p.returncode == 0)
    save(ts, rec)
    print('probe exit', p.returncode, p.stderr)
    print(json.dumps(result, indent=1))
    print('server lines added:', json.dumps(new, indent=1))
    if p.returncode != 0:
        rec['stopped'] = 'TLS probe failed'
        save(ts, rec)
        sys.exit('STOP: probe failed')


def stage_flash():
    folders = sorted((root / 'runs/HBPSN-09').glob('preflight_*'))
    assert len(folders) == 1, folders
    ts = folders[0].name.split('_', 1)[1]
    rec = json.loads((folders[0] / 'preflight_record.json').read_text(encoding='utf-8'))
    assert rec['tls_probe']['passed'] is True and 'stopped' not in rec
    ver = verify_flash_args()
    assert ver['all_match'] and ver == rec['flash_args_verification'], 'flash_args changed since verification'
    started = utc()
    rec['flash'] = dict(started_utc=started, command=CMD, cwd=str(BUILD), setup_only=True, flash_args_verification_immediately_before=ver)
    save(ts, rec)
    p = subprocess.run(CMD, cwd=str(BUILD), capture_output=True, timeout=300)
    ended = utc()
    out = p.stdout + p.stderr
    for d in dirs(ts):
        (d / 'flash.log').write_bytes(out)
    text = out.decode('utf-8', 'replace')
    verified = len(re.findall(r'Hash of data verified', text))
    rec['flash'].update(ended_utc=ended, exit_code=p.returncode, verified_image_count=verified, full_esptool_output=text, flash_log_sha256=sh(folders[0] / 'flash.log'), passed=p.returncode == 0 and verified == 3)
    save(ts, rec)
    manifest = []
    for name in ['preflight_record.json', 'flash.log', 'host_tls_probe.json', 'host_tls_probe_once.py']:
        q = folders[0] / name
        manifest.append(dict(path=name, bytes=q.stat().st_size, sha256=sh(q)))
    for d in dirs(ts):
        (d / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('exit', p.returncode, 'verified images', verified, 'start', started, 'end', ended)
    print(text)
    for n in ['preflight_record.json', 'flash.log', 'SHA256SUMS.json']:
        print(n, 'run==mirror', sh(dirs(ts)[0] / n) == sh(dirs(ts)[1] / n), sh(dirs(ts)[0] / n))


{'probe': stage_probe, 'flash': stage_flash}[sys.argv[1]]()
