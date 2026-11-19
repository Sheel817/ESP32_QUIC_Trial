# QUIC 12 h run, 18-19 Nov 2026 (fixed profile, normal network, no Clumsy)

**Profile:** `profiles/fixed_20261118` (ngtcp2 alignment fix, UDP socket close, event-loop init once). NOT the formal 18-run build.
**Image:** `fq2` = fixed QUIC image + free-heap/min-free-heap log line every 60 s, 1,637,616 bytes,
sha256 `7f16605b7a20c92dd9f15e30c1e21957783d9207c5fd85ab252948db852cacc7`. Normal sensor loop (DHT11 publish every 5 s), `QUIET_MEASUREMENT=1`,
`WIFI_PS_NONE`, partition 1,700K, no heap poisoning. **Network:** Windows Mobile Hotspot 2.4 GHz, 192.168.137.1, **Clumsy not running**.
Server: `quic_server.py` UDP 14567 on the laptop (logs `server_stdout.log`, `server_stderr.log`; CSV `server_sensor.csv`).

Capture 43,200 s from reset release: 12:20:10Z (18 Nov) to 00:20:10Z (19 Nov). One host reset at the start, no restart afterwards. The board kept running after the capture closed until the server was stopped at about 00:21Z (server CSV `server_sensor.csv` therefore has rows after the capture end; `server_sensor_capture_window.csv` is cut at the capture end and is the one used for the summary).

## Pre-checks (before start, `prechecks.json`, 12:18Z)
Hotspot On with 192.168.137.1; Clumsy/WinDivert processes 0; QUIC server listening on UDP 14567; COM6 present, no serial monitor running; flash verified (3/3 regions hash-verified, image hash matches the build);
board connected and the first 10 RTTs arrived (seq 1-10); laptop on AC (battery 100 %); sleep/hibernate on AC already "never", so no power setting was changed and nothing needs restoring; 646 GB free disk.

## Result in one paragraph
**The board did not receive echoes after 11.53 h.** The run was normal until seq 8282 (echo at 23:51:52Z, board uptime 41,501 s). The server received seq 8283 at 23:51:56.795Z and sent its echo. At 23:51:56.963Z the board
started to log `MQTT process returned: 11` (need more bytes: part of an incoming MQTT packet had arrived, the rest never was processed) about 300 times (30 s). From 23:52:27Z it logged `returned: 10` (keepalive timeout: no ping response)
until the end (16,541 lines), and `APP_RTT storage full; dropping pending` for seq 8283-8605. **The board kept running and kept publishing**: the server received every message up to the capture end (seq 8,621) and echoed each one, the heap line kept printing (free 174,228 B), no panic, no reboot, no QUIC close or cleanup message. So the direction board-to-server kept working and the direction server-to-board stopped. As instructed, the board was not restarted. **Cause not determined** (see `STALL_ANALYSIS.md`).

| item | value |
|---|---|
| messages sent in capture window (server CSV, highest seq) / echoed with APP_RTT | 8,621 / 8,282 |
| missing echoes | 339 (seq 8283-8621, all after the stall; every one of them reached the server) |
| RTT ms overall (n=8,282) | median 65.53, mean 66.76, P95 105.61, min 24.45, max 465.53 |
| crashes / reboots | 0 / 0 (single boot) |
| disconnects | no QUIC close or cleanup; receive direction stalled at 11.53 h (the 16,840 "disconnect markers" in `SUMMARY.md` are the repeated `MQTT process returned: 10/11` warning lines, not separate disconnects) |
| hotspot outages | none (watcher active the whole run, only WATCH_START logged) |
| connection setup at start | QUIC established in 2,780 ms (board log time stamps: connecting at 4,585 ms, established at 7,365 ms); MQTT connected at 8,465 ms (includes the formal firmware's 1,000 ms delay) |
| free heap | first 175,712 B, last 174,228 B, change -1,484 B; min free 144,048 B constant; flat 174,228 B for the last hours |

RTT per hour: see `SUMMARY.md` (medians 65.5 ms each hour; outliers up to 465 ms).

## Notes
- Hours are counted from reset release; hour 11-12 has 380 echoes because the echoes stopped at 11.53 h.
- Raw log `serial_raw.log` has the Wi-Fi SSID masked; the original unmasked copy is in a git-ignored local backup.
- The hotspot watcher and the QUIC server were stopped by me after the capture ended (00:21Z). The board itself was left powered and running.
- `SHA256SUMS.txt` lists checksums of all files in this folder.
