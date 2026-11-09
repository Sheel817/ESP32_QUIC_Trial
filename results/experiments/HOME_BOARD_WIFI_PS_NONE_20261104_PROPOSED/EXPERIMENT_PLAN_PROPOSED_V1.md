# Proposed frozen experiment plan V1

HOME_BOARD ESP32-C6, WIFI_PS_NONE, QUIC versus TCP_TLS. Status: **PROPOSED, NOT STARTED**. This is a plan for future execution; preparing it does not authorize or perform a flash, reset, condition change, or recording. Freeze this version and its artifact manifest before the first formal run. A later protocol change requires a new version and a dated deviation record; never silently alter a completed run or its scheduled condition.

## Design and fixed inputs

Two transports × three conditions × three independent boot sessions = **18 planned runs**, each with a **37-minute / 2,220-second recording from its controlled reset**. Planned recording time totals 666 minutes (11 h 6 min), excluding setup, flashing and checks. Every row is a new recorded boot session, not another window from an already-running session.

- Board: HOME_BOARD, base MAC `40:4c:ca:56:bb:b0`, ESP32-C6 revision v0.0, physical flash 8 MB, COM6 unless a documented enumeration change is verified. DHT11 DATA GPIO4, VCC 3V3, GND GND. Record actual board identity; never substitute university-board data.
- Firmware: only the preserved validated [QUIC PS_NONE build](../../../profiles/wifi_ps_none_20261103/README.md) and matching [TCP_TLS PS_NONE build](../../../profiles/tcp_tls_wifi_ps_none_20261104/README.md). Freeze BIN/ELF/bootloader/partition hashes in [freeze manifest](./freeze_manifest.json). Git HEAD is `3c8c7a30b7b32ae3feaa07788b74eec637be37fc`; the modified source tree's recorded hashes, not HEAD alone, identify the source. Use the same ESP-IDF v6.1, GCC/G++ 15.2.0, effective sdkconfig and locked dependencies.
- Both builds use DEMO_WIFI_PS_NONE=ON. Explicit successful requested/returned `WIFI_PS_NONE(0)` API startup readback is required for every formal measured boot.
- Retain the shared five-second publication interval, 20 ms loop, existing transport/MQTT processing cadence, payload construction, DHT11 wiring, topic `esp32/quic/test`, client ID `esp32_quic_client`, QoS 0, APP_RTT timestamp placement and quiet logging. Do not tune firmware after seeing formal results.
- Server endpoints: QUIC UDP 14567, TCP_TLS TCP 14568, host `192.168.137.1` as compiled. Save the board's actual assigned IP from each measured startup; do not assume an earlier IP. Record host/server addresses, interface, Wi-Fi SSID/BSSID, channel, RSSI when available, AP beacon/DTIM information, OS/tool versions, time zone and relevant host load/background traffic. Keep the same host, AP/location, power supply and sensor setup; document deviations.
- Both paths must log TLS 1.3, `TLS_AES_128_GCM_SHA256` / suite 0x1301, ALPN `mqtt`, and the existing certificate-verification mode NONE. TCP_TLS additionally must report `TCP_NODELAY=1`. These are existing protocol choices, not new firmware changes. Save actual negotiated values and server certificate hash; a mismatched startup is a failed run, not a valid RTT sample.

## Conditions and impairment scope

Capture stays running in **every** formal condition. Use a constant filter within each transport, and change only the predeclared condition between runs, before reset:

| Condition ID | Capture | Lag | Drop | Direction | Other effects |
|---|---|---|---|---|---|
| CONTROL | Running | Off | Off | Neither effect active | All off |
| LAG100_OUT | Running | Configured 100 ms | Off | Outbound only, inbound unchecked | All off |
| DROP1_OUT | Running | Off | Configured 1% | Outbound only, inbound unchecked | All off |

QUIC filter: `udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)`.

TCP_TLS filter: `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`.

Keep filter text identical across conditions for a transport. No ICMP filter or pings during formal runs. Record exact filter, tool version and executable hash, capture Running state, Lag/Drop checkboxes, values, inbound/outbound checkboxes and every other effect's disabled state. Save screenshots before reset and after recording, with UTC and hashes. If settings are only operator-reported, label them explicitly; do not claim independently verified per-packet impairment. Configured 100 ms Lag is not an assertion of exactly +100 ms APP_RTT. Configured 1% Drop is not an observed packet-loss or message-loss rate; TCP/QUIC retransmission and control traffic may also be affected. Retain available counters/packet capture evidence if gathered under the same predeclared procedure for every run; do not add a new diagnostic to selected runs only.

There is no impairment ramp or mid-run toggle. Settings must be stable before the measured reset and throughout the 37 minutes. For the next condition, finish/close the previous recording, configure/check the next setting, then begin the next boot session. Do not reset within a run to improve results.

