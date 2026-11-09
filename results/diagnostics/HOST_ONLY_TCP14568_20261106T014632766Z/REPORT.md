# HOST_ONLY TCP14568 readiness diagnosis

**Both requested host-local TCP connections and TLS handshakes succeeded. Windows listener reporting remains inconsistent with the working service. HBPSN-04 remains NOT_RUN.** These probes do not establish board-to-server connectivity. No formal start is authorized by this result.

## Process identity and READY ordering

[Identity output](./server_identity.stdout.txt) verifies PID36536, parent18676, command line using this project .quic-venv and tcp_tls_server.py. The actual image executable is the venv base Python3.14 binary, consistent with the saved pyvenv configuration. No process was stopped or restarted in this diagnosis.

The unchanged [server source snapshot](./tcp_tls_server.source.snapshot.py) calls `await asyncio.start_server(...)` at line106, then prints READY at line110 inside the server context. It prints after successful bind/listen setup, not before. The saved [installed asyncio implementation](./asyncio_base_events.snapshot.py) has default start_serving=True at line1540, invokes server._start_serving at1663 before returning, and _start_serving invokes sock.listen at317. READY records successful setup at that moment; it alone is not a perpetual liveness guarantee.

## Windows commands and state interpretation

[Exact argv, timestamps, exit codes and output hashes](./commands.json). Each command has complete unfiltered stdout/stderr byte files (*.raw), readable copies (*.txt) and individual command metadata. No native output was piped through grep/Select-String in these saved checks. The all-TCP command and netstat retain unrelated rows for audit.

| Check | Exit | stdout | stderr |
|---|---:|---|---|
| server_identity | 0 | [253035 bytes](./server_identity.stdout.raw) | [0 bytes](./server_identity.stderr.raw) |
| cim_state_schema | 0 | [469 bytes](./cim_state_schema.stdout.raw) | [0 bytes](./cim_state_schema.stderr.raw) |
| before_powershell_all_tcp | 0 | [414425 bytes](./before_powershell_all_tcp.stdout.raw) | [0 bytes](./before_powershell_all_tcp.stderr.raw) |
| before_powershell_14568 | 0 | [1288 bytes](./before_powershell_14568.stdout.raw) | [0 bytes](./before_powershell_14568.stderr.raw) |
| before_powershell_listen | 1 | [0 bytes](./before_powershell_listen.stdout.raw) | [669 bytes](./before_powershell_listen.stderr.raw) |
| before_cim_14568 | 0 | [1277 bytes](./before_cim_14568.stdout.raw) | [0 bytes](./before_cim_14568.stderr.raw) |
| before_cim_state_raw | 0 | [5118 bytes](./before_cim_state_raw.stdout.raw) | [0 bytes](./before_cim_state_raw.stderr.raw) |
| before_netstat | 0 | [15060 bytes](./before_netstat.stdout.raw) | [0 bytes](./before_netstat.stderr.raw) |
| after_powershell_all_tcp | 0 | [418313 bytes](./after_powershell_all_tcp.stdout.raw) | [0 bytes](./after_powershell_all_tcp.stderr.raw) |
| after_powershell_14568 | 0 | [1288 bytes](./after_powershell_14568.stdout.raw) | [0 bytes](./after_powershell_14568.stderr.raw) |
| after_powershell_listen | 1 | [0 bytes](./after_powershell_listen.stdout.raw) | [669 bytes](./after_powershell_listen.stderr.raw) |
| after_cim_14568 | 0 | [1277 bytes](./after_cim_14568.stdout.raw) | [0 bytes](./after_cim_14568.stderr.raw) |
| after_cim_state_raw | 0 | [5118 bytes](./after_cim_state_raw.stdout.raw) | [0 bytes](./after_cim_state_raw.stderr.raw) |
| after_netstat | 0 | [15203 bytes](./after_netstat.stdout.raw) | [0 bytes](./after_netstat.stderr.raw) |

Before and after the two probes, Get-NetTCPConnection -State Listen -LocalPort14568 returned no matching instance and exit1 with the complete error retained. Other listener queries/netstat exited0. Numeric CIM State was0 both times; the raw property flags did not include NullValue. Default formatting/serialization can show a blank or null; that is distinct from the raw property value.

