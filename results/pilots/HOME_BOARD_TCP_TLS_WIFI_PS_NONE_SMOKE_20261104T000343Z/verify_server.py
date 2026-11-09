import datetime as dt
import json
from pathlib import Path
import socket
import ssl

folder=Path(__file__).resolve().parent
context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname=False
context.verify_mode=ssl.CERT_NONE
context.minimum_version=ssl.TLSVersion.TLSv1_3
context.maximum_version=ssl.TLSVersion.TLSv1_3
context.set_alpn_protocols(['mqtt'])
with socket.create_connection(('127.0.0.1',14568),timeout=5) as raw:
    with context.wrap_socket(raw,server_hostname='localhost') as secure:
        result=dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),endpoint='127.0.0.1:14568',tls=secure.version(),cipher=secure.cipher(),alpn=secure.selected_alpn_protocol(),purpose='Local listener TLS readiness probe only; no MQTT or sensor messages')
assert result['tls']=='TLSv1.3' and result['alpn']=='mqtt'
(folder/'server_tls_readiness.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
