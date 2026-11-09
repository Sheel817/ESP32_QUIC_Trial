# QUIC Clumsy control run 1

Source: `log.quic_demo.20261025181444.txt`, SHA-256 `9017f49b479ff11753b7d399cad03c1f54743a02167a5d3eb3b23321f611c49c`. Selected CSV: `results/quic_clumsy_control_1.rtt.csv`; columns `esp_log_timestamp_ms,seq,app_rtt_ms`.

## Manually confirmed condition

The user confirmed **all Clumsy effects were unchecked before starting capture**. This is a manually reported condition. **The ESP log cannot verify Clumsy settings or capture activity**, including whether capture remained active throughout the selected window. Earlier host-side conditions are not independently verified here. No Clumsy setting is inferred from RTT values or ESP startup messages.

## Reset and session identification

- Raw-log line 4: `ESP-ROM:esp32c6-20220919`.
- Raw-log line 6: `rst:0x1 (POWERON),boot:0x6c (SPI_FAST_FLASH_BOOT)`.
- Raw-log line 59: `I (533) quic_demo_main: Starting ESP32-C6 DHT11 over QUIC`.
- Raw-log line 130: `I (4553) quic_demo_main: Connecting to QUIC server 192.168.137.1:14567`.
- Raw-log line 142: `I (7183) TLS: QUIC negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256 wolfSSL_cipher=TLS13-AES128-GCM-SHA256 suite=0x1301 ALPN=mqtt certificate_verification=NONE (mode=0)`.
- Raw-log line 143: `I (7203) QUIC: QUIC handshake completed callback triggered!`.
- Raw-log line 146: `I (7203) quic_demo_main: QUIC connection established`.
- Raw-log line 149: `I (8303) quic_demo_main: MQTT connected over QUIC`.
- Raw-log line 151: `I (8423) quic_demo_main: Subscription acknowledged`.
- Raw-log line 152: `I (13453) quic_demo_main: APP_RTT seq=1 app_rtt_ms=85.984`.

The ROM banner at line 4 and reset-reason line 6 identify one **POWERON** reset, not two separate boots. Exactly one post-reset QUIC startup, connection attempt, TLS negotiation, actual handshake-completed callback, established QUIC connection, MQTT connection, and subscription acknowledgment were found. The first APP_RTT exactly matches the requested session anchor: **seq 1, 85.984 ms, ESP timestamp 13453 ms**, raw-log line 152. There is no selected-session ambiguity or additional boot session in this file. Sessions are not combined.

The 3 pre-reset measurements form a separate partial session with **unknown transport** because no startup evidence precedes them in this file. They span sequences **25-27**, ESP timestamps **133783-143743 ms** and are excluded regardless of their timestamps.

## Selection and counts

Strip ANSI console colours for parsing without altering the raw file. Parse ESP log timestamp, sequence number, and application RTT. Use only the anchored post-reset QUIC session. Exclude timestamps **below 60000 ms**; exactly 60000 ms is eligible. Sort eligible records chronologically by ESP log timestamp, resolving ties by original source-line order, and select the **first 415**. Retain every outlier; do not deduplicate, trim by RTT, interpolate, or combine sessions.

| Stage | Records |
|---|---:|
| Raw APP_RTT candidate lines | 551 |
| Valid raw APP_RTT records | 551 |
| Invalid APP_RTT lines | 0 |
| Pre-reset records excluded | 3 |
| Post-reset QUIC session records | 548 |
| Warm-up records excluded below 60000 ms | 10 |
| Excluded before chronological selection (pre-reset plus warm-up) | 13 |
| Eligible records after warm-up | 538 |
| Selected first measurements | 415 |
| Later eligible records beyond the selected window, unused | 123 |
| Total valid raw records omitted from selected CSV | 136 |
| Shortfall from 415 | 0 |

The full **415**-record selection is available; **no shortfall**. Later eligible measurements are unused solely because of the predefined first-415 limit.

- Full post-reset session: sequences **1-548**, ESP timestamps **13453-2753713 ms**, raw-log lines 152-699.
- Warm-up: sequences **1-10**, ESP timestamps **13453-58533 ms**.
- Eligible pool: sequences **11-548**, ESP timestamps **63563-2753713 ms**.
- Selected: sequences **11-425**, ESP timestamps **63563-2137553 ms**, raw-log lines 162-576.

## Application RTT statistics and descriptive comparisons

| Run | Samples | Sequence range | ESP timestamp range (ms) | Min (ms) | Mean (ms) | Median (ms) | P95 (ms) | Max (ms) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| QUIC repeat 2 baseline | 415 | 11-425 | 63463-2137403 | 25.096 | 67.710 | 65.605 | 105.811 | 126.811 |
| QUIC Clumsy control 1 | 415 | 11-425 | 63563-2137553 | 25.038 | 69.310 | 65.774 | 105.940 | 285.589 |
| TCP_TLS Clumsy control 1 | 395 | 11-405 | 62347-2036267 | 26.484 | 70.341 | 67.832 | 108.576 | 147.555 |

