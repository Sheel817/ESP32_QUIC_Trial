# TCP_TLS repeat run 2

Raw source: `log.quic_demo.20261025135315.txt`. SHA-256: `ecfd99217ccef3674a77340a7ac19aed6a13b26066099874de0dc87264971b6c`.
Selected data: `tcp_tls_repeat_2.rtt.csv` with columns `esp_log_timestamp_ms,seq,app_rtt_ms`.

## Boot and transport evidence

- Source line 84: `ESP-ROM:esp32c6-20220919`.
- Source line 86: `rst:0x1 (POWERON),boot:0x6c (SPI_FAST_FLASH_BOOT)`.
- Source line 139: `I (507) quic_demo_main: Starting ESP32-C6 DHT11 over TCP_TLS`.
- Source line 209: `I (4527) quic_demo_main: Connecting to TCP_TLS server 192.168.137.1:14568`.
- Source line 213: `I (6077) TLS: TCP_TLS negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256 wolfSSL_cipher=TLS13-AES128-GCM-SHA256 suite=0x1301 ALPN=mqtt certificate_verification=NONE (mode=0)`.
- Source line 215: `I (6087) quic_demo_main: TCP_TLS connection established`.
- Source line 217: `I (7097) quic_demo_main: MQTT connected over TCP_TLS`.
- Source line 219: `I (7207) quic_demo_main: Subscription acknowledged`.

One board reset was identified by the ROM banner at line 84 and its reset reason `0x1 (POWERON)`. These are two markers of the same reset, not two boots. The new session is explicitly **TCP_TLS**. No additional resets or reconnects were found: there is one TCP_TLS startup, connection attempt, negotiated TLS report, connection-established message, MQTT connection, and subscription acknowledgment. Boot sessions are not combined.

The 83 records before the reset form a separate partial session with **unknown transport** because no startup evidence is recorded for that partial session. They span sequences **19-101**, ESP timestamps **102387-513247 ms** and are excluded even though their timestamps exceed 60000 ms.

## Selection and counts

The shared warm-up rule excludes ESP log timestamps below **60000 ms** within the identified post-reset session (exactly 60000 ms is eligible). Records are ordered by ESP log timestamp, with source-line order resolving ties, and up to the first **415** eligible measurements are selected. Outliers and duplicates are not silently removed; no missing records are imputed. Statistics below are recomputed from the selected CSV values, not copied from earlier summaries. Mean is arithmetic; median averages the two middle sorted values when the count is even. P95 uses the one-based nearest rank `ceil(0.95 * n)`, without interpolation. Values are displayed to three decimal places in milliseconds.

| Stage | Records |
|---|---:|
| Valid RTT records in raw file | 502 |
| Excluded before reset | 83 |
| Records in new TCP_TLS boot session | 419 |
| Excluded warm-up records below 60000 ms | 10 |
| Total excluded (pre-reset plus warm-up) | 93 |
| Eligible after reset and warm-up | 409 |
| Selected | 409 |
| Eligible records beyond selection, not used | 0 |
| Invalid RTT lines | 0 |

**Only 409 eligible records exist: 6 fewer than the requested 415.** All 409 are selected. The log ends at sequence 419; the shortfall is not an internal sequence gap, and no Task stopped message establishes why recording ended.

Post-reset full session: sequences **1-419**, ESP timestamps **12237-2106377 ms**. Selected window: sequences **11-419**, ESP timestamps **62337-2106377 ms**. The selected first/last source lines are **230/638**.

## Selected-data statistics

| Transport | Samples | Sequence range | ESP timestamp range (ms) | Min (ms) | Mean (ms) | Median (ms) | P95 (ms) | Max (ms) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| TCP_TLS | 409 | 11-419 | 62337-2106377 | 26.834 | 70.186 | 67.688 | 107.590 | 367.506 |

Nearest-rank P95 uses rank **389** of 409. The selected maximum **367.506 ms** is retained as observed.

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, measured on the ESP32 from immediately before MQTT_Publish to delivery of the sequence-matched returned publication on `esp32/quic/test` to the coreMQTT callback, before JSON parsing and console logging. It includes application processing and scheduling and is different from transport RTT. Both timestamps use the ESP32 clock; laptop UTC and ESP32 uptime are not subtracted.

## Validation issues

- Duplicate sequences, gaps and regressions within each scope: `{"session":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"eligible":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"selected":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`. Empty arrays mean none were found.
- The raw file reuses sequence numbers across the reset. These are separate sessions; no cross-session deduplication was applied.
- Connection/error candidates after reset: **0**. No error-level ESP messages, failed connections, disconnects, closing/draining messages, assertions, crashes, or Task stopped messages were observed after reset.
- Three startup Wi-Fi warnings were observed; successful TCP_TLS/MQTT establishment follows them:

- Source line 175: `W (677) wifi:Password length matches WPA2 standards, authmode threshold changes from OPEN to WPA2`.
- Source line 183: `W (3237) wifi:(trc)band:2G, phymode:3, highestRateIdx:0, lowestRateIdx:11, dataSchedTableSize:14`.
- Source line 201: `W (3397) wifi:<ba-add>idx:0, ifx:0, tid:0, TAHI:0x100bb8a, TALO:0x8c9d8cb6, (ssn:4, win:64, cur_ssn:4), CONF:0xc0000005`.

The raw log and earlier results, including the QUIC selected CSV, remain unchanged. No firmware edits, builds, or flashing were performed.
