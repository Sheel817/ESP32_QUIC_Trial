# RECONNECT_TEST_20261125: controlled reconnect test, QUIC vs TCP+TLS (20 cycles each)

Profile: `profiles/reconnect_20261124`, images **fq3v4** (QUIC) and **ft3v4** (TCP+TLS).
- Same board (ESP32-C6, COM6) for both protocols.
- Laptop hotspot 192.168.137.1, 2.4 GHz. Normal network, no Clumsy, Wi-Fi kept up.
- Same pre-checks as the long runs: hotspot on, no Clumsy/WinDivert, COM port free, server port free, AC power. The hotspot watchdog runs throughout.

## Procedure (`reconnect_cycles.ps1`, unattended chain `reconnect_test_chain.ps1`)
1. Start the server, reset the board once, and wait for the first `CONNECT session=0`.
2. Repeat 20 times:
   - Let the connection run for 60 s.
   - Stop the server with `Stop-Process -Force`, so the OS closes the socket.
   - Wait 10 s, then restart the server and wait for its `READY`.
   - Wait for the board's `RECONNECT` line, with a 180 s timeout.
3. The test stops early if a pre-check fails or two cycles in a row fail.

Analysis: `analyze_cycles.py` writes `<proto>/SUMMARY.md` and `<proto>/cycles.csv`. Metrics per cycle:
- **(1) Detection:** server stop → board logs `CONNECTION_FAILED`, measured on the host clock.
- **(2) Reconnect duration (headline):** reconnect start (`RECONNECT_START`, the same instant as `CONNECTION_FAILED`) → handshake done (2a) and → MQTT CONNACK (2b). Measured entirely on the board clock. It includes the 1 s backoff and any failed attempts.
- **(3) Reference:** server READY → handshake done / CONNACK. Board times are mapped to the host clock at the `RECONNECT` line.

## Results (all ms)

| | QUIC (fq3v4) | TCP+TLS (ft3v4) |
|---|---|---|
| cycles reconnected / failed (timeout) | **20 / 0** | **20 / 0** |
| attempts per reconnect | 1 in all 20 cycles | 2 in all 20 cycles (attempt 1 always `tcp_tls_connect` timeout) |
| reboots / panics | 0 / 0 | 0 / 0 |
| **(2b) reconnect start → CONNACK**: median / min / max / P95 | **3,865 / 3,739 / 6,549 / 3,929** | **12,331 / 12,306 / 12,762 / 12,567** |
| (2a) reconnect start → handshake done: median / min / max / P95 | 3,809 / 3,655 / 3,849 / 3,838 | 12,317 / 12,296 / 12,555 / 12,551 |
| successful attempt only, attempt start → CONNACK: median / min / max / P95 | 2,829 / 2,704 / 5,514 / 2,894 | 4,298 / 4,288 / 4,743 / 4,548 |
| MQTT CONNECT → CONNACK: median / min / max / P95 | 51 / 26 / 2,745 / 90 | 15 / 9 / 215 / 19 |
| (1) detection: median / min / max / P95 | 19,977 / 15,110 / 20,176 / 20,154 | 214 / 125 / 350 / 347 |
| (3b) server READY → CONNACK: median / min / max / P95 | 13,129 / 8,027 / 13,537 / 13,408 | 2,040 / 1,806 / 2,510 / 2,399 |
| reconnect started before the server was READY | 0 / 20 | 20 / 20 |
| failure detected as | `stall` (no echo for 15 s) ×20 | `mqtt_process_error` ×16, `publish_failed` ×4 (TLS read errno 104 = connection reset) |
| messages lost (APP_RTT_LOST) | 60 (3 per cycle) | 5 |
| first connection after reset: transport / CONNACK | 2,725 / 84 | 1,550 / 19 |

## How to read the numbers (fairness)
- **Detection differs by design.**
  - TCP+TLS sees the reset from the killed server process within about 0.2 s.
  - QUIC gets no signal, because the new server instance has no state for the old connection. QUIC only notices through the 15 s no-echo STALL check. Since messages go out every 5 s, detection takes 15 or 20 s.
  - This is why metric (2) starts at reconnect start, not at the server stop.
