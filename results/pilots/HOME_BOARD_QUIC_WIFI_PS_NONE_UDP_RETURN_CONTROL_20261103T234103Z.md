# HOME_BOARD QUIC WIFI_PS_NONE — UDP return-to-control APP_RTT

QUIC, HOME_BOARD, WIFI_PS_NONE, UDP capture running, all effects off — operator-reported.

Source: [existing monitor log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Fresh boundary after the request: **2026-11-03T23:42:12.729391+00:00**, byte offset **54141**, immediately following prior APP_RTT sequence **430**. Boundary partial line: False. Only complete records appended after this boundary were eligible. All 10 have ESP uptime >60000 ms, retained in arrival order without trimming.

UTC collection boundary/start: 2026-11-03T23:42:12.729391+00:00; reader started: 2026-11-03T23:42:12.741436+00:00; completed: **2026-11-03T23:42:58.742926+00:00**. Source host timestamps are Europe/Helsinki UTC+02:00 at second resolution; CSV records their UTC equivalents. They are log receipt timestamps, not wire timestamps.

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

Mean **65.6854 ms**, minimum **25.383 ms**, maximum **108.267 ms**.

Sequence gaps, including the boundary transition: **0**. Connection-error/reboot/APP_RTT anomaly lines: **0**. All warning/error log lines in the captured interval: **0**. These observations cover the saved interval through the tenth qualifying APP_RTT, not the entire historical log or unlogged network events.

[Timestamped CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.csv), [raw appended interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.raw.log), [boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.boundary.json), [statistics, gap/error evidence and hashes](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_RETURN_CONTROL_20261103T234103Z.json). The original live log is not copied over or modified. No pings, port opens, resets, builds, flashes or settings changes were performed; existing monitor and server remain untouched.
