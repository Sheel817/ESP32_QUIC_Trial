# Long run with reconnect: QUIC, image fq3, 8 h, normal network

Capture duration from reset release to capture close: 28800 s (8.00 h).
Boots seen: 1 (1 = no reboot); panic/fault markers: 0.

## Messages

- sent (highest seq seen in serial log, server CSV or APP_RTT_LOST): 5746
- echoed with APP_RTT: 5746; missing: 0
- missing seq that reached the server (echo lost on the way back or session closed first): 0 (none)
- missing seq not in the server CSV (never arrived): 0 (none)
- server CSV rows in capture window: 5746; unique seq: 5746
- RTT ms overall: n=5746 median=65.65 mean=69.17 P95=105.91 min=24.58 max=408.71

## Connection failures, stalls and reconnects

- first connection: {'kind': 'CONNECT', 'utc': '2026-11-24T15:46:11.261668+00:00', 'elapsed_s': 8.704, 'session': 0, 'initial': 1, 'transport_ms': 2824.5, 'connack_ms': 65.9}
- connection failures (CONNECTION_FAILED): 0; reasons: {}
- STALL lines (no echo for 15 s): 0
- reconnects completed: 0; failed attempts: 0; attempts per reconnect: []
- reconnect handshake ms (transport setup): n=0
- reconnect MQTT CONNECT->CONNACK ms: n=0
- reconnect attempt total ms (attempt start -> subscribed): n=0
- downtime ms (failure detected -> connected again, includes 1 s backoff): n=0

| # | failure UTC | reason | fail uptime ms | reconnect start uptime ms | connected uptime ms | handshake ms | CONNACK ms | attempts | downtime ms |
|---|---|---|---|---|---|---|---|---|---|

### State at each stall / failure (STALL and FAIL_DIAG lines, first 30)


## Wi-Fi

- RSSI dBm from DIAG (every 60 s): n=479 median=-31 mean=-33 P95=-29 min=-55 max=-27
- Wi-Fi events: 1 ({'start': 1}); WIFI_KICK: 0

## Transport-level diagnostics

- APP_RX_DROP (QUIC receive buffer full, data discarded): 0
- QUIC_TIMEOUT (ngtcp2 expiry error): 0
- DIAG in_flight: max 0, samples > 0: 0 of 479
- DIAG pto_count: max 0, samples > 0: 0 of 479
- DIAG lost_pending: max 0, samples > 0: 0 of 479
- DIAG tx_loss_count: max 0, samples > 0: 0 of 479
- DIAG app_buf_len: max 127, samples > 0: 6 of 479

## RTT per hour (ms, elapsed from reset release)

| hour | n | median | mean | P95 | min | max |
|---|---|---|---|---|---|---|
| 0-1 | 716 | 65.58 | 70.06 | 106.19 | 24.64 | 405.56 |
| 1-2 | 719 | 65.86 | 69.34 | 106.07 | 24.80 | 264.56 |
| 2-3 | 719 | 65.67 | 68.40 | 106.00 | 24.81 | 309.23 |
| 3-4 | 718 | 65.51 | 68.11 | 105.84 | 24.69 | 280.73 |
| 4-5 | 719 | 65.70 | 69.37 | 105.89 | 24.61 | 408.71 |
| 5-6 | 718 | 65.69 | 69.66 | 105.90 | 24.58 | 385.51 |
| 6-7 | 719 | 65.54 | 69.51 | 105.90 | 24.65 | 385.44 |
| 7-8 | 718 | 65.50 | 68.92 | 105.81 | 25.01 | 345.29 |

## Free heap trend (HEAPLOG every 60 s)

- samples: 479; first free 174384 B, last free 172928 B, change -1456 B (-183 B/h)
- free min/max over run: 172804 / 174384 B; minimum-free-heap first/last/overall: 142684 / 142684 / 142684 B
- free heap after each reconnect (RECONNECT free=): []

## Panic / fault markers

- none