The local [CDXML enum snapshot](./MSFT_NetTCPConnection.cdxml.snapshot) maps Closed=1, Listen=2 and Bound=100, with no named State0. The [CIM schema output](./cim_state_schema.stdout.txt) ValueMap contains1–12, with no0. Microsoft [MSFT_NetTCPConnection documentation](https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/nettcpipprov/msft-nettcpconnection#properties) likewise defines Closed1/Listen2, not0. Therefore0 is an unrecognized/undefined value for this class and must not be interpreted as Closed or proof the service cannot accept connections. The separate .NET TcpState Unknown0 definition is not a definition of this CIM class. Exact cause of the reporting discrepancy is unresolved.

## Exactly one TLS probe per requested address

Executed by the existing project .quic-venv, recorded in [runtime metadata](./runtime.json). Each address had one shared five-second TCP+TLS deadline, no retry. TLS minimum and maximum were1.3, ALPN offered mqtt. Existing lab policy retained: CERT_NONE and hostname checking disabled, followed by explicit certificate fingerprint comparison. No MQTT bytes were sent; the client socket closed after the handshake.

| Target | Start UTC | Local endpoint | TCP / TLS | TLS complete after |
|---|---|---|---|---:|
| 127.0.0.1:14568 | 2026-11-06T01:47:54.457822+00:00 | 127.0.0.1:50516 | CONNECTED / NEGOTIATED | 54.8824 ms |
| 192.168.137.1:14568 | 2026-11-06T01:47:54.869278+00:00 | 192.168.137.1:50517 | CONNECTED / NEGOTIATED | 11.8204 ms |

Both negotiated TLSv1.3 / TLS_AES_256_GCM_SHA384 / ALPN mqtt. Both client exceptions were null; no TCP or handshake timeout occurred. The timing values describe these host probes, not application RTT measurements. [Full outcomes](./probe_results.json) retain separate TCP/handshake/close UTC times, local/peer endpoints and exception fields.

Both peer DER certificate SHA-256 fingerprints were `fed2844dd91a687e2116bb21f356acc0e39839979ae9737dda1218ce8778a328`, matching DER decoded from the preserved server certificate. Preserved PEM file SHA-256 remains `dad4aa42a253793e77b161ac0846e6a1b39447b4d207572739b24b41dbfce462`. PEM-file hash and DER-certificate fingerprint are different representations, not a mismatch. [Certificate provenance](./expected_certificate.json), [peer1 DER](./probe_1.peer_certificate.der), [peer2 DER](./probe_2.peer_certificate.der).

The probe client used its default TLS1.3 cipher preferences, resulting in AES256. This is not the formal firmware startup cipher verification: the frozen measured TCP_TLS boot must still report TLS_AES_128_GCM_SHA256/suite0x1301, ALPN mqtt, TCP_NODELAY1 and WIFI_PS_NONE readback. No server configuration was changed.

## Probe-associated server evidence

Server stdout/stderr and sensor CSV were snapshotted at actual byte boundaries before/after each connection and around the overall checks. Original sources were never truncated. Delta files below are HOST_ONLY probe-associated evidence, not formal-run errors or measurements. Server log lines lack peer endpoints/timestamps; temporal bracketing alone does not establish the precise cause of an error.

| Probe | Stream | Start byte | End byte | Delta |
|---|---|---:|---:|---|
| 1 | stdout | 147 | 244 | [raw](./probe_1.server.stdout.delta.log) |
| 1 | stderr | 0 | 80 | [raw](./probe_1.server.stderr.delta.log) |
| 1 | sensor_csv | 97 | 97 | [raw](./probe_1.server.sensor_csv.delta.log) |
| 2 | stdout | 244 | 341 | [raw](./probe_2.server.stdout.delta.log) |
| 2 | stderr | 80 | 160 | [raw](./probe_2.server.stderr.delta.log) |
| 2 | sensor_csv | 97 | 97 | [raw](./probe_2.server.sensor_csv.delta.log) |

Each stdout delta contains one TCP+TLS CONNECTED line with the negotiated values. Each stderr delta contains `TCP+TLS ERROR: [WinError 64] The specified network name is no longer available` after that probe closed. Both lines are retained, not erased or attributed to HBPSN-04. The server emits only the exception string, so no server traceback is available. Probe client operations completed without exceptions. Sensor CSV remained97bytes with no new MQTT/sensor record.

[Before-check boundaries](./before_checks.boundaries.json), [after-check boundaries](./after_checks.boundaries.json), all intermediate boundary JSONs and full prefix snapshots preserve source paths, real UTC times, byte offsets and prefix hashes.

## Preservation and conclusion

TCP connectivity and TLS negotiation pass for both requested local routes. The observed failure is listener-state reporting; a stable LISTENING entry remains unconfirmed, despite functional acceptance. The root cause of State0/netstat omission and the server close-associated WinError64 messages is not established. These probes do not test an external device, Wi-Fi client path, formal MQTT transaction or formal cipher gate.

[Protected hashes after checks](./protected_after.json) confirm server/source, certificate/key, frozen plan and both registers unchanged. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP are preserved; HBPSN-04 stays NOT_RUN. Previous blocked-preflight evidence remains intact. QUIC crash remains unresolved. No restart, source/config edit, firewall/Clumsy change, COM6 open, flash, reset or formal timer occurred. TEST_ONLY firmware/logger remain untouched.
