# Connection-time comparison (fixed profile, normal network, Clumsy off, 50 attempts each, all OK)

Milliseconds; all 50 attempts / excluding attempt 1 shown as median (mean) [P95].

| metric | TCP+TLS 1.3 | QUIC |
|---|---|---|
| Transport setup: TCP connect + TLS handshake (TCP+TLS) / QUIC handshake_completed (QUIC) | 1524.3 (1524.5) [1533.9] / 1524.3 (1524.2) [1533.5] | 2628.6 (2627.7) [2668.7] / 2628.3 (2626.8) [2662.0] |
| MQTT CONNECT to CONNACK | 14.4 (22.5) [38.6] / 14.2 (18.8) [30.8] | 47.0 (49.7) [82.0] / 47.0 (49.8) [82.3] |
| Connect start to CONNACK (total) | 1555.2 (1562.2) [1575.4] / 1552.3 (1558.2) [1572.1] | 2817.2 (2802.9) [2849.2] / 2817.2 (2802.5) [2849.3] |
| (TCP only) TCP connect | 5.1 (6.1) [10.8] | - |
| (TCP only) TLS handshake | 1519.5 (1518.4) [1523.3] | - |
| (QUIC only) init: socket + SSL + conn | - | 18.6 (18.5) [18.6] |
| (QUIC only) ready seen by 100 ms polling | - | 2772.6 (2752.6) [2795.4] |

Failures: 0 of 50 for each protocol. Per-protocol tables: `tcp_tls/summary_tcp_tls.md`, `quic/summary_quic.md`.
