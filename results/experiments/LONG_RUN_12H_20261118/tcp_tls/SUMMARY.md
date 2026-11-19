# 12 h run summary: TCP+TLS 12 h (fixed image ft2)

Capture duration from reset release to capture close: 43200 s (12.00 h).
Boot markers seen (initial boot included): 1; sessions: 1; panic/fault markers: 0; disconnect markers: 252.

## Session 0 (start 2026-11-18T00:17:01.613114+00:00)

- messages sent (highest seq seen): 7195; echoed with APP_RTT: 7195; missing seq: 0
- missing sequence numbers: none
- RTT ms overall: n=7195 median=67.47 mean=68.51 P95=107.89 min=26.79 max=387.50

Server CSV rows: 7195; unique seq: 7195; highest seq: 7195.

## RTT per hour (ms, elapsed from reset release)

| hour | n | median | mean | P95 | min | max |
|---|---|---|---|---|---|---|
| 0-1 | 717 | 67.39 | 67.66 | 107.80 | 26.96 | 146.72 |
| 1-2 | 718 | 67.52 | 68.29 | 107.97 | 26.87 | 167.44 |
| 2-3 | 719 | 67.45 | 68.72 | 107.89 | 26.79 | 267.58 |
| 3-4 | 718 | 67.48 | 72.84 | 108.26 | 26.91 | 367.38 |
| 4-5 | 719 | 67.45 | 67.55 | 107.88 | 26.93 | 127.45 |
| 5-6 | 718 | 67.46 | 68.28 | 107.88 | 26.80 | 287.58 |
| 6-7 | 719 | 67.47 | 68.90 | 107.89 | 26.92 | 387.50 |
| 7-8 | 719 | 67.46 | 67.52 | 107.86 | 26.86 | 108.29 |
| 8-9 | 718 | 67.45 | 67.53 | 107.87 | 26.91 | 127.47 |
| 9-10 | 719 | 67.46 | 67.76 | 107.88 | 26.89 | 147.39 |
| 10-11 | 11 | 67.48 | 67.52 | 107.78 | 27.32 | 108.18 |

Overall (all sessions): sent 7195, echoed 7195.

## Connection setup at start (board uptime ms, first session)

`{"connecting": 4559, "established": 6099, "mqtt_connected": 7119}`
- transport setup (connecting -> connection established): 1540 ms (board log time stamps, 1 ms resolution)
- connecting -> MQTT connected (includes the fixed 1,000 ms application delay of the formal firmware): 2560 ms

## Free heap trend (HEAPLOG every 60 s)

- samples: 601; first free 269988 B, last free 265340 B, change -4648 B (-465 B/h)
- free min/max over run: 265340 / 270012 B; minimum-free-heap first/last/overall: 241004 / 241004 / 241004 B

## Crash / disconnect markers (first 20)

- 2026-11-18T10:18:30.753784+00:00 W (36089299) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:30.753929+00:00 W (36089399) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:30.962017+00:00 W (36089499) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:30.962168+00:00 W (36089599) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.169477+00:00 W (36089699) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.169608+00:00 W (36089799) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.375266+00:00 W (36089899) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.375372+00:00 W (36089999) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.375389+00:00 W (36090099) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.583083+00:00 W (36090199) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.583217+00:00 W (36090299) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.791250+00:00 W (36090399) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.791372+00:00 W (36090499) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.998910+00:00 W (36090599) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:31.999006+00:00 W (36090699) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:32.205555+00:00 W (36090799) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:32.205804+00:00 W (36090899) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:32.413916+00:00 W (36090999) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:32.414063+00:00 W (36091099) quic_demo_main: MQTT process returned: 10
- 2026-11-18T10:18:32.620783+00:00 W (36091199) quic_demo_main: MQTT process returned: 10
