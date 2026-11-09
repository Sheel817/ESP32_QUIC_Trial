# Initial QUIC versus TCP_TLS application RTT comparison

| Transport | Samples | Minimum (ms) | Average (ms) | Median (ms) | P95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|---:|
| QUIC | 415 | 25.051 | 67.769 | 65.703 | 105.843 | 145.776 |
| TCP_TLS | 415 | 26.670 | 69.179 | 67.793 | 107.550 | 147.677 |

## Sources and validation

- `log.quic_demo.20261022191059.quiet.rtt.csv`: 415 valid measurements, 415 unique sequences; first/last sequence in file order: 391/805. SHA-256: `8598d02a4e94e541b073c663f01e0cc34edb686179c5dbd4a1b06079af267b0c`.
- `log.quic_demo.20261022221325.tcp_tls.rtt.csv`: 415 valid measurements, 415 unique sequences; first/last sequence in file order: 249/663. SHA-256: `5100471fcdd57709a88746fde7d38d952024d38252e40ecda3dd67fe77e2b44f`.

Each source contains exactly 415 data records with columns `seq,app_rtt_ms`. Every sequence is an unsigned 32-bit integer and unique within its file. Every RTT is numeric, finite, and nonnegative. All 415 records from each file are included; no truncation, outlier removal, or imputation was performed. The source files were left unchanged.

## Measurement and statistics

Application RTT is measured entirely on the ESP32: `(receive_time_us - send_time_us) / 1000.0`. The send timestamp is captured immediately before `MQTT_Publish`; the receive timestamp is captured when the returned publication on `esp32/quic/test` reaches the coreMQTT callback, before JSON parsing and console logging. The JSON sequence number matches the echo to its pending send timestamp. This includes application processing and scheduling, and differs from ngtcp2 transport RTT. Laptop UTC and ESP32 uptime are different clocks and are not subtracted.

Minimum and maximum are the smallest and largest observed values. Average is the arithmetic mean. Median is the 208th sorted value for 415 samples. P95 uses the **nearest-rank** definition: sort ascending and select rank `ceil(0.95 * 415) = 395` (one-based), without interpolation. Calculations use the original recorded values and results are displayed to three decimal places in milliseconds.

## Run provenance and interpretation

There is **one run per transport**. The earlier QUIC run **preceded the transport refactor**, while the TCP_TLS run used the later transport-selection firmware. These are initial descriptive comparisons of the supplied runs, not a replicated comparison of both transports under the same current firmware revision. The requested current QUIC build enables a subsequent run using the refactored firmware. No new measurements or flashing are part of this analysis.
