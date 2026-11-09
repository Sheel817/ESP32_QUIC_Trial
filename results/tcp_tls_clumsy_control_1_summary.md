# TCP_TLS Clumsy control run 1

Source: `log.quic_demo.20261025164836.txt`, SHA-256 `ba71a2f68fd4d87eff6073afdb217c0b21bb9ac48414def44f320236e1d21a6b`. Selected output: `results/tcp_tls_clumsy_control_1.rtt.csv`.

## Intended condition

Intended condition, supplied by the user: **Clumsy capture enabled, all impairment functions disabled**. These are manually configured conditions, not settings verified by the ESP log. No Clumsy configuration capture or independent host-side verification is available in this analysis. The earlier TCP_TLS repeat-2 run is the comparison baseline; its host-side Clumsy state is not independently established here.

## Session identification

- Source line 166: `ESP-ROM:esp32c6-20220919`.
- Source line 168: `rst:0x1 (POWERON),boot:0x6c (SPI_FAST_FLASH_BOOT)`.
- Source line 221: `I (507) quic_demo_main: Starting ESP32-C6 DHT11 over TCP_TLS`.
- Source line 292: `I (4527) quic_demo_main: Connecting to TCP_TLS server 192.168.137.1:14568`.
- Source line 296: `I (6087) TLS: TCP_TLS negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256 wolfSSL_cipher=TLS13-AES128-GCM-SHA256 suite=0x1301 ALPN=mqtt certificate_verification=NONE (mode=0)`.
- Source line 298: `I (6097) quic_demo_main: TCP_TLS connection established`.
- Source line 300: `I (7107) quic_demo_main: MQTT connected over TCP_TLS`.
- Source line 302: `I (7217) quic_demo_main: Subscription acknowledged`.

The ROM banner and reset-reason line identify **one** POWERON reset, not two resets. Exactly one post-reset TCP_TLS startup, connection attempt, negotiated TLS report, connection establishment, MQTT connection, and subscription acknowledgment were found. There is no ambiguity about the selected session's transport. The 165 pre-reset records belong to a separate partial session whose transport is **unknown** because startup evidence is absent. They span sequences **2016-2180**, ESP timestamps **10107387-10929007 ms** and are excluded. Boot sessions are kept separate.

## Selection and counts

Use only the identified post-reset TCP_TLS session. Exclude pre-reset records and ESP log timestamps below **60000 ms** (exactly 60000 ms is eligible). Order by ESP log timestamp, with raw-log line order resolving ties; select up to the first **415** eligible records. Retain every outlier and do not silently deduplicate, impute, or substitute records. Mean is arithmetic; median is the middle value (or mean of the middle pair). Nearest-rank P95 is sorted value `ceil(0.95 * n)`, without interpolation. Statistics are recomputed from each selected CSV and displayed to three decimal places in milliseconds.

| Stage | Records |
|---|---:|
| APP_RTT candidate lines in raw log | 570 |
| Valid raw records | 570 |
| Invalid APP_RTT lines | 0 |
| Pre-reset records excluded | 165 |
| Post-reset TCP_TLS records | 405 |
| Warm-up records excluded below 60000 ms | 10 |
| Total excluded valid records | 175 |
| Eligible records | 395 |
| Selected | 395 |
| Eligible records beyond selection, not used | 0 |
| Shortfall relative to 415 | 20 |

**Only 395 eligible records exist: 20 short of 415. All 395 are selected.**

Post-reset session: sequences **1-405**, ESP timestamps **12247-2036267 ms**; first/last source lines 303/707. Selected window: sequences **11-405**, ESP timestamps **62347-2036267 ms**; first/last source lines 313/707.

## Selected statistics

| Condition | Samples | Sequence range | ESP timestamp range (ms) | Min (ms) | Mean (ms) | Median (ms) | P95 (ms) | Max (ms) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| TCP_TLS_clumsy_control | 395 | 11-405 | 62347-2036267 | 26.484 | 70.341 | 67.832 | 108.576 | 147.555 |

Nearest-rank P95 uses rank **376** of 395. The maximum is retained.

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, from immediately before ESP32 MQTT_Publish to delivery of the sequence-matched returned publication to the MQTT callback, before JSON parsing and console logging. It includes application processing and scheduling and differs from transport RTT. Both timestamps use the ESP32 clock; laptop UTC is not subtracted from ESP uptime.

## Diagnostics

No duplicate sequences, internal sequence gaps, or sequence/timestamp regressions were found within the post-reset session, eligible records, or selected records. No additional reset or reconnect, error-level ESP message, connection/handshake failure, disconnect, assertion, crash, or Task stopped message was found after reset. Connection/error candidates: 0. The log ends at sequence 405; it does not establish why capture ended. The shortfall is not an internal sequence gap.

Scope checks (empty arrays mean no flags): `{"pre_reset_partial_session":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"post_reset_session":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"eligible":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"selected":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`. Invalid source lines: `[]`.

3 startup Wi-Fi warnings were recorded, followed by successful TLS/MQTT establishment:

- Line 258: `W (727) wifi:Password length matches WPA2 standards, authmode threshold changes from OPEN to WPA2`.
- Line 266: `W (3287) wifi:(trc)band:2G, phymode:3, highestRateIdx:0, lowestRateIdx:11, dataSchedTableSize:14`.
- Line 284: `W (3457) wifi:<ba-add>idx:0, ifx:0, tid:0, TAHI:0x100bb8a, TALO:0x8c9d8cb6, (ssn:4, win:64, cur_ssn:4), CONF:0xc0000005`.

These messages do not verify Clumsy settings or establish a cause for observed RTT differences. Raw logs and earlier results are preserved; no firmware changes, builds, or flashing were performed.
