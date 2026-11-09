# HOME_BOARD WIFI_PS_NONE — ICMP diagnostic — return-to-control, capture running, all effects off

HOME_BOARD, WIFI_PS_NONE, ICMP capture running, all effects off, return-to-control.

Exact command: `ping.exe /n 30 /w 2000 192.168.137.212`

UTC start: 2026-11-03T23:22:39.364733+00:00; UTC finish: 2026-11-03T23:23:08.630787+00:00. Exit code: 0.

Requests: **30**; replies: **30**; timeouts: **0**; other failures: **0**.

Minimum **1 ms**, median **2 ms**, mean **3.1333 ms**, maximum **13 ms**.

No less-than observations. Statistics use the integer-resolution RTTs reported by Windows ping. Reply-only RTT statistics; failures are retained separately.

| Request | Host output receipt UTC | Status | Reported RTT ms |
|---:|---|---|---:|
| 1 | 2026-11-03T23:22:39.386394+00:00 | reply | 2 |
| 2 | 2026-11-03T23:22:40.388058+00:00 | reply | 1 |
| 3 | 2026-11-03T23:22:41.400226+00:00 | reply | 2 |
| 4 | 2026-11-03T23:22:42.401368+00:00 | reply | 2 |
| 5 | 2026-11-03T23:22:43.419503+00:00 | reply | 6 |
| 6 | 2026-11-03T23:22:44.417520+00:00 | reply | 2 |
| 7 | 2026-11-03T23:22:45.429676+00:00 | reply | 1 |
| 8 | 2026-11-03T23:22:46.437631+00:00 | reply | 2 |
| 9 | 2026-11-03T23:22:47.449368+00:00 | reply | 2 |
| 10 | 2026-11-03T23:22:48.456277+00:00 | reply | 2 |
| 11 | 2026-11-03T23:22:49.468658+00:00 | reply | 2 |
| 12 | 2026-11-03T23:22:50.475354+00:00 | reply | 3 |
| 13 | 2026-11-03T23:22:51.475594+00:00 | reply | 2 |
| 14 | 2026-11-03T23:22:52.499744+00:00 | reply | 13 |
| 15 | 2026-11-03T23:22:53.505464+00:00 | reply | 2 |
| 16 | 2026-11-03T23:22:54.510219+00:00 | reply | 2 |
| 17 | 2026-11-03T23:22:55.524621+00:00 | reply | 8 |
| 18 | 2026-11-03T23:22:56.532396+00:00 | reply | 13 |
| 19 | 2026-11-03T23:22:57.539832+00:00 | reply | 6 |
| 20 | 2026-11-03T23:22:58.538271+00:00 | reply | 3 |
| 21 | 2026-11-03T23:22:59.552291+00:00 | reply | 2 |
| 22 | 2026-11-03T23:23:00.567604+00:00 | reply | 1 |
| 23 | 2026-11-03T23:23:01.569504+00:00 | reply | 2 |
| 24 | 2026-11-03T23:23:02.570085+00:00 | reply | 1 |
| 25 | 2026-11-03T23:23:03.585937+00:00 | reply | 1 |
| 26 | 2026-11-03T23:23:04.598848+00:00 | reply | 2 |
| 27 | 2026-11-03T23:23:05.606030+00:00 | reply | 3 |
| 28 | 2026-11-03T23:23:06.608613+00:00 | reply | 2 |
| 29 | 2026-11-03T23:23:07.616892+00:00 | reply | 3 |
| 30 | 2026-11-03T23:23:08.628534+00:00 | reply | 1 |

[Complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.raw.txt), [per-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.requests.csv), [complete output with UTC receipt timestamps](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.output_timestamped.csv), [metadata and statistics](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.json). UTC receipt timestamps indicate when the host read each output line, not exact ICMP wire timestamps.

WIFI_PS_NONE was verified in the preceding controlled startup: [startup evidence](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json). No fresh mode readback or reset was performed. Clumsy capture/effects settings are operator-reported; no GUI inspection or changes were made in this run. No firmware, server, or monitor settings changed. This run remains separate from default-power-saving, previous Clumsy-stopped, and university-board results; no data were pooled or overwritten.
