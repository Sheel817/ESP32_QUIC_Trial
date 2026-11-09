"""One bounded preflight TLS connection; no MQTT or board access."""
from pathlib import Path
import datetime as dt,hashlib,json,socket,ssl,sys,time,traceback
out=Path(__file__).resolve().parent;root=out.parents[5]
assert Path(sys.prefix).resolve()==(root/'.quic-venv').resolve()
result=dict(label='HOST_ONLY_PREFLIGHT_NOT_FORMAL',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),target=['192.168.137.1',14568],timeout_seconds=5,mqtt_bytes_sent=0,exception=None)
begin=time.monotonic();deadline=begin+5;sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);tls=None
try:
    sock.settimeout(5);sock.connect(('192.168.137.1',14568));result['tcp']='CONNECTED'
    result.update(local=sock.getsockname(),peer=sock.getpeername())
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE;ctx.minimum_version=ssl.TLSVersion.TLSv1_3;ctx.maximum_version=ssl.TLSVersion.TLSv1_3;ctx.set_alpn_protocols(['mqtt'])
    tls=ctx.wrap_socket(sock,server_hostname='192.168.137.1',do_handshake_on_connect=False);tls.settimeout(max(.001,deadline-time.monotonic()));tls.do_handshake()
    fingerprint=hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest();expected=hashlib.sha256(ssl.PEM_cert_to_DER_cert((root/'server-cert.pem').read_text())).hexdigest()
    result.update(tls='NEGOTIATED',tls_version=tls.version(),cipher=tls.cipher(),alpn=tls.selected_alpn_protocol(),peer_der_sha256=fingerprint,preserved_der_sha256=expected,certificate_match=fingerprint==expected,certificate_policy='Existing lab CERT_NONE; explicit preserved certificate fingerprint comparison')
except Exception as e:result.update(exception=dict(type=type(e).__name__,repr=repr(e),traceback=traceback.format_exc()))
finally:
    (tls or sock).close();result.update(ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-begin)
with (out/'host_tls_probe.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
assert result.get('tcp')=='CONNECTED' and result.get('tls')=='NEGOTIATED' and result.get('certificate_match') and result.get('alpn')=='mqtt',result
print(json.dumps(result))
