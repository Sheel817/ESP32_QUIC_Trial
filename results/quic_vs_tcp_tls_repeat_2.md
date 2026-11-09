# QUIC versus TCP_TLS repeat run 2

| Transport | Samples | Sequence range | ESP timestamp range (ms) | Min (ms) | Mean (ms) | Median (ms) | P95 (ms) | Max (ms) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| QUIC | 415 | 11-425 | 63463-2137403 | 25.096 | 67.710 | 65.605 | 105.811 | 126.811 |
| TCP_TLS | 409 | 11-419 | 62337-2106377 | 26.834 | 70.186 | 67.688 | 107.590 | 367.506 |

## Sources

- **QUIC:** selected CSV `results/quic_repeat_2.rtt.csv` (SHA-256 `ec589382f4c882dacbf05f106ea65dbae5872dd0bef4f1d1c0778e65b50e3446`), from raw log `log.quic_demo.20261024182008.txt`.
- **TCP_TLS:** selected CSV `results/tcp_tls_repeat_2.rtt.csv` (SHA-256 `bf805f3a5bf4abb3d2824b15dbfd58874e340d22db84a3fafb901e9a0bd34cf1`), from raw log `log.quic_demo.20261025135315.txt`.

QUIC uses the existing, unchanged `results/quic_repeat_2.rtt.csv`; its reset/session and selection evidence is in `results/quic_repeat_2_summary.md`. TCP_TLS uses the newly selected data and `results/tcp_tls_repeat_2_summary.md`.

## Shared measurement and sample selection

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, measured on the ESP32 from immediately before MQTT_Publish to delivery of the sequence-matched returned publication on `esp32/quic/test` to the coreMQTT callback, before JSON parsing and console logging. It includes application processing and scheduling and is different from transport RTT. Both timestamps use the ESP32 clock; laptop UTC and ESP32 uptime are not subtracted.

The shared warm-up rule excludes ESP log timestamps below **60000 ms** within the identified post-reset session (exactly 60000 ms is eligible). Records are ordered by ESP log timestamp, with source-line order resolving ties, and up to the first **415** eligible measurements are selected. Outliers and duplicates are not silently removed; no missing records are imputed. Statistics below are recomputed from the selected CSV values, not copied from earlier summaries. Mean is arithmetic; median averages the two middle sorted values when the count is even. P95 uses the one-based nearest rank `ceil(0.95 * n)`, without interpolation. Values are displayed to three decimal places in milliseconds.

The QUIC CSV contains **415** selected measurements (the first 415 of 530 post-warm-up eligible records in its post-reset session). The TCP_TLS CSV contains **409**, because its raw log provides only 409 eligible measurements. All 409 are retained; six measurements are unavailable to reach 415. QUIC is not truncated to force equal counts, and no pre-reset or warm-up TCP_TLS records are substituted. P95 ranks are **395 for QUIC** and **389 for TCP_TLS**.

## Validation and interpretation

The CSVs contain finite nonnegative RTT values, valid uint32 sequence numbers, and timestamps at least 60000 ms. Neither selected CSV has duplicate sequences, internal sequence gaps, sequence regressions, or timestamp regressions: `{"QUIC":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"TCP_TLS":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`.

The TCP_TLS raw log contains one reset and one confirmed new connection; no additional reset/reconnect or connection error is observed. Its 83 pre-reset records and 10 warm-up records are excluded. Three startup Wi-Fi warning lines are recorded in its session summary. The earlier QUIC session summary reports no additional resets/reconnects or connection errors. Outliers, including TCP_TLS's **367.506 ms** maximum, remain in the comparison.

This is a **descriptive comparison of these two runs**, with one selected boot session per transport and **different sample counts (415 versus 409)**. It is not a replicated benchmark, an estimate of repeated-run uncertainty, or a causal conclusion about transport performance. The same 60-second warm-up rule is used, but the selected record windows have different durations. Source logs and all earlier result files are preserved.
