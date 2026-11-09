# HOME_BOARD WIFI_PS_NONE — ICMP capture, effects disabled

HOME_BOARD, WIFI_PS_NONE verified at startup, Clumsy ICMP capture running, all effects disabled — operator-reported GUI settings.

Exact command: `ping.exe /n 30 /w 2000 192.168.137.212`

UTC start: 2026-11-03T23:14:29.360243+00:00; UTC finish: 2026-11-03T23:14:58.676267+00:00. Exit code: 0.

Requests: **30**; replies: **30**; timeouts: **0**; other failures: **0**.

Minimum **1 ms**, median **2 ms**, mean **2.6333 ms**, maximum **12 ms**.

No less-than observations. Statistics use the integer-resolution RTTs reported by Windows ping. Reply-only RTT statistics; failures are retained separately.

| Request | Host output receipt UTC | Status | Reported RTT ms |
|---:|---|---|---:|
| 1 | 2026-11-03T23:14:29.389901+00:00 | reply | 12 |
| 2 | 2026-11-03T23:14:30.390081+00:00 | reply | 1 |
| 3 | 2026-11-03T23:14:31.400936+00:00 | reply | 2 |
| 4 | 2026-11-03T23:14:32.407853+00:00 | reply | 1 |
| 5 | 2026-11-03T23:14:33.417209+00:00 | reply | 2 |
| 6 | 2026-11-03T23:14:34.418182+00:00 | reply | 2 |
| 7 | 2026-11-03T23:14:35.439319+00:00 | reply | 7 |
| 8 | 2026-11-03T23:14:36.443905+00:00 | reply | 2 |
| 9 | 2026-11-03T23:14:37.447346+00:00 | reply | 2 |
| 10 | 2026-11-03T23:14:38.459422+00:00 | reply | 2 |
| 11 | 2026-11-03T23:14:39.464390+00:00 | reply | 1 |
| 12 | 2026-11-03T23:14:40.469649+00:00 | reply | 2 |
| 13 | 2026-11-03T23:14:41.480759+00:00 | reply | 2 |
| 14 | 2026-11-03T23:14:42.486277+00:00 | reply | 3 |
| 15 | 2026-11-03T23:14:43.494146+00:00 | reply | 2 |
| 16 | 2026-11-03T23:14:44.501848+00:00 | reply | 2 |
| 17 | 2026-11-03T23:14:45.509103+00:00 | reply | 2 |
| 18 | 2026-11-03T23:14:46.517667+00:00 | reply | 2 |
| 19 | 2026-11-03T23:14:47.529864+00:00 | reply | 1 |
| 20 | 2026-11-03T23:14:48.545190+00:00 | reply | 2 |
| 21 | 2026-11-03T23:14:49.553076+00:00 | reply | 2 |
| 22 | 2026-11-03T23:14:50.561020+00:00 | reply | 3 |
| 23 | 2026-11-03T23:14:51.574186+00:00 | reply | 2 |
| 24 | 2026-11-03T23:14:52.587502+00:00 | reply | 2 |
| 25 | 2026-11-03T23:14:53.599314+00:00 | reply | 4 |
| 26 | 2026-11-03T23:14:54.612688+00:00 | reply | 5 |
| 27 | 2026-11-03T23:14:55.625327+00:00 | reply | 2 |
| 28 | 2026-11-03T23:14:56.643553+00:00 | reply | 3 |
| 29 | 2026-11-03T23:14:57.658267+00:00 | reply | 2 |
| 30 | 2026-11-03T23:14:58.673927+00:00 | reply | 2 |

[Complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.raw.txt), [per-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.requests.csv), [complete output with UTC receipt timestamps](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.output_timestamped.csv), [metadata and statistics](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.json). UTC receipt timestamps indicate when the host read each output line, not exact ICMP wire timestamps.

WIFI_PS_NONE was verified in the preceding controlled startup: [startup evidence](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json). No fresh mode readback or reset was performed. Clumsy capture/effects settings are operator-reported; no GUI inspection or changes were made in this run. No firmware, server, or monitor settings changed. This run remains separate from default-power-saving, previous Clumsy-stopped, and university-board results; no data were pooled or overwritten.
