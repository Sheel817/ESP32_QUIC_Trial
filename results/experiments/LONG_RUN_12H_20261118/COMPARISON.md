# TCP+TLS vs QUIC comparison (fixed profile, normal network, no Clumsy, 18-19 Nov 2026)

All numbers from the fixed profile (`profiles/fixed_20261118`), NOT the formal 18-run builds. Same board, laptop, hotspot and server code.

## 1. Connection-time test (50 attempts each, 0 failures; median ms, details in `../CONNECTION_TIME_20261118/`)
| metric | TCP+TLS 1.3 | QUIC |
|---|---|---|
| transport setup (TCP connect + TLS handshake / QUIC handshake_completed) | 1,524.3 | 2,628.6 |
| MQTT CONNECT to CONNACK | 14.4 | 47.0 |
| connect start to CONNACK | 1,555.2 | 2,817.2 |
| free heap after attempts | flat, about 290 KB | 223,632 B after 10 to 221,612 B after 50 (about -50 B per connect, not investigated) |

## 2. 12 h runs (normal sensor loop, publish every 5 s)
| item | TCP+TLS (image ft2) | QUIC (image fq2) |
|---|---|---|
| planned / reached healthy duration | 12 h / **10.0 h** (stall at uptime 36,054 s) | 12 h / **11.53 h** (stall at uptime 41,501 s) |
| capture length | 12 h (board idle after stall) | 12 h (board still publishing after stall) |
| messages sent (highest seq) / echoed | 7,195 / 7,195 | 8,621 / 8,282 |
| missing seq | none | 8283-8621 (339), all after the stall; all reached the server |
| RTT ms median / mean / P95 / min / max | 67.47 / 68.51 / 107.89 / 26.79 / 387.50 | 65.53 / 66.76 / 105.61 / 24.45 / 465.53 |
| crashes / reboots | 0 / 0 | 0 / 0 |
| what stopped | board stopped delivering to the server (server received nothing after seq 7195); server closed after 60 s; board stopped its task ("Restart board to reconnect") | board stopped receiving (partial MQTT packet, then keepalive timeout); publishing continued and reached the server; connection never closed |
| hotspot outages | none | none |
| connection setup at start (board log time stamps) | 1,540 ms | 2,780 ms |
| free heap first / last | 269,988 / 265,340 B (flat 270,012 B until the stall) | 175,712 / 174,228 B (flat for the last hours) |
| min free heap | 241,004 B | 144,048 B |

Remarks: (1) Neither 12 h run completed healthily; both stalled before 12 h, at different times and in different directions, so the stalls are not shown to be protocol-specific and not shown to be the same fault. Causes are not determined (see `tcp_tls/STALL_ANALYSIS.md`, `quic/STALL_ANALYSIS.md`). (2) The RTT values are dominated by the application's 20 ms polling sawtooth; the 2 ms median difference should not be read as a protocol result. (3) One run of each; no statistics across repeats.