- **With a 10 s outage, (2) still differs in what it contains.**
  - **QUIC:** the reconnect starts 5–10 s *after* the server is back (0/20 before READY). So (2) = 1 s backoff + one handshake (about 2.8 s) + CONNACK. This is a clean "reconnect to a live server" time.
  - **TCP+TLS:** the reconnect starts *during* the outage (20/20 before READY). The laptop does not answer SYNs to the closed port with a RST; it drops them. So:
    - Attempt 1 always ran into the 5 s connect timeout (errno 119).
    - After a 2 s backoff, attempt 2 started about 2.3 s before the server was READY. It completed after a SYN retransmission, about 2 s after READY.
    - So TCP's (2), about 12.3 s, is mostly the server outage plus the board's timeout and backoff schedule. It is not handshake cost. The same applies to TCP's "successful attempt" time of about 4.3 s.
  - The cost of one TCP+TLS connection to a live server is best seen in the first connection: 1.55 s transport + 19 ms CONNACK. The QUIC equivalent is 2.7–2.8 s (first connection 2.73 s, reconnect attempts median 2.77 s).
- **Outliers.** One QUIC cycle (5) needed 2,745 ms for CONNECT→CONNACK, probably one lost packet and a PTO. One TCP cycle (10) needed 215 ms. All other CONNACKs were under 100 ms (QUIC) and 20 ms (TCP).
- **Lost messages** follow from detection: QUIC loses the messages sent during the 15–20 s before the stall is declared (3 per cycle). TCP loses at most one per cycle.

## 8 h QUIC long run (previous night, `LONG_RUN_RECONNECT_20261124/quic`, image fq3 with IPv6 start-up)

| item | value |
|---|---|
| duration | 8.00 h, normal network, no Clumsy |
| messages sent / echoed / missing | 5,746 / 5,746 / 0 |
| STALL lines, connection failures, reconnects | 0 / 0 / 0 |
| reboots, panics | 0 / 0 |
| app RTT ms | median 65.7, P95 105.9, min 24.6, max 408.7 (flat per hour) |
| RSSI dBm | median −31 (min −55, max −27) |
| free heap | −183 B/h (174,384 → 172,928 B), minimum free 142,684 B |

## Deviations and incidents (in order)
1. **`attempt1_precheck_bug/`: script bug.** PowerShell variable names are case-insensitive, so `$port` (UDP 14567) overwrote `$Port` (COM6). The pre-check then reported "14567 missing". Fixed by renaming to `$srvPort` in `reconnect_cycles.ps1` and `run_long.ps1`. Nothing was run on the board.
2. **`attempt2_ipv6_hang/`: IPv6 start-up hang.**
   - All pre-checks passed. The board (fq3) got IPv4 but never the IPv6 link-local event that `example_connect` waits for, and the test aborted after 150 s.
   - Earlier the same happened with ft3 on the second board (COM8, 24 Nov). Boots up to 15:46 UTC got IPv6 within 0.1–0.6 s; every boot from 16:19 UTC on did not.
   - On the laptop, the hotspot interface had its IPv6 link-local address and listed the board as a neighbour.
3. **Hotspot restart (operator-approved, once): `hotspot_restart.jsonl`.**
   - Off and on with the saved configuration (2.4 GHz, 192.168.137.1).
   - The first switch-on try was refused by the safety check in `enable_existing_hotspot.ps1`: the sharing profile was not reported as Ethernet while Windows was switching. The retry 5 min later succeeded, with the configuration preserved.
   - `boot_check_after_hotspot_restart/`: after the restart, still IPv4 only and no IPv6 within 60 s.
4. **IPv4-only images (operator-approved deviation).**
   - fq3v4 and ft3v4 are fq3/ft3 built with `CONFIG_EXAMPLE_CONNECT_IPV6=n` (`V4ONLY=1` in `build.py`). Nothing else differs; lwIP IPv6 is still compiled in.
   - **Both protocols therefore use the same start-up, and all traffic uses IPv4 to 192.168.137.1** (as before, since the servers were always reached over IPv4).
   - fq3v4: 1,643,168 B, sha256 `318e5141…13d0e`. ft3v4: 1,504,896 B, sha256 `cc8332a5…9114d`.
5. **`attempt3_flash_log_encoding/`: script bug.** The fq3v4 flash succeeded ("Hash of data verified" is in the log). The chain's check failed only because the log mixed UTF-8 and UTF-16 text. Fixed, and the chain was rerun, which flashed fq3v4 again. The valid results are the ones in `quic/` and `tcp_tls/`.
6. **No packet capture.** pktmon needs an elevation prompt that could not be answered unattended.

## Files
- `quic/`, `tcp_tls/`:
  - `serial_raw.log`: host-timestamped board log.
  - `cycles.jsonl`: host events (kill, restart, READY, reconnect seen).
  - `serverNN_stdout.log` and `serverNN_sensor.csv`: one per server instance.
  - `prechecks.json`, `hotspot_watch.jsonl`.
  - Analysis: `SUMMARY.md` and `cycles.csv`.
- `chain.log`, `flash_fq3v4_com6.log`, `flash_ft3v4_com6.log`: the unattended sequence.
- Wi-Fi SSID and password are masked in the committed files.
