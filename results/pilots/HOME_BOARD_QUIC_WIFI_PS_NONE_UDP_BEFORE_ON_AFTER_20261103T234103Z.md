# HOME_BOARD WIFI_PS_NONE QUIC — before/on/after UDP Lag pilot

All statistics were recomputed from the actual three 10-record CSVs and cross-checked against their saved raw intervals and corresponding byte ranges in the existing source log. No values were removed. The earlier files were read only and remain preserved.

Source live log for all stages: [HOME_BOARD_WIFI_PS_NONE_serial.log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Absolute source paths, file hashes, hashes of the live-log prefixes up to each captured end offset, boundaries and all errors/gaps are recorded in [evidence JSON](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_BEFORE_ON_AFTER_20261103T234103Z.json). A live growing file has no single fixed final hash; immutable intervals and exact prefixes are hashed instead.

| Stage | Sequences | Mean ms | Min ms | Max ms | Gaps | Connection/error/reboot lines |
|---|---|---:|---:|---:|---:|---:|
| Before | 273–282 | 66.2630 | 25.436 | 105.885 | 0 | 0 |
| Lag on | 351–360 | 187.7515 | 128.888 | 285.512 | 0 | 0 |
| After | 431–440 | 65.6854 | 25.383 | 108.267 | 0 | 0 |

Lag-on minus before: **+121.4885 ms**. After minus before: **-0.5776 ms**. After minus lag-on: **-122.0661 ms**.

This is a QUIC application RTT pilot, not an ICMP diagnostic. No ICMP, default-power-saving, or university-board results enter the comparison. Clumsy capture/effect settings are operator-reported and were not inspected or changed. The return condition is **UDP capture running, all effects off — operator-reported**. The new return run waited 60 seconds before marking its fresh boundary; only complete newly appended records after that boundary, with ESP uptime >60000 ms, were selected.

Sequence gaps are evaluated within each selected phase and from its own immediately preceding boundary sequence. Unmeasured time between phases is not called a sequence gap. Host timestamps have one-second resolution, converted from Europe/Helsinki UTC+02:00; precise boundary/collection UTC times are saved separately. APP_RTT includes application and transport scheduling as well as network delay. These sequential small samples do not establish a long-run latency distribution.

## Before

Label: HOME_BOARD, QUIC, WIFI_PS_NONE, Clumsy UDP 14567 capture running, all effects disabled — operator-reported GUI settings.

Immediate boundary after the capture-only request. Boundary **2026-11-03T23:28:58.8003037Z**, byte **40928**, after sequence 272. First/last source host receipt UTC: 2026-11-03T23:29:01+00:00 / 2026-11-03T23:29:47+00:00; reader completed 2026-11-03T23:29:47.154198+00:00.

| Sequence | Host receipt UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
| 273 | 2026-11-03T23:29:01+00:00 | 1376223 | 25.436 |
| 274 | 2026-11-03T23:29:06+00:00 | 1381253 | 45.595 |
| 275 | 2026-11-03T23:29:11+00:00 | 1386283 | 65.492 |
| 276 | 2026-11-03T23:29:16+00:00 | 1391313 | 85.489 |
| 277 | 2026-11-03T23:29:21+00:00 | 1396343 | 105.132 |
| 278 | 2026-11-03T23:29:26+00:00 | 1401273 | 28.834 |
| 279 | 2026-11-03T23:29:31+00:00 | 1406303 | 48.908 |
| 280 | 2026-11-03T23:29:36+00:00 | 1411333 | 65.847 |
| 281 | 2026-11-03T23:29:42+00:00 | 1416363 | 86.012 |
| 282 | 2026-11-03T23:29:47+00:00 | 1421393 | 105.885 |

Mean 66.2630 ms; min 25.436; max 105.885. Gaps including boundary transition: 0; connection-error/reboot/APP_RTT anomaly lines: 0; all warning/error lines: 0.

[Actual source CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.csv), SHA-256 `323d257b39d36fd986c5372bb9e2290abf8d7c8f71c214b73ad098b47cbc215d`. [Raw interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.raw.log), SHA-256 `d26c31e1b8d438c3e53940b52ea57a1d493df446bc005a71aac7ceae47b85e3e`. [Boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.boundary.json), [capture metadata/errors](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.json).

## Lag on

Label: QUIC, HOME_BOARD, WIFI_PS_NONE, UDP 14567 capture, Lag 100 ms outbound only; other effects off — operator-reported settings.

Wait started 2026-11-03T23:34:32.441871+00:00; requested wait 60 seconds. Boundary **2026-11-03T23:35:32.443135+00:00**, byte **47435**, after sequence 350. First/last source host receipt UTC: 2026-11-03T23:35:32+00:00 / 2026-11-03T23:36:17+00:00; reader completed 2026-11-03T23:36:17.931688+00:00.

| Sequence | Host receipt UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
| 351 | 2026-11-03T23:35:32+00:00 | 1767083 | 128.888 |
| 352 | 2026-11-03T23:35:37+00:00 | 1772213 | 245.425 |
| 353 | 2026-11-03T23:35:42+00:00 | 1777143 | 165.964 |
| 354 | 2026-11-03T23:35:47+00:00 | 1782173 | 185.927 |
| 355 | 2026-11-03T23:35:52+00:00 | 1787203 | 205.387 |
| 356 | 2026-11-03T23:35:57+00:00 | 1792133 | 130.189 |
| 357 | 2026-11-03T23:36:02+00:00 | 1797163 | 152.097 |
| 358 | 2026-11-03T23:36:07+00:00 | 1802193 | 168.809 |
| 359 | 2026-11-03T23:36:12+00:00 | 1807323 | 285.512 |
| 360 | 2026-11-03T23:36:17+00:00 | 1812253 | 209.317 |

Mean 187.7515 ms; min 128.888; max 285.512. Gaps including boundary transition: 0; connection-error/reboot/APP_RTT anomaly lines: 0; all warning/error lines: 0.

[Actual source CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.csv), SHA-256 `f1f0f9680f4f13d5fb6bd3483fea29a14a358dd800e84c2afe7660cd84d09f8c`. [Raw interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.raw.log), SHA-256 `b8108a327dfe6ec34187be19d20b8fc2198e7e489317007f0aa8c58024ff656c`. [Boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.boundary.json), [capture metadata/errors](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.json).

## After

Label: QUIC, HOME_BOARD, WIFI_PS_NONE, UDP capture running, all effects off — operator-reported.

Wait started 2026-11-03T23:41:12.728064+00:00; requested wait 60 seconds. Boundary **2026-11-03T23:42:12.729391+00:00**, byte **54141**, after sequence 430. First/last source host receipt UTC: 2026-11-03T23:42:13+00:00 / 2026-11-03T23:42:58+00:00; reader completed 2026-11-03T23:42:58.742926+00:00.

| Sequence | Host receipt UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
| 431 | 2026-11-03T23:42:13+00:00 | 2167783 | 25.529 |
| 432 | 2026-11-03T23:42:18+00:00 | 2172813 | 45.480 |
| 433 | 2026-11-03T23:42:23+00:00 | 2177843 | 65.474 |
| 434 | 2026-11-03T23:42:28+00:00 | 2182873 | 85.385 |
| 435 | 2026-11-03T23:42:33+00:00 | 2187903 | 108.267 |
| 436 | 2026-11-03T23:42:38+00:00 | 2192833 | 25.383 |
| 437 | 2026-11-03T23:42:43+00:00 | 2197863 | 45.274 |
| 438 | 2026-11-03T23:42:48+00:00 | 2202893 | 65.355 |
| 439 | 2026-11-03T23:42:53+00:00 | 2207923 | 85.361 |
| 440 | 2026-11-03T23:42:58+00:00 | 2212953 | 105.346 |

Mean 65.6854 ms; min 25.383; max 108.267. Gaps including boundary transition: 0; connection-error/reboot/APP_RTT anomaly lines: 0; all warning/error lines: 0.

[Actual source CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.csv), SHA-256 `0c33024e8d14655b3715479101281107532a5bb898865239e3dff4811e832459`. [Raw interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.raw.log), SHA-256 `9d13a39e48aeac0da8e926373b6e879b0cf3283de2558473c77841a8728492ae`. [Boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.boundary.json), [capture metadata/errors](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.json).

## Derived outputs and final state

[All 30 measurements with source paths, boundaries and UTC metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_BEFORE_ON_AFTER_20261103T234103Z.all_measurements.csv), [recomputed statistics CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_BEFORE_ON_AFTER_20261103T234103Z.statistics.csv), [full evidence and hashes](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_BEFORE_ON_AFTER_20261103T234103Z.json). No pings, port opens, resets, builds, flashes, or firmware/filter/server/monitor/Clumsy settings changes were performed. Existing monitor and server were left untouched.