## Predeclared run order

The order is deterministic, chosen before formal observations. Three chronological blocks each contain every transport/condition combination once. Transport alternates within each block, and block 2 reverses block 1. This is a blocked schedule, not a claim of randomized assignment or complete order-effect balance. Do not reorder based on results; log scheduling deviations.

| Order | Block / replicate | Run ID | Transport | Condition |
|---:|---:|---|---|---|
| 1 | 1 | HBPSN-01 | QUIC | CONTROL |
| 2 | 1 | HBPSN-02 | TCP_TLS | LAG100_OUT |
| 3 | 1 | HBPSN-03 | QUIC | DROP1_OUT |
| 4 | 1 | HBPSN-04 | TCP_TLS | CONTROL |
| 5 | 1 | HBPSN-05 | QUIC | LAG100_OUT |
| 6 | 1 | HBPSN-06 | TCP_TLS | DROP1_OUT |
| 7 | 2 | HBPSN-07 | TCP_TLS | DROP1_OUT |
| 8 | 2 | HBPSN-08 | QUIC | LAG100_OUT |
| 9 | 2 | HBPSN-09 | TCP_TLS | CONTROL |
| 10 | 2 | HBPSN-10 | QUIC | DROP1_OUT |
| 11 | 2 | HBPSN-11 | TCP_TLS | LAG100_OUT |
| 12 | 2 | HBPSN-12 | QUIC | CONTROL |
| 13 | 3 | HBPSN-13 | QUIC | LAG100_OUT |
| 14 | 3 | HBPSN-14 | TCP_TLS | DROP1_OUT |
| 15 | 3 | HBPSN-15 | QUIC | CONTROL |
| 16 | 3 | HBPSN-16 | TCP_TLS | LAG100_OUT |
| 17 | 3 | HBPSN-17 | QUIC | DROP1_OUT |
| 18 | 3 | HBPSN-18 | TCP_TLS | CONTROL |

[Run register CSV](./run_register.csv) and [run register workbook](../../../outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx) contain exactly these 18 planned rows. All observed/result fields start blank and all runs start NOT_RUN. The CSV is the machine-readable working register; if the workbook is used for entry, export/reconcile that single working register rather than independently editing two divergent copies.

## Required checks before each future measured reset

1. Confirm board/MAC, DHT11 wiring, intended transport/condition/order and unique run ID. Record operator and environment. Complete setup/flashing, if separately authorized, before the formal recording; retain its verification log and artifact hashes. Any automatic post-flash boot is setup only. Do not reuse its RTTs in the formal session.
2. Verify prepared BIN/ELF/partition hashes against the frozen manifest. Use the correct ELF for the persistent monitor. Start a fresh run-named raw log and server log boundary with logging active before reset. Record serial port, baud, monitor command/PID/version, source byte boundaries and start UTC. No competing serial monitor may own COM6.
3. Confirm the matching server listener/process and source hash: UDP 14567 / quic_server.py or TCP 14568 / tcp_tls_server.py. The current QUIC server may remain running during TCP runs; confirm transport filtering isolates the intended server traffic. Save server command/PID, listener check and certificate hash. Do not silently restart servers mid-run; record interruptions.
4. Verify exact Clumsy filter, capture Running, condition/direction/value and other effects off. Save evidence and record whether independently observed or operator-reported. If a required preflight item is missing, leave the run NOT_RUN and record the blocked setup attempt; do not start the formal timer.
5. Issue one controlled reset with logging active. Record reset request/release UTC and host monotonic anchor, reset mechanism, boot-session ID and raw startup boundary. Each planned row is an independently reset initial boot. After reset, verify expected transport and ELF digest prefix against the full local frozen ELF, explicit WIFI_PS_NONE requested/returned=0, actual IP/MAC, QUIC/TCP+TLS and MQTT connection, subscription acknowledgement, TLS details, and TCP_NODELAY for TCP_TLS. Record that a printed ELF prefix is a prefix comparison, not a full on-device digest measurement.

## Recording window and deterministic selection

