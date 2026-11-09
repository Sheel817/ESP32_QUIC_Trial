# QUIC repeat run 2

Source: `log.quic_demo.20261024182008.txt`. SHA-256: `e373e597a08c6769a0d35047fa1c8fb82deb0a865738185b05371cf4b14f0096`.

## Reset and session identification

- Source line 22: `ESP-ROM:esp32c6-20220919`.
- Source line 24: `rst:0x1 (POWERON),boot:0x7c (SPI_FAST_FLASH_BOOT)`.
- Source line 77: `I (533) quic_demo_main: Starting ESP32-C6 DHT11 over QUIC`.
- Source line 147: `I (4553) quic_demo_main: Connecting to QUIC server 192.168.137.1:14567`.
- Source line 160: `I (7103) QUIC: QUIC handshake completed callback triggered!`.
- Source line 163: `I (7173) quic_demo_main: QUIC connection established`.
- Source line 166: `I (8213) quic_demo_main: MQTT connected over QUIC`.
- Source line 168: `I (8323) quic_demo_main: Subscription acknowledged`.

The ROM boot banner and reset-reason line belong to the same board reset (reported reason `0x1 (POWERON)`). The 21 RTT records before source line 22 belong to the prior session (sequences 280-300) and are excluded even though their ESP timestamps exceed 60000 ms. There are **no additional resets or reconnects** in the new session: one application startup, QUIC connection attempt, completed handshake, established QUIC connection, MQTT connection, and subscription acknowledgment were found. Sessions were not combined.

## Selection rule and counts

1. Strip ANSI console colours for parsing without modifying the raw log. Parse each APP_RTT line's ESP log timestamp (ms), sequence number, and application RTT (ms).
2. Use only the session after the identified board reset and QUIC startup. Exclude records from before that reset.
3. Exclude records with ESP log timestamps **below 60000 ms** (a timestamp exactly 60000 would be eligible).
4. Sort eligible measurements by ESP log timestamp, breaking ties by source line, and select the **first 415**. Retain every outlier; do not deduplicate, trim by RTT, or interpolate samples.

| Stage | Records |
|---|---:|
| Valid APP_RTT records in entire raw file | 561 |
| Prior-session records excluded before reset | 21 |
| Total records in new post-reset session | 540 |
| Post-reset warm-up records below 60000 ms | 10 |
| Post-reset records after warm-up | 530 |
| Selected first records | 415 |
| Eligible records after selected window, not used | 115 |
| Invalid APP_RTT measurement lines | 0 |

The requested 415-measurement selection is available.

Selected sequence range: **11-425**. The first selected record is source line 179, timestamp **63463 ms**, sequence 11; the last is source line 593, timestamp **2137403 ms**, sequence 425. The CSV contains exactly these 415 selected rows, plus its header. The post-reset session contains sequences 1-540.

## Statistics of the selected measurements

| Samples | Sequence range | Minimum (ms) | Mean (ms) | Median (ms) | Nearest-rank P95 (ms) | Maximum (ms) |
|---:|---|---:|---:|---:|---:|---:|
| 415 | 11-425 | 25.096 | 67.710 | 65.605 | 105.811 | 126.811 |

Mean is the arithmetic mean. Median is the middle sorted RTT (or mean of the two middle values for an even sample count). P95 is sorted value **395**, using one-based rank `ceil(0.95 * 415)`, without interpolation. Statistics use the original recorded values; displayed values are rounded to three decimal places. The selected maximum is retained, not removed as an outlier.

These are **application RTT** measurements: `(receive_time_us - send_time_us) / 1000.0`, from immediately before ESP32 MQTT_Publish to receipt of the sequence-matched echoed publication on `esp32/quic/test` by the MQTT callback. They include application processing and scheduling and are different from ngtcp2 transport RTT. Both RTT timestamps use the ESP32 clock; laptop UTC is not subtracted. This is one QUIC repeat run, not a combination of runs.

## Integrity and connection diagnostics

- session: duplicate sequences []; missing sequence ranges []; sequence regressions (source line pairs) []; RTT timestamp regressions (source line pairs) [].
- eligible: duplicate sequences []; missing sequence ranges []; sequence regressions (source line pairs) []; RTT timestamp regressions (source line pairs) [].
- selected: duplicate sequences []; missing sequence ranges []; sequence regressions (source line pairs) []; RTT timestamp regressions (source line pairs) [].

Empty lists mean no flags were found. No duplicates, missing sequences, or clock-order reversals were removed to obtain these results.

Connection/error candidates after reset: **0**. No connection failures, disconnects, closing/draining messages, error-level ESP logs, assertions, or crashes were observed.

Startup Wi-Fi warning lines (3):

- Line 113: `W (703) wifi:Password length matches WPA2 standards, authmode threshold changes from OPEN to WPA2`.
- Line 121: `W (3253) wifi:(trc)band:2G, phymode:3, highestRateIdx:0, lowestRateIdx:11, dataSchedTableSize:14`.
- Line 139: `W (3423) wifi:<ba-add>idx:0, ifx:0, tid:0, TAHI:0x100bb8a, TALO:0x8c9d8cb6, (ssn:4, win:64, cur_ssn:4), CONF:0xc0000005`.

These startup diagnostics do not indicate a failed connection or a reconnect; successful QUIC/MQTT establishment follows them. The raw source and earlier result files are preserved unchanged. No firmware changes, build, or flashing were performed.
