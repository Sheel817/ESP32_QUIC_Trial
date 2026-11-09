# HOME_BOARD WIFI_PS_NONE — ICMP diagnostic, before/on/after

Three separate 30-request ICMP runs to 192.168.137.212 using `ping.exe /n 30 /w 2000 192.168.137.212`. Statistics below were recomputed from the actual three per-request CSVs, not copied from reference means. No default-power-saving, university-board, or APP_RTT data are included.

Before: ICMP capture running, all effects disabled. On: Lag 100 ms outbound only, other effects off. After: **HOME_BOARD, WIFI_PS_NONE, ICMP capture running, all effects off, return-to-control.** Capture and effects settings are operator-reported. No GUI or firmware/filter/server/monitor settings were changed in the return run. A 10-second wait preceded that ping command. WIFI_PS_NONE was verified in the [earlier controlled startup](./HOME_BOARD_WIFI_PS_NONE_20261103T230410Z/startup_checks.json); no fresh readback or reset was performed.

| Stage | Requests | Replies | Timeouts | Other failures | Min ms | Median ms | Mean ms | Max ms | Censored |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Before | 30 | 30 | 0 | 0 | 1.0 | 2.0 | 2.6333 | 12.0 | 0 |
| Lag on | 30 | 30 | 0 | 0 | 108.0 | 128.5 | 128.6667 | 168.0 | 0 |
| After | 30 | 30 | 0 | 0 | 1.0 | 2.0 | 3.1333 | 13.0 | 0 |

Lag-on mean minus before: **126.0333 ms**. Return-to-control mean minus before: **0.5000 ms**. Return-to-control mean minus lag-on: **-125.5333 ms**.

All reported RTTs are retained in request order, including failures and `<1 ms` if present. Statistics are reply-only, at Windows ping's reporting resolution. If censored values exist, each `<1 ms` contributes the interval [0,1) rather than an invented exact value; the mean is reported as lower-inclusive/upper-exclusive bounds. Zero censored counts mean no such bounds were required.

| Request | Before RTT ms | Lag-on RTT ms | After RTT ms |
|---:|---:|---:|---:|
| 1 | 12 | 129 | 2 |
| 2 | 1 | 128 | 1 |
| 3 | 2 | 168 | 2 |
| 4 | 1 | 143 | 2 |
| 5 | 2 | 109 | 6 |
| 6 | 2 | 143 | 2 |
| 7 | 7 | 134 | 1 |
| 8 | 2 | 137 | 2 |
| 9 | 2 | 111 | 2 |
| 10 | 2 | 133 | 2 |
| 11 | 1 | 108 | 2 |
| 12 | 2 | 126 | 3 |
| 13 | 2 | 135 | 2 |
| 14 | 3 | 142 | 13 |
| 15 | 2 | 128 | 2 |
| 16 | 2 | 125 | 2 |
| 17 | 2 | 110 | 8 |
| 18 | 2 | 143 | 13 |
| 19 | 1 | 111 | 6 |
| 20 | 2 | 128 | 3 |
| 21 | 2 | 143 | 2 |
| 22 | 3 | 130 | 1 |
| 23 | 2 | 111 | 2 |
| 24 | 2 | 126 | 1 |
| 25 | 4 | 136 | 1 |
| 26 | 5 | 110 | 2 |
| 27 | 2 | 135 | 3 |
| 28 | 3 | 120 | 2 |
| 29 | 2 | 147 | 3 |
| 30 | 2 | 111 | 1 |

## Actual input sources

- Before: [actual 30-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.requests.csv), [complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.raw.txt), [UTC timestamped output](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.output_timestamped.csv), [run metadata](./HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z.json).
- Lag on: [actual 30-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.requests.csv), [complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.raw.txt), [UTC timestamped output](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.output_timestamped.csv), [run metadata](./HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z.json).
- After: [actual 30-request CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.requests.csv), [complete raw output](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.raw.txt), [UTC timestamped output](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.output_timestamped.csv), [run metadata](./HOME_BOARD_WIFI_PS_NONE_ICMP_RETURN_CONTROL_20261103T232229Z.json).

[Recomputed statistics CSV](./HOME_BOARD_WIFI_PS_NONE_ICMP_BEFORE_ON_AFTER_20261103T232229Z.statistics.csv), [all 90 requests with source/UTC metadata](./HOME_BOARD_WIFI_PS_NONE_ICMP_BEFORE_ON_AFTER_20261103T232229Z.all_requests.csv), [statistics and source SHA-256 hashes](./HOME_BOARD_WIFI_PS_NONE_ICMP_BEFORE_ON_AFTER_20261103T232229Z.json). Original source files are preserved; these derived artifacts use new filenames.

This remains an **ICMP diagnostic**, not an application/QUIC RTT experiment. The sequential pilot shows the observed before/on/after pattern under operator-reported settings; it does not measure packet-by-packet Clumsy delays or establish a long-run distribution. Capture is left running with Lag off as reported by the operator, without automated settings changes.
