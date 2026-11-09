# HOME_BOARD WIFI_PS_NONE — ICMP capture, Lag 100 ms outbound only

HOME_BOARD, WIFI_PS_NONE, Clumsy ICMP capture running, Lag 100 ms outbound only; other effects off — operator-reported settings.

Exact command: `ping.exe /n 30 /w 2000 192.168.137.212`

UTC start: 2026-11-03T23:18:47.931569+00:00; UTC finish: 2026-11-03T23:19:17.333883+00:00. Exit code: 0.

Requests: **30**; replies: **30**; timeouts: **0**; other failures: **0**.

Minimum **108 ms**, median **128.5 ms**, mean **128.6667 ms**, maximum **168 ms**.

No less-than observations. Statistics use the integer-resolution RTTs reported by Windows ping. Reply-only RTT statistics; failures are retained separately.

| Request | Host output receipt UTC | Status | Reported RTT ms |
|---:|---|---|---:|
| 1 | 2026-11-03T23:18:48.089036+00:00 | reply | 129 |
| 2 | 2026-11-03T23:18:49.090870+00:00 | reply | 128 |
| 3 | 2026-11-03T23:18:50.145648+00:00 | reply | 168 |
| 4 | 2026-11-03T23:18:51.134348+00:00 | reply | 143 |
| 5 | 2026-11-03T23:18:52.111199+00:00 | reply | 109 |
| 6 | 2026-11-03T23:18:53.146834+00:00 | reply | 143 |
| 7 | 2026-11-03T23:18:54.153871+00:00 | reply | 134 |
| 8 | 2026-11-03T23:18:55.171397+00:00 | reply | 137 |
| 9 | 2026-11-03T23:18:56.150030+00:00 | reply | 111 |
| 10 | 2026-11-03T23:18:57.181203+00:00 | reply | 133 |
| 11 | 2026-11-03T23:18:58.164357+00:00 | reply | 108 |
| 12 | 2026-11-03T23:18:59.192268+00:00 | reply | 126 |
| 13 | 2026-11-03T23:19:00.208426+00:00 | reply | 135 |
| 14 | 2026-11-03T23:19:01.220388+00:00 | reply | 142 |
| 15 | 2026-11-03T23:19:02.208363+00:00 | reply | 128 |
| 16 | 2026-11-03T23:19:03.216924+00:00 | reply | 125 |
| 17 | 2026-11-03T23:19:04.205021+00:00 | reply | 110 |
| 18 | 2026-11-03T23:19:05.248026+00:00 | reply | 143 |
| 19 | 2026-11-03T23:19:06.224216+00:00 | reply | 111 |
| 20 | 2026-11-03T23:19:07.255292+00:00 | reply | 128 |
| 21 | 2026-11-03T23:19:08.281769+00:00 | reply | 143 |
| 22 | 2026-11-03T23:19:09.281991+00:00 | reply | 130 |
| 23 | 2026-11-03T23:19:10.272565+00:00 | reply | 111 |
| 24 | 2026-11-03T23:19:11.294396+00:00 | reply | 126 |
| 25 | 2026-11-03T23:19:12.318197+00:00 | reply | 136 |
| 26 | 2026-11-03T23:19:13.303436+00:00 | reply | 110 |
| 27 | 2026-11-03T23:19:14.334359+00:00 | reply | 135 |
| 28 | 2026-11-03T23:19:15.324193+00:00 | reply | 120 |
| 29 | 2026-11-03T23:19:16.359298+00:00 | reply | 147 |
| 30 | 2026-11-03T23:19:17.331584+00:00 | reply | 111 |

[Complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.raw.txt), [per-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.requests.csv), [complete output with UTC receipt timestamps](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.output_timestamped.csv), [metadata and statistics](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.json). UTC receipt timestamps indicate when the host read each output line, not exact ICMP wire timestamps.

WIFI_PS_NONE was verified in the preceding controlled startup: [startup evidence](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json). No fresh mode readback or reset was performed. Clumsy capture/effects settings are operator-reported; no GUI inspection or changes were made in this run. No firmware, server, or monitor settings changed. This run remains separate from default-power-saving, previous Clumsy-stopped, and university-board results; no data were pooled or overwritten.


## Comparison only with fresh PS_NONE capture-only control

[Control](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.md): mean **2.6333 ms**, median **2 ms**, **30 replies**, no timeouts.

Current outbound-Lag run: mean **128.6667 ms**, **30 replies**, **0 timeouts**. Mean increased by **126.0333 ms**; median increased by **126.5 ms**.

Both runs are HOME_BOARD WIFI_PS_NONE with Clumsy settings operator-reported. This comparison uses only the fresh capture-only control; no default-power-saving or university-board data are used. Every current result remains in request order in the raw output and CSV.
