# LONG_RUN_RECONNECT_20261124: 8 h QUIC run with automatic reconnect (images ft3/fq3)

Profile: `profiles/reconnect_20261124` (a copy of `profiles/fixed_20261118`; the fixed profile and earlier results are unchanged).
Board: ESP32-C6 on COM6. Laptop Windows Mobile Hotspot 192.168.137.1, 2.4 GHz. Normal network, no Clumsy.
Server: `quic_server.py` (aioquic, MQTT over QUIC, UDP 14567).

## What is new in ft3/fq3 (compared with ft2/fq2)
- **Diagnostics.** A `DIAG` line every 60 s with:
  - RSSI, Wi-Fi IP state, free heap, pending echoes and echo age.
  - TCP+TLS: `unacked`, `unsent`, `nrtx`, `rto` and the send window from the lwIP pcb.
  - QUIC: bytes in flight, cwnd, RTT, `pto_count`, `lost_pending`, the stream's `tx_loss_count` and the stream receive offset.
  - It also logs `WIFI_EVENT` lines, `APP_RX_DROP` (QUIC receive buffer full; before this, data was dropped silently) and `QUIC_TIMEOUT`.
- **STALL.** If the oldest unanswered message is 15 s old, the board logs `STALL` with the full state.
- **Automatic reconnect.**
  - Triggers: STALL, a transport or MQTT error, or the keep-alive timing out.
  - The old connection is closed cleanly (MQTT DISCONNECT, then TLS close_notify or QUIC CONNECTION_CLOSE). Wi-Fi stays up.
  - New attempts follow with backoff of 1, 2, 4, 8, 16, then 30 s.
  - Each reconnect logs `RECONNECT` with: failure time, reconnect start, attempts, handshake ms, CONNECT→CONNACK ms and downtime.
  - Message sequence numbers continue across reconnects.
- **First connection.** The call order and the 1 s delay before MQTT CONNECT are the same as before. The one change: if the *first* connection fails, the board now enters the retry loop instead of stopping the task.
- Image sizes: ft3 1,507,360 B (sha256 `b7f7ba4d…`), fq3 1,645,632 B (sha256 `d1f94585…`). Both built with `HEAPLOG=1`.

## Result: QUIC, 8 h (`quic/SUMMARY.md`)

| item | value |
|---|---|
| messages sent / echoed / missing | **5,746 / 5,746 / 0** |
| STALL lines, connection failures, reconnects | **0 / 0 / 0** |
| reboots, panics | 0 / 0 |
| app RTT ms | median 65.7, mean 69.2, P95 105.9, min 24.6, max 408.7 (flat in every hour) |
| RSSI dBm (479 samples) | median −31, min −55, max −27 |
| free heap | 174,384 → 172,928 B (−183 B/h); minimum free heap 142,684 B, unchanged after the first minutes |
| APP_RX_DROP, QUIC_TIMEOUT, PTO, lost packets | all 0 |
| hotspot watchdog | no outage in 8 h 10 min |

No stall happened, so tonight's run did not reproduce the two stalls from the earlier 12 h runs. The reconnect path itself was exercised in the smoke test and in `RECONNECT_TEST_20261125`.

Note: `in_flight` was 0 in all 479 DIAG samples. The DIAG snapshot is taken in the publish loop, after the previous echo has normally been acknowledged, so this sampling cannot show short in-flight periods. It is not evidence of a fault.

## Smoke tests (5 min each: server killed at 90 s, restarted at 120 s)
- **`smoke_quic/` (fq3, COM6): passed.**
  - STALL after 15 s without an echo; seq 16–18 were lost while the server was down. CONNECTION_CLOSE was sent.
  - Attempt 1 failed (`quic_handshake`, 20.5 s, server still down). Attempt 2 succeeded: handshake 9,883 ms, CONNACK 33 ms, downtime 33.4 s.
  - No reboot. The slow handshake (cwnd 4,200, srtt 423 ms) is noted for follow-up.
- **`smoke_tcp_tls/`, `smoke_tcp_tls_retry/` (ft3 on a second board, COM8): failed before the first connection.**
  - The board got IPv4 (192.168.137.45) but never the IPv6 link-local event, and `example_connect` waits for both.
  - Because of this, no parallel TCP+TLS run was made tonight (operator decision: QUIC only).

## Deviations
- **No packet capture.** pktmon is installed (Wireshark/dumpcap is not), but starting it needs an elevation prompt, which nobody could answer unattended. The run used `-NoPktmon`.
- **8 h instead of 12 h, and QUIC only.** The time was shortened for the supervisor meeting, and the COM8 IPv6 start-up hang ruled out the TCP+TLS run.
- **IPv6 start-up hang.** It appeared on both boards after about 16:00 UTC and persisted after a hotspot restart. It is handled in `RECONNECT_TEST_20261125` with IPv4-only start-up images.
- **Later script fix.** After this run, `run_long.ps1` was fixed: PowerShell variable names are case-insensitive, so `$port` (the server port) overwrote `$Port` (the COM port). This run was started with the COM6 default, which was not affected.

## Files
- `quic/`
  - `serial_raw.log`: host-timestamped board log.
  - `server_sensor.csv`, `prechecks.json`, `run_events.jsonl`, `hotspot_watch.jsonl`.
  - Analysis: `SUMMARY.md`, `rtt.csv`, `heap.csv`, `diag.csv`, `reconnects.csv`, `stalls.csv`, `failures.csv`, `wifi_events.csv`, `lost_seq.csv` (from `analyze_reconnect.py`).
- `smoke_*`: serial logs and server logs of the smoke tests.
- Wi-Fi SSID and password are masked in the committed files (`<SSID_MASKED>`, `<WIFI_PASSWORD_MASKED>`).