All three sets are recomputed from their **CSV data**, using every selected record. No comparison set is truncated to equalize counts. Mean is arithmetic; median is the middle sorted value (or average of the middle pair). P95 uses the one-based nearest rank `ceil(0.95 * n)`, without interpolation. P95 ranks: **395** for QUIC baseline, **395** for QUIC control, and **376** for TCP_TLS control. Results are displayed to three decimal places in milliseconds.

The selected QUIC control maximum is **285.589 ms**, sequence **198**, ESP log timestamp **1000573 ms**, raw-log line **349**. It is retained. The log alone does not establish its cause.

| QUIC control minus comparison run | Minimum (ms) | Mean (ms) | Median (ms) | P95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|
| QUIC repeat 2 baseline | -0.058 | +1.600 | +0.169 | +0.129 | +158.778 |
| TCP_TLS Clumsy control 1 | -1.446 | -1.031 | -2.058 | -2.636 | +138.034 |

Signed differences use the unrounded CSV-derived statistics. Compared with the QUIC baseline, this QUIC control has a higher observed mean and maximum while its median and P95 are close in these records. Compared with the TCP_TLS control, its observed mean, median, and P95 are lower while its maximum is higher. These are descriptions of the selected observations, **not a causal Clumsy effect or a claim of protocol superiority**. There is one run per listed condition, different sample counts and selected-window durations, and no estimate of repeated-run uncertainty. Host capture settings, Wi-Fi conditions, and application/network variation are not controlled or verified by the ESP log.

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, from immediately before ESP32 MQTT_Publish to delivery of the sequence-matched returned publication to the MQTT callback, before JSON parsing and console logging. It includes application processing and scheduling and differs from transport RTT. Both timestamps use the ESP32 clock; laptop UTC and ESP uptime are not subtracted. ESP log timestamps identify the log-line uptime, not the original send time.

## Comparison sources and shared warm-up

- **QUIC repeat 2 baseline:** `results/quic_repeat_2.rtt.csv`, SHA-256 `ec589382f4c882dacbf05f106ea65dbae5872dd0bef4f1d1c0778e65b50e3446`, from `log.quic_demo.20261024182008.txt`.
- **QUIC Clumsy control 1:** `results/quic_clumsy_control_1.rtt.csv`, SHA-256 `3c535ee0468178a682183d737749be1636e7abf6a5c4398c4cbf47a43d97fc8a`, from `log.quic_demo.20261025181444.txt`.
- **TCP_TLS Clumsy control 1:** `results/tcp_tls_clumsy_control_1.rtt.csv`, SHA-256 `c719ba700129400b9934625bc5ced7d8acb6e0464c3335fd9b877b6a6bf3876a`, from `log.quic_demo.20261025164836.txt`.

All selected CSVs use the same **post-reset, ESP timestamp >=60000 ms, first up-to-415 eligible measurements** rule. The existing QUIC repeat-2 CSV has 415 selected records from 530 eligible measurements. The existing TCP_TLS control CSV has all 395 eligible records, **20 short of 415**; missing records are not imputed or replaced. Their prior selection evidence remains in `quic_repeat_2_summary.md` and `tcp_tls_clumsy_control_1_summary.md`.

## Validation and connection diagnostics

- One reset and one confirmed QUIC/MQTT connection are recorded. No additional resets, reconnects, connection failures, disconnects, closing/draining errors, assertions, crashes, or Task stopped messages were observed after reset. Connection/error candidates: **0**.
- No duplicate sequences, internal gaps, sequence regressions, or timestamp regressions were found within the pre-reset partial session, the new session, eligible records, or selected records. Scope checks: `{"pre_reset_partial_session":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"post_reset_session":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"eligible":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"selected":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`.
- Repeated sequence numbers across the reset refer to different sessions and are not treated as within-session duplicates.
- Recomputed comparison-CSV checks: `{"QUIC repeat 2 baseline":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"QUIC Clumsy control 1":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"TCP_TLS Clumsy control 1":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`. Empty arrays mean no flags.
- Invalid APP_RTT source lines: `[]`.
- 3 startup Wi-Fi warnings are recorded, followed by successful QUIC/MQTT establishment:

- Raw-log line 96: `W (713) wifi:Password length matches WPA2 standards, authmode threshold changes from OPEN to WPA2`.
- Raw-log line 104: `W (3273) wifi:(trc)band:2G, phymode:3, highestRateIdx:0, lowestRateIdx:11, dataSchedTableSize:14`.
- Raw-log line 122: `W (3453) wifi:<ba-add>idx:0, ifx:0, tid:0, TAHI:0x100bb8a, TALO:0x8c9d8cb6, (ssn:4, win:64, cur_ssn:4), CONF:0xc0000005`.

These startup warnings do not establish the cause of subsequent RTT variation. The recording ends at sequence 548 without a Task stopped message; no reason for stopping capture is inferred. Raw logs, firmware sources/configuration and generated image, existing selected CSVs, figures, and earlier results are preserved unchanged. No build, flash, or firmware edits were performed.
