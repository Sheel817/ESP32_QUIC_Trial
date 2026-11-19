# Connection-time summary: QUIC (fixed profile, ctq)

Attempts logged: 50; OK: 50; failed: 0.
Board final line: `proto=QUIC attempts=50 ok=50 failed=0 free=222176 min_free=142088`

Times in milliseconds (board esp_timer_get_time, microsecond resolution), successful attempts only. P95 = linear interpolation.

## All successful attempts

| metric | n | median | mean | min | max | P95 |
|---|---|---|---|---|---|---|
| quic_init | 50 | 18.622 | 18.484 | 17.841 | 22.529 | 18.637 |
| quic_handshake_cb | 50 | 2628.595 | 2627.703 | 2420.651 | 2677.458 | 2668.683 |
| quic_ready_seen | 50 | 2772.642 | 2752.574 | 2529.116 | 2801.735 | 2795.441 |
| mqtt_connect_to_connack | 50 | 47.010 | 49.724 | 19.666 | 116.498 | 82.019 |
| connack_from_start | 50 | 2817.242 | 2802.851 | 2572.877 | 2874.303 | 2849.160 |

## Excluding attempt 1 (first-connection effects)

| metric | n | median | mean | min | max | P95 |
|---|---|---|---|---|---|---|
| quic_init | 49 | 18.622 | 18.401 | 17.841 | 18.888 | 18.632 |
| quic_handshake_cb | 49 | 2628.321 | 2626.834 | 2420.651 | 2677.458 | 2662.018 |
| quic_ready_seen | 49 | 2770.811 | 2752.127 | 2529.116 | 2801.735 | 2795.451 |
| mqtt_connect_to_connack | 49 | 46.969 | 49.778 | 19.666 | 116.498 | 82.331 |
| connack_from_start | 49 | 2817.196 | 2802.462 | 2572.877 | 2874.303 | 2849.306 |

## Heap (every 10 attempts)

| after attempt | free bytes | min free bytes |
|---|---|---|
| 10 | 223632 | 143512 |
| 20 | 223268 | 143188 |
| 30 | 222920 | 142772 |
| 40 | 222532 | 142424 |
| 50 | 221612 | 142088 |
