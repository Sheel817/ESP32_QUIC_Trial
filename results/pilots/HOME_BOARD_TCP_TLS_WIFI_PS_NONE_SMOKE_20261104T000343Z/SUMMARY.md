# HOME_BOARD TCP_TLS WIFI_PS_NONE startup smoke verification

**PASS_WITH_SERVER_LOG_WARNING**. Startup check only; no formal experiment was started. All 18 registered runs remain NOT_RUN and the CSV/workbook hashes are unchanged.

## Prepared artifacts and flash

Used only [matching TCP_TLS profile artifacts](../../../profiles/tcp_tls_wifi_ps_none_20261104/README.md): [application](../../../profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.bin), [ELF](../../../profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.elf), bootloader and partition table from the same profile. App SHA-256 **ff97eb5d20c9c47375539395f9cf23c1d0780381562cf511094d4b525ab17de8**; ELF SHA-256 **1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6**. [Pre-flash artifact checks](./preflash_artifacts.json).

Flash command from that build directory: `esptool --chip esp32c6 --port COM6 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args`. Bootloader 0x0, partition 0x8000 and app 0x10000 all passed written-data hash verification; exit 0. [Successful raw flash log](./HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_flash.log), [result](./flash_result.json). Esptool logged an in-memory bootloader header/digest update for flash parameters; prepared disk inputs remain hash-identical.

An initial attempt failed opening the still-busy COM6 port, before connection/reset/write: [failed-attempt evidence](./flash_attempt1_port_busy.log). Its prerequisite listener query had returned no match because Windows CIM reports this listener with blank State/offload metadata, despite the project server process and socket existing. A [local TLS readiness probe](./server_tls_readiness.json) verified the actual listener before retrying. The probe used TLS_AES_256_GCM_SHA384; it is a separate host-only connection, not the board negotiation. The existing monitor was then gracefully exited via its control file, flushing/closing output: [closure record](./previous_monitor_closed.json). No unrelated listener or QUIC server was stopped.

## Persistent server and monitor

Project tcp_tls_server.py started persistently with `.quic-venv/Scripts/python.exe -u`, TCP 0.0.0.0:14568, owner PID 26228. [Server metadata](./server_session.json), [live stdout](./tcp_tls_server.stdout.log), [live stderr](./tcp_tls_server.stderr.log), [sensor CSV source](../../../logs/sensor_tcp_tls_20261104T000344_550740Z_xly3omnb.csv). No server source changes. The listener is further demonstrated by successful board connections and matching sensor records.

The new persistent ESP-IDF monitor uses the TCP_TLS ELF, COM6 at 115200: [monitor command and PIDs](./monitor_session.json), [HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE serial log](./HOME_BOARD_TCP_TLS_WIFI_PS_NONE_SMOKE_serial.log). Logging was active before the controlled startup reset requested at **2026-11-04T00:05:59.620894+00:00**. Initial startup output from opening the port precedes the explicit reset marker and is excluded from the checked five echoes. Flash downloader/post-write resets and this controlled startup reset are recorded; no formal 37-minute recording was started.

Startup digest prefix `1f661a4f7...` matches the prepared ELF; a full on-device ELF digest was not printed. Explicit setter/readback reports **requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)**. Assigned IP **192.168.137.212**. TCP_NODELAY **1**. TCP_TLS connection, MQTT connection and subscription acknowledgement confirmed.

Actual board TLS evidence:

```text
2026-11-04T02:06:05 I (6087) TLS: TCP_TLS negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256 wolfSSL_cipher=TLS13-AES128-GCM-SHA256 suite=0x1301 ALPN=mqtt certificate_verification=NONE (mode=0)
```

## First five APP_RTT echoes and matching sensors

| Sequence | ESP log uptime ms | APP_RTT ms | Temperature C | Humidity %RH | Sensor error |
|---:|---:|---:|---:|---:|---:|
| 1 | 12247 | 87.693 | 30.0 | 31.0 | 0 |
| 2 | 17277 | 107.333 | 29.0 | 31.0 | 0 |
| 3 | 22207 | 27.586 | 29.0 | 33.0 | 0 |
| 4 | 27237 | 47.497 | 29.0 | 34.0 | 0 |
| 5 | 32267 | 67.473 | 29.0 | 31.0 | 0 |

All five match server records by post-reset UTC boundary, sequence, client ID `esp32_quic_client`, topic `esp32/quic/test` and DHT11 payload. Each sensor_error is 0. [Joined echoes/sensor CSV](./first_five_echoes_and_sensors.csv), [matching sensor rows](./matching_server_sensor_records.csv), [serial snapshot](./serial_startup_through_first_five.log), [server stdout snapshot](./tcp_tls_server_stdout_snapshot.log). These are startup echoes, without warmup exclusion or formal-run eligibility. No connection errors or sequence gaps were observed in this controlled startup through echo five; all warning/error evidence remains in the raw log.

## Preservation and next registered run

All 6198 original-build and 1796 QUIC-profile inventoried files retain their recorded hashes; both QUIC BIN/ELF pairs and the formal register CSV/workbook match their pre-smoke hashes. No rebuild, firmware edit or dependency change occurred. This smoke output is separate under results/pilots. Clumsy effects were not enabled or settings changed by this task; existing filter remains untouched.

First registered run is **HBPSN-01 — QUIC — CONTROL**, still **NOT_RUN**. [Register](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/run_register.csv). This smoke test does not consume or substitute for it. TCP server and new monitor are left running; the prior QUIC server is also preserved.

[Structured verification](./verification.json) contains actual source/artifact paths, reset/completion UTC times, all first-five measurements, sensor UTC timestamps and preservation checks.


## Server-log warning

The persistent server stderr contains 1 bare `TCP+TLS ERROR:` line(s), with no timestamp, peer/connection ID or error detail. They cannot be confidently attributed to the measured boot versus setup/local-probe connections. The controlled serial startup through the first five echoes has no connection errors, all five matching sensor records succeeded, and later fresh RTTs continue. This caveat is retained rather than claiming an entirely error-free server log. See [server stderr snapshot](./tcp_tls_server_stderr_snapshot.log) and structured verification.
