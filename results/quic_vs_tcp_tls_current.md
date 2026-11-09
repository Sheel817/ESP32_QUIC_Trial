# Current QUIC versus TCP_TLS application RTT comparison

| Transport | Samples | Sequence range | Minimum (ms) | Mean (ms) | Median (ms) | P95 (ms) | Maximum (ms) |
|---|---:|---|---:|---:|---:|---:|---:|
| QUIC | 412 | 87-498 | 25.077 | 68.036 | 66.112 | 105.836 | 145.990 |
| TCP_TLS | 415 | 249-663 | 26.670 | 69.179 | 67.793 | 107.550 | 147.677 |

## Sources and validation

- **QUIC:** `log.quic_demo.20261022235848.quic.rtt.csv`. 412 valid measurements, 412 unique sequences, sequence range 87-498. Nearest-rank P95 selects sorted record 392 (one-based). SHA-256: `17c04585c83b8f6c3897602aba10a378d4b0fbfd57f625bc912e9efa9b495ac8`.
- **TCP_TLS:** `log.quic_demo.20261022221325.tcp_tls.rtt.csv`. 415 valid measurements, 415 unique sequences, sequence range 249-663. Nearest-rank P95 selects sorted record 395 (one-based). SHA-256: `5100471fcdd57709a88746fde7d38d952024d38252e40ecda3dd67fe77e2b44f`.

The expected counts were verified: **QUIC 412; TCP_TLS 415**. Every data record in both files is valid: each sequence is an unsigned 32-bit integer and unique within its file, and every RTT is numeric, finite, and nonnegative. There are no invalid measurements or duplicate sequences. All measurements in each file are included, with no equal-count truncation, outlier removal, or imputation. The source files were left unchanged.

## Measurement and statistics

Application RTT is measured entirely on the ESP32: `(receive_time_us - send_time_us) / 1000.0`. The send timestamp is captured immediately before `MQTT_Publish`; the receive timestamp is captured when the returned publication on `esp32/quic/test` reaches the coreMQTT callback, before JSON parsing and console logging. The JSON sequence number matches the echo to its pending send timestamp. This includes application processing and scheduling, and differs from ngtcp2 transport RTT. Laptop UTC and ESP32 uptime are different clocks and are not subtracted.

Minimum and maximum are the smallest and largest observed values. Mean is the arithmetic mean of all included measurements. The QUIC median averages sorted records 206 and 207 (412 samples); the TCP_TLS median is sorted record 208 (415 samples). P95 uses the **nearest-rank** definition: sort ascending and select rank `ceil(0.95 * n)` (one-based), without interpolation: **392 for QUIC** and **395 for TCP_TLS**. Calculations use the original recorded values and results are displayed to three decimal places in milliseconds.

## Run provenance and interpretation

There is **one run per transport**, with **different sample counts** (412 versus 415). Treat this comparison as **preliminary**: these are descriptive summaries of two individual runs, not a replicated transport benchmark or evidence establishing a statistically reliable performance difference. No repeated-run uncertainty or causal conclusion is inferred from the difference in means.

This comparison uses the later QUIC source named above. The earlier initial comparison remains unchanged in `quic_vs_tcp_tls_initial.csv` and `quic_vs_tcp_tls_initial.md`; it used `log.quic_demo.20261022191059.quiet.rtt.csv`, which preceded the transport refactor. No firmware edits, build, flashing, or new hardware measurements were performed for this analysis.
