"""Offline reporting only; does not repeat any connection attempt."""
from pathlib import Path
import datetime as dt
import hashlib
import json

out=Path(__file__).resolve().parent
def load(n):return json.loads((out/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=load('probe_results.json');commands=load('commands.json')
assert len(results)==2 and all(x['tcp']=='CONNECTED' and x['tls']=='NEGOTIATED' and x['certificate_matches_preserved'] and x['exception'] is None for x in results)
lines=['# HOST_ONLY TCP14568 readiness diagnosis', '',
'**Both requested host-local TCP connections and TLS handshakes succeeded. Windows listener reporting remains inconsistent with the working service. HBPSN-04 remains NOT_RUN.** These probes do not establish board-to-server connectivity. No formal start is authorized by this result.', '',
'## Process identity and READY ordering', '',
'[Identity output](./server_identity.stdout.txt) verifies PID36536, parent18676, command line using this project .quic-venv and tcp_tls_server.py. The actual image executable is the venv base Python3.14 binary, consistent with the saved pyvenv configuration. No process was stopped or restarted in this diagnosis.', '',
'The unchanged [server source snapshot](./tcp_tls_server.source.snapshot.py) calls `await asyncio.start_server(...)` at line106, then prints READY at line110 inside the server context. It prints after successful bind/listen setup, not before. The saved [installed asyncio implementation](./asyncio_base_events.snapshot.py) has default start_serving=True at line1540, invokes server._start_serving at1663 before returning, and _start_serving invokes sock.listen at317. READY records successful setup at that moment; it alone is not a perpetual liveness guarantee.', '',
'## Windows commands and state interpretation', '',
'[Exact argv, timestamps, exit codes and output hashes](./commands.json). Each command has complete unfiltered stdout/stderr byte files (*.raw), readable copies (*.txt) and individual command metadata. No native output was piped through grep/Select-String in these saved checks. The all-TCP command and netstat retain unrelated rows for audit.', '',
'| Check | Exit | stdout | stderr |', '|---|---:|---|---|']
for c in commands:
    n=c['name'];lines.append(f"| {n} | {c['exit_code']} | [{c['stdout_bytes']} bytes](./{n}.stdout.raw) | [{c['stderr_bytes']} bytes](./{n}.stderr.raw) |")
lines += ['',
'Before and after the two probes, Get-NetTCPConnection -State Listen -LocalPort14568 returned no matching instance and exit1 with the complete error retained. Other listener queries/netstat exited0. Numeric CIM State was0 both times; the raw property flags did not include NullValue. Default formatting/serialization can show a blank or null; that is distinct from the raw property value.', '',
'The local [CDXML enum snapshot](./MSFT_NetTCPConnection.cdxml.snapshot) maps Closed=1, Listen=2 and Bound=100, with no named State0. The [CIM schema output](./cim_state_schema.stdout.txt) ValueMap contains1–12, with no0. Microsoft [MSFT_NetTCPConnection documentation](https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/nettcpipprov/msft-nettcpconnection#properties) likewise defines Closed1/Listen2, not0. Therefore0 is an unrecognized/undefined value for this class and must not be interpreted as Closed or proof the service cannot accept connections. The separate .NET TcpState Unknown0 definition is not a definition of this CIM class. Exact cause of the reporting discrepancy is unresolved.', '',
'## Exactly one TLS probe per requested address', '',
'Executed by the existing project .quic-venv, recorded in [runtime metadata](./runtime.json). Each address had one shared five-second TCP+TLS deadline, no retry. TLS minimum and maximum were1.3, ALPN offered mqtt. Existing lab policy retained: CERT_NONE and hostname checking disabled, followed by explicit certificate fingerprint comparison. No MQTT bytes were sent; the client socket closed after the handshake.', '',
'| Target | Start UTC | Local endpoint | TCP / TLS | TLS complete after |', '|---|---|---|---|---:|']
for r in results:
    lines.append(f"| {r['address']}:14568 | {r['started_utc']} | {r['local_address'][0]}:{r['local_address'][1]} | {r['tcp']} / {r['tls']} | {r['total_tcp_tls_seconds']*1000:.4f} ms |")
cert=load('expected_certificate.json')
lines += ['',
'Both negotiated TLSv1.3 / TLS_AES_256_GCM_SHA384 / ALPN mqtt. Both client exceptions were null; no TCP or handshake timeout occurred. The timing values describe these host probes, not application RTT measurements. [Full outcomes](./probe_results.json) retain separate TCP/handshake/close UTC times, local/peer endpoints and exception fields.', '',
f"Both peer DER certificate SHA-256 fingerprints were `{cert['certificate_der_sha256']}`, matching DER decoded from the preserved server certificate. Preserved PEM file SHA-256 remains `{cert['preserved_pem_sha256']}`. PEM-file hash and DER-certificate fingerprint are different representations, not a mismatch. [Certificate provenance](./expected_certificate.json), [peer1 DER](./probe_1.peer_certificate.der), [peer2 DER](./probe_2.peer_certificate.der).", '',
'The probe client used its default TLS1.3 cipher preferences, resulting in AES256. This is not the formal firmware startup cipher verification: the frozen measured TCP_TLS boot must still report TLS_AES_128_GCM_SHA256/suite0x1301, ALPN mqtt, TCP_NODELAY1 and WIFI_PS_NONE readback. No server configuration was changed.', '',
'## Probe-associated server evidence', '',
'Server stdout/stderr and sensor CSV were snapshotted at actual byte boundaries before/after each connection and around the overall checks. Original sources were never truncated. Delta files below are HOST_ONLY probe-associated evidence, not formal-run errors or measurements. Server log lines lack peer endpoints/timestamps; temporal bracketing alone does not establish the precise cause of an error.', '',
'| Probe | Stream | Start byte | End byte | Delta |', '|---|---|---:|---:|---|']
for i in (1,2):
    before=load(f'probe_{i}_before.boundaries.json');after=load(f'probe_{i}_after.boundaries.json')
    for name in ('stdout','stderr','sensor_csv'):
        lines.append(f"| {i} | {name} | {before['streams'][name]['byte_offset']} | {after['streams'][name]['byte_offset']} | [raw](./probe_{i}.server.{name}.delta.log) |")
lines += ['',
'Each stdout delta contains one TCP+TLS CONNECTED line with the negotiated values. Each stderr delta contains `TCP+TLS ERROR: [WinError 64] The specified network name is no longer available` after that probe closed. Both lines are retained, not erased or attributed to HBPSN-04. The server emits only the exception string, so no server traceback is available. Probe client operations completed without exceptions. Sensor CSV remained97bytes with no new MQTT/sensor record.', '',
'[Before-check boundaries](./before_checks.boundaries.json), [after-check boundaries](./after_checks.boundaries.json), all intermediate boundary JSONs and full prefix snapshots preserve source paths, real UTC times, byte offsets and prefix hashes.', '',
'## Preservation and conclusion', '',
'TCP connectivity and TLS negotiation pass for both requested local routes. The observed failure is listener-state reporting; a stable LISTENING entry remains unconfirmed, despite functional acceptance. The root cause of State0/netstat omission and the server close-associated WinError64 messages is not established. These probes do not test an external device, Wi-Fi client path, formal MQTT transaction or formal cipher gate.', '',
'[Protected hashes after checks](./protected_after.json) confirm server/source, certificate/key, frozen plan and both registers unchanged. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP are preserved; HBPSN-04 stays NOT_RUN. Previous blocked-preflight evidence remains intact. QUIC crash remains unresolved. No restart, source/config edit, firewall/Clumsy change, COM6 open, flash, reset or formal timer occurred. TEST_ONLY firmware/logger remain untouched.', '']
with (out/'REPORT.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
manifest=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.json']
with (out/'SHA256SUMS.json').open('x',encoding='utf-8') as f:json.dump(dict(label='HOST_ONLY_NOT_FORMAL',created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files=manifest),f,indent=2)
print(json.dumps(dict(report=str(out/'REPORT.md'),report_sha256=sha(out/'REPORT.md'),files=len(manifest),command_exit_codes={c['name']:c['exit_code'] for c in commands}),indent=2))
