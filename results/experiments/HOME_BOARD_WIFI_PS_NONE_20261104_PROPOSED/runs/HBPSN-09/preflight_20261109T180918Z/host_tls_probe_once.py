"""One bounded preflight TLS connection to 127.0.0.1:14568. No MQTT bytes, no board or COM6 access."""
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
