# HOME_BOARD QUIC WIFI_PS_NONE — UDP capture-only APP_RTT

HOME_BOARD, QUIC, WIFI_PS_NONE, Clumsy UDP 14567 capture running, all effects disabled — operator-reported GUI settings.

Source: [existing monitor log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Fresh boundary after the request: **2026-11-03T23:28:58.8003037Z**, byte offset **40928**, immediately following prior APP_RTT sequence **272**. Boundary partial line: False. Only complete records appended after this boundary were eligible. All 10 have ESP uptime >60000 ms, retained in arrival order without trimming.

UTC collection boundary/start: 2026-11-03T23:28:58.8003037Z; reader started: 2026-11-03T23:29:45.129582+00:00; completed: **2026-11-03T23:29:47.154198+00:00**. Source host timestamps are Europe/Helsinki UTC+02:00 at second resolution; CSV records their UTC equivalents. They are log receipt timestamps, not wire timestamps.

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

Mean **66.2630 ms**, minimum **25.436 ms**, maximum **105.885 ms**.

Sequence gaps, including the boundary transition: **0**. Connection-error/reboot/APP_RTT anomaly lines: **0**. All warning/error log lines in the captured interval: **0**. These observations cover the saved interval through the tenth qualifying APP_RTT, not the entire historical log or unlogged network events.

[Timestamped CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.csv), [raw appended interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.raw.log), [boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.boundary.json), [statistics, gap/error evidence and hashes](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.json). The original live log is not copied over or modified. No pings, port opens, resets, builds, flashes or settings changes were performed; existing monitor and server remain untouched.