- Record **exactly 2,220 host-monotonic seconds from controlled-reset release**. Save the UTC start/end and monotonic elapsed time. ESP timestamps remain the eligibility clock; host UTC is provenance, not the RTT clock. If only reset-request anchoring is available, record that implementation deviation and measured reset pulse/duration rather than silently claiming release precision.
- Continue raw recording for the whole 37 minutes even when 415 samples have already arrived. Never extend the run to obtain 415. Save complete startup, all later RTTs, warnings/errors, unmatched/duplicate/full-storage diagnostics, reconnects and server output. A physically interrupted recording keeps its actual duration and interruption evidence and is not called a complete 37-minute run.
- Within the initial measured boot, exclude APP_RTT lines whose **ESP log uptime is below 60,000 ms**. Eligibility is `esp_log_uptime_ms >= 60000`, before `2220000`, and within the fixed host recording window. Use the existing firmware's ESP log timestamp in milliseconds as the logged uptime criterion; do not imply a new internal timer/readback. Exclude setup boots and incomplete/corrupt lines from numeric analysis, retaining them in raw output and an exclusion ledger.
- Select the **first 415 eligible sequence-matched APP_RTT records in source-log arrival order**. Retain every numeric value, including outliers. Do not sort by RTT, trim, winsorize, or substitute later records. Keep eligibility count for the whole window, selected count, and first/last sequence/timestamp.
- If eligible count N < 415, select all N and report **shortfall = 415 − N**. Zero observed RTTs means unavailable mean, not zero RTT. Never pool across boot sessions or conditions to fill a shortfall. If N > 415, preserve all raw records and the extra eligible records, marking them outside the primary first-415 subset.
- Track sequence gaps, repeats and timestamp regressions. First sequence after warmup need not be 1. A gap indicates a missing matched RTT record, not proof of packet loss; retain publish/send failure and echo diagnostics where logged. Duplicate/unmatched diagnostics are evidence, not extra independent RTT samples.
- If a reboot occurs, keep the entire fixed-window recording and mark the run failed/interrupted; identify each boot, but do not concatenate post-reboot RTTs into the initial-boot first-415 sample. If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.

## Run files and metadata

For each run, use a new `runs/<run_id>/` directory under this proposed study directory when execution is separately started. Store raw serial/server logs, startup/settings evidence, all parsed/eligible/selected RTT CSVs, exclusion/error ledger and `metadata.json`. Required metadata fields:

- Protocol ID/version and plan/register hashes; run order, block, transport, condition and boot-session ID.
- Board identity/wiring, actual assigned IP, host/AP/interface context and UTC/monotonic timestamps.
- Image/ELF/bootloader/partition, source/config/dependency, server/certificate, tool/filter/settings hashes or exact version/text as applicable.
- Monitor/server commands and PIDs; reset evidence; log paths, byte boundaries, final sizes/hashes and time-zone conversion.
- Startup gate results and exact raw lines: transport/digest/WIFI_PS_NONE, TLS/cipher/ALPN, MQTT/subscription, TCP_NODELAY where applicable.
- Clumsy evidence files and source type, configured Lag/Drop/direction, other effects off, pre/post state and interruptions.
- Requested/actual duration; all eligible/selected counts; shortfall; all per-record sequences, ESP timestamps, host receipt UTC and APP_RTT; errors/gaps/reboots and any protocol deviation.

Keep missing fields blank with a reason, never populated with invented zeroes or assumed passes. Close/hash immutable run files after the window. The continuously growing monitor log must be cited by exact byte ranges and interval hashes if it remains open.

## Reporting and failed-run policy

The independent analysis unit is a boot session, not 415 independent sessions. Report every scheduled session's selected count, shortfall, mean, median, min/max and descriptive percentiles, plus its errors/gaps and completion/startup/settings status. Report each cell's three session means and their equal-session descriptive aggregate; preserve per-session distributions and do not let a longer session silently dominate a pooled mean. A short session's statistic uses its actual N and is visibly flagged. Do not substitute numeric zero for unavailable session statistics or hide a failed session in an aggregate denominator.

Predeclare comparisons within each condition (QUIC vs TCP_TLS) and within each transport (Lag or Drop vs capture-only). Distinguish configured impairment from measured application response. With only three sessions per cell, emphasize session-level variability and failed/short-run evidence rather than claiming robust population inference from thousands of correlated RTT records.

Once a measured reset starts, retain the run even if startup/settings/connection checks fail. Its scheduled row receives FAILED_STARTUP, FAILED_SETTINGS, INTERRUPTED, COMPLETE_SHORTFALL or COMPLETE with a reason; preflight-only failed attempts remain separately documented without pretending a boot was recorded. No automatic replacement or extra run to improve results. Any later approved replacement gets a new ID and a deviation record and never overwrites the original or silently becomes the primary scheduled session.

## Separation and current state

All earlier HOME_BOARD short pilots, ICMP diagnostics, default-power-saving and university-board data remain **exploratory**, under their original files in results/pilots. None counts toward the 18 sessions or the first-415 formal subsets. The proposed protocol is informed by setup experience; it is not retrospectively applied to exploratory observations.

This preparation task only builds a separate TCP_TLS profile and saves this proposal/register. It does not flash/reset, start the TCP server, alter firmware/timing, or change current monitor/server/Clumsy settings. Keep effects off and the current QUIC server and monitor running. Protocol execution and actual condition changes are future work.

