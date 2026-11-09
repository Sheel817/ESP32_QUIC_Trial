# University board ICMP before/on/after diagnostic

Descriptive results from the three actual CSVs. All request outcomes and reported RTT values are retained. Settings are operator-reported; no Clumsy settings were inspected or changed during collection. This is ICMP, not QUIC. These data do not establish calibrated 100 ms delay.

Before: Clumsy capturing, all effects disabled. At that earlier collection the reported filter was UDP-only. On: reported filter changed to `icmp and (ip.SrcAddr == 192.168.137.11 or ip.DstAddr == 192.168.137.11)`, capture running, Lag 100 ms outbound only, other effects off. After: same ICMP filter as On, capture running, Lag OFF and other effects disabled. Thus the Before and After capture filters are not identical, although neither control intentionally enables Lag.

Statistics describe received replies; timeouts/errors are retained separately. Values reported as <1 ms are preserved and would be represented by bounds, not assigned exact RTTs.

| Phase | Requests | Replies | Timeouts | Errors | Min ms | Median ms | Mean ms | Max ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Before | 30 | 30 | 0 | 0 | 20.0 | 200.0 | 228.56666666666666 | 474.0 |
| Lag on | 30 | 30 | 0 | 0 | 133.0 | 196.0 | 198.86666666666667 | 348.0 |
| After | 30 | 30 | 0 | 0 | 16.0 | 211.0 | 230.5 | 515.0 |

On minus Before mean: -29.7000 ms; median: -4.0000 ms.
After minus Before mean: +1.9333 ms; median: +11.0000 ms.
After minus On mean: +31.6333 ms; median: +15.0000 ms.

## Before

Source: [UNIVERSITY_BOARD_ICMP_capture_only_control_20261103T160216719237Z.csv](./UNIVERSITY_BOARD_ICMP_capture_only_control_20261103T160216719237Z.csv). UTC start 2026-11-03T16:02:16.719276+00:00; UTC end 2026-11-03T16:02:45.988958+00:00.

| Request | Status | Reported RTT ms |
|---:|---|---:|
| 1 | reply | 187 |
| 2 | reply | 86 |
| 3 | reply | 100 |
| 4 | reply | 213 |
| 5 | reply | 429 |
| 6 | reply | 349 |
| 7 | reply | 268 |
| 8 | reply | 77 |
| 9 | reply | 403 |
| 10 | reply | 423 |
| 11 | reply | 241 |
| 12 | reply | 54 |
| 13 | reply | 68 |
| 14 | reply | 325 |
| 15 | reply | 310 |
| 16 | reply | 113 |
| 17 | reply | 20 |
| 18 | reply | 178 |
| 19 | reply | 458 |
| 20 | reply | 474 |
| 21 | reply | 290 |
| 22 | reply | 100 |
| 23 | reply | 150 |
| 24 | reply | 236 |
| 25 | reply | 461 |
| 26 | reply | 473 |
| 27 | reply | 186 |
| 28 | reply | 130 |
| 29 | reply | 21 |
| 30 | reply | 34 |

## Lag on

Source: [UNIVERSITY_BOARD_ICMP_lag100_outbound_20261103T160827472092Z.csv](./UNIVERSITY_BOARD_ICMP_lag100_outbound_20261103T160827472092Z.csv). UTC start 2026-11-03T16:08:37.472497+00:00; UTC end 2026-11-03T16:09:06.917056+00:00.

| Request | Status | Reported RTT ms |
|---:|---|---:|
| 1 | reply | 136 |
| 2 | reply | 245 |
| 3 | reply | 164 |
| 4 | reply | 185 |
| 5 | reply | 197 |
| 6 | reply | 206 |
| 7 | reply | 219 |
| 8 | reply | 133 |
| 9 | reply | 156 |
| 10 | reply | 271 |
| 11 | reply | 184 |
| 12 | reply | 205 |
| 13 | reply | 219 |
| 14 | reply | 233 |
| 15 | reply | 348 |
| 16 | reply | 155 |
| 17 | reply | 176 |
| 18 | reply | 193 |
| 19 | reply | 204 |
| 20 | reply | 221 |
| 21 | reply | 246 |
| 22 | reply | 160 |
| 23 | reply | 164 |
| 24 | reply | 195 |
| 25 | reply | 202 |
| 26 | reply | 214 |
| 27 | reply | 236 |
| 28 | reply | 139 |
| 29 | reply | 175 |
| 30 | reply | 185 |

## After

Source: [UNIVERSITY_BOARD_ICMP_return_to_control_20261103T161550240895Z.csv](./UNIVERSITY_BOARD_ICMP_return_to_control_20261103T161550240895Z.csv). UTC start 2026-11-03T16:16:00.241309+00:00; UTC end 2026-11-03T16:16:29.690809+00:00.

| Request | Status | Reported RTT ms |
|---:|---|---:|
| 1 | reply | 37 |
| 2 | reply | 61 |
| 3 | reply | 74 |
| 4 | reply | 400 |
| 5 | reply | 113 |
| 6 | reply | 318 |
| 7 | reply | 438 |
| 8 | reply | 41 |
| 9 | reply | 161 |
| 10 | reply | 170 |
| 11 | reply | 360 |
| 12 | reply | 406 |
| 13 | reply | 415 |
| 14 | reply | 16 |
| 15 | reply | 69 |
| 16 | reply | 314 |
| 17 | reply | 170 |
| 18 | reply | 294 |
| 19 | reply | 515 |
| 20 | reply | 327 |
| 21 | reply | 293 |
| 22 | reply | 60 |
| 23 | reply | 290 |
| 24 | reply | 105 |
| 25 | reply | 229 |
| 26 | reply | 239 |
| 27 | reply | 159 |
| 28 | reply | 472 |
| 29 | reply | 176 |
| 30 | reply | 193 |

No outlier filtering or result removal. Small sequential samples with varying wireless latency, unverified per-packet impairment and differing initial control filter do not isolate a calibrated delay effect. No reset, build, flash, firmware edit or Clumsy/server/monitor setting change was performed.
