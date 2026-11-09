# HOME_BOARD QUIC WIFI_PS_NONE — UDP outbound Lag 100 ms APP_RTT

QUIC, HOME_BOARD, WIFI_PS_NONE, UDP 14567 capture, Lag 100 ms outbound only; other effects off — operator-reported settings.

Source: [existing monitor log](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/HOME_BOARD_WIFI_PS_NONE_serial.log). Fresh boundary after the request: **2026-11-03T23:35:32.443135+00:00**, byte offset **47435**, immediately following prior APP_RTT sequence **350**. Boundary partial line: False. Only complete records appended after this boundary were eligible. All 10 have ESP uptime >60000 ms, retained in arrival order without trimming.

UTC collection boundary/start: 2026-11-03T23:35:32.443135+00:00; reader started: 2026-11-03T23:35:32.454749+00:00; completed: **2026-11-03T23:36:17.931688+00:00**. Source host timestamps are Europe/Helsinki UTC+02:00 at second resolution; CSV records their UTC equivalents. They are log receipt timestamps, not wire timestamps.

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

Mean **187.7515 ms**, minimum **128.888 ms**, maximum **285.512 ms**.

Sequence gaps, including the boundary transition: **0**. Connection-error/reboot/APP_RTT anomaly lines: **0**. All warning/error log lines in the captured interval: **0**. These observations cover the saved interval through the tenth qualifying APP_RTT, not the entire historical log or unlogged network events.

[Timestamped CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.csv), [raw appended interval](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.raw.log), [boundary metadata](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.boundary.json), [statistics, gap/error evidence and hashes](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.json). The original live log is not copied over or modified. No pings, port opens, resets, builds, flashes or settings changes were performed; existing monitor and server remain untouched.


## Matching capture-only comparison

Wait began **2026-11-03T23:34:32.441871+00:00**; a 60-second wait completed before marking the boundary above.

Reference: [actual capture-only CSV](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_CAPTURE_20261103T232858Z.csv), sequences **273–282**, recomputed mean **66.2630 ms**. Current Lag pilot mean **187.7515 ms**, change **+121.4885 ms**. Every selected RTT was retained, including high/low values. No ICMP, default-power-saving, or university-board data are included. GUI settings remain operator-reported.

[Comparison metadata and reference hash](./HOME_BOARD_QUIC_WIFI_PS_NONE_UDP_LAG100_OUTBOUND_20261103T233432Z.comparison.json).
