# Connection-time test, 18 Nov 2026 (supervisor's test)

**This test uses the FIXED profile (`profiles/fixed_20261118`), NOT the formal 18-run builds (HBPSN-01..18).** The formal runs used the
frozen images, which contain the ngtcp2 `conn_new` alignment bug (see `results/diagnostics/quic_crash_20261117/`). Numbers here must
not be mixed with the formal runs without saying so.

## What was done
Each image boots once, joins Wi-Fi once (`WIFI_PS_NONE`, same as the formal profile), then repeats **50 times**:
open connection -> MQTT CONNECT/CONNACK -> MQTT DISCONNECT + protocol cleanup -> wait 3 s. No sensor loop, no DHT reads, no publishes.
Normal network (Windows Mobile Hotspot 2.4 GHz, 192.168.137.1), **Clumsy not running**, same laptop servers
(`tcp_tls_server.py` port 14568, `quic_server.py` port 14567). No heap poisoning, no checkpoints, `QUIET_MEASUREMENT=1`, partition 1,700K.
TCP+TLS was run first, then QUIC (supervisor's order). One board reset at the start of each run (RTS pulse by the capture script).

## Images (fixed profile, `FIXED_CT_MODE=1`)
| image | transport | bytes | sha256 |
|---|---|---|---|
| ctt | TCP+TLS 1.3 | 1,489,808 | 33bfdded2bbc8536168898aa6b172428cfa5904995da116db418fedc8bb40a94 |
| ctq | QUIC | 1,628,288 | bcd0ab676b9ad56c0621aa369491e69723a787fa685b4be2f5f950fbc6f03fe8 |

Code changes versus the verified fixed images fq/ft (all in `profiles/fixed_20261118/patch_ct.py`, behind compile switches that are off by default):
event-loop initialisation runs once per boot, timing task replaces the sensor task, timestamps in the transports.

## Definitions (all from `esp_timer_get_time()`, microseconds on the board)
- **TCP image:** `t0` = just before `socket()`. `tcp_connect` = `connect()` complete - `t0`. `tls_handshake` = `wolfSSL_connect` success - connect complete.
  `tcp_tls_total` = sum. TLS 1.3, `TLS13-AES128-GCM-SHA256`, ALPN mqtt (formal settings).
- **QUIC image:** `t0` = just before `quic_client_init_with_config` (socket, SSL context, ngtcp2 connection creation). `quic_init` = init done - `t0`.
  `quic_handshake_cb` = time of the ngtcp2 `handshake_completed` callback - `t0` (precise, taken inside the callback).
  `quic_ready_seen` = first time the same 100 ms polling loop as the formal firmware (`wait_for_quic_ready`) sees handshake done and stream credit - `t0`
  (quantised by the 100 ms polling and includes waiting for the server's stream-credit frame).
- **Both:** `mqtt_connect_to_connack` = `MQTT_Connect()` call start to return (CONNACK received). `connack_from_start` = CONNACK - `t0`.
- Statistics (median, mean, min, max, P95) over successful attempts, in ms; P95 by linear interpolation. Shown with and without attempt 1.

## Deviations from the formal firmware flow
- The formal task waits 1,000 ms between "connection established" and MQTT CONNECT. **Removed** here (it would add a constant to CONNACK time).
- Each attempt ends with MQTT DISCONNECT and the existing cleanup functions; the formal firmware never closes during a run.
- Because the QUIC handshake is also advanced by the 100 ms polling (`quic_client_process`), `quic_handshake_cb` can include up to ~100 ms polling delay; this is the same in the formal firmware.

## Results (see `SUMMARY.md`, per-protocol `summary_*.md`, `connection_time_*.csv`)
Both runs: 50 attempts, 50 OK, 0 failures, 0 crashes. Raw logs `serial_raw.log` (SSID masked), server logs, SHA-256 in `SHA256SUMS.txt`.

## Failed starts (kept for the record)
`tcp_tls/ABORTED_run1/run2_wrong_ssid_in_build_*`: the first two start attempts failed because images ctt/ctq/ft2/fq2 had been built from a profile
`sdkconfig` in which I had masked the Wi-Fi SSID for the commit (build then used the placeholder name). The board could not find the network
(reason 201) and rebooted in a loop; no test data. Fixed by taking the real Wi-Fi settings from the root `sdkconfig` at build time. The Windows hotspot
had also switched itself off in the meantime (no-client auto-off); the operator turned off that power saving. The images used for the results were rebuilt after the fix.

## Notes
- QUIC free heap falls slowly across attempts (223,632 B after attempt 10, 221,612 B after attempt 50, about 50 B per connect); TCP+TLS heap is flat (about 290 KB). Cause not investigated.
- TCP+TLS handshake time is dominated by TLS (about 1.52 s) because of software crypto on the ESP32-C6; this is not specific to this test.
