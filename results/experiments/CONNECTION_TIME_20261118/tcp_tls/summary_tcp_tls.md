# Connection-time summary: TCP+TLS 1.3 (fixed profile, ctt)

Attempts logged: 50; OK: 50; failed: 0.
Board final line: `proto=TCP_TLS attempts=50 ok=50 failed=0 free=290864 min_free=240580`

Times in milliseconds (board esp_timer_get_time, microsecond resolution), successful attempts only. P95 = linear interpolation.

## All successful attempts

| metric | n | median | mean | min | max | P95 |
|---|---|---|---|---|---|---|
| tcp_connect | 50 | 5.143 | 6.067 | 3.794 | 19.352 | 10.799 |
| tls_handshake | 50 | 1519.455 | 1518.431 | 1509.164 | 1529.859 | 1523.328 |
| tcp_tls_total | 50 | 1524.348 | 1524.499 | 1513.118 | 1540.431 | 1533.925 |
| mqtt_connect_to_connack | 50 | 14.386 | 22.450 | 8.600 | 215.609 | 38.590 |
| connack_from_start | 50 | 1555.243 | 1562.190 | 1538.179 | 1756.779 | 1575.352 |

## Excluding attempt 1 (first-connection effects)

| metric | n | median | mean | min | max | P95 |
|---|---|---|---|---|---|---|
| tcp_connect | 49 | 5.090 | 5.975 | 3.794 | 19.352 | 10.804 |
| tls_handshake | 49 | 1519.351 | 1518.198 | 1509.164 | 1528.564 | 1522.958 |
| tcp_tls_total | 49 | 1524.314 | 1524.173 | 1513.118 | 1539.409 | 1533.539 |
| mqtt_connect_to_connack | 49 | 14.179 | 18.796 | 8.600 | 215.609 | 30.842 |
| connack_from_start | 49 | 1552.314 | 1558.219 | 1538.179 | 1753.559 | 1572.065 |

## Heap (every 10 attempts)

| after attempt | free bytes | min free bytes |
|---|---|---|
| 10 | 290280 | 240812 |
| 20 | 290280 | 240808 |
| 30 | 290088 | 240580 |
| 40 | 290300 | 240580 |
| 50 | 290516 | 240580 |
