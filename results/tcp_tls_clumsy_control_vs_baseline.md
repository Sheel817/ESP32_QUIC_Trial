# TCP_TLS Clumsy control versus baseline

| Condition | Samples | Sequence range | ESP timestamp range (ms) | Min (ms) | Mean (ms) | Median (ms) | P95 (ms) | Max (ms) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| TCP_TLS_baseline | 409 | 11-419 | 62337-2106377 | 26.834 | 70.186 | 67.688 | 107.590 | 367.506 |
| TCP_TLS_clumsy_control | 395 | 11-405 | 62347-2036267 | 26.484 | 70.341 | 67.832 | 108.576 | 147.555 |

## Sources and intended condition

- **TCP_TLS_baseline:** `results/tcp_tls_repeat_2.rtt.csv`, SHA-256 `bf805f3a5bf4abb3d2824b15dbfd58874e340d22db84a3fafb901e9a0bd34cf1`, from raw log `log.quic_demo.20261025135315.txt`.
- **TCP_TLS_clumsy_control:** `results/tcp_tls_clumsy_control_1.rtt.csv`, SHA-256 `c719ba700129400b9934625bc5ced7d8acb6e0464c3335fd9b877b6a6bf3876a`, from raw log `log.quic_demo.20261025164836.txt`.

Intended condition, supplied by the user: **Clumsy capture enabled, all impairment functions disabled**. These are manually configured conditions, not settings verified by the ESP log. No Clumsy configuration capture or independent host-side verification is available in this analysis. The earlier TCP_TLS repeat-2 run is the comparison baseline; its host-side Clumsy state is not independently established here.

## Measurement and sample selection

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, from immediately before ESP32 MQTT_Publish to delivery of the sequence-matched returned publication to the MQTT callback, before JSON parsing and console logging. It includes application processing and scheduling and differs from transport RTT. Both timestamps use the ESP32 clock; laptop UTC is not subtracted from ESP uptime.

Use only the identified post-reset TCP_TLS session. Exclude pre-reset records and ESP log timestamps below **60000 ms** (exactly 60000 ms is eligible). Order by ESP log timestamp, with raw-log line order resolving ties; select up to the first **415** eligible records. Retain every outlier and do not silently deduplicate, impute, or substitute records. Mean is arithmetic; median is the middle value (or mean of the middle pair). Nearest-rank P95 is sorted value `ceil(0.95 * n)`, without interpolation. Statistics are recomputed from each selected CSV and displayed to three decimal places in milliseconds.

Use **all selected CSV records**: baseline **409** and control **395**. Both use the same 60-second warm-up rule. The baseline has 409 eligible records (six short of 415); this control has 395 (20 short of 415). Neither set is truncated to equalize counts, and no missing values are filled. Baseline sequences 11-419 span 62337-2106377 ms; control sequences 11-405 span 62347-2036267 ms. P95 ranks are 389 and 376, respectively.

## Observed differences

| Metric | Control minus baseline (ms) |
|---|---:|
| minimum_ms | -0.350 |
| mean_ms | +0.155 |
| median_ms | +0.144 |
| p95_ms | +0.986 |
| maximum_ms | -219.951 |

The signed differences above use unrounded CSV-derived statistics. This is a **descriptive comparison of one run per condition**, with unequal sample counts and observation windows. The observed mean, median, and P95 changes and the different maxima describe these records only. All outliers remain, including the baseline's 367.506 ms maximum. No repeated-run variability or causal effect is estimated. Differences cannot be attributed solely to Clumsy: its settings are manually reported, the log does not verify them, and run-to-run network/application conditions may differ.

## Validation

Both CSVs contain finite nonnegative RTTs, uint32 sequences, and timestamps at least 60000 ms. Checks recomputed from each CSV: `{"TCP_TLS_baseline":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]},"TCP_TLS_clumsy_control":{"duplicates":[],"gaps":[],"sequenceRegressions":[],"timestampRegressions":[]}}`.

No duplicate sequences, internal sequence gaps, or sequence/timestamp regressions were found within the post-reset session, eligible records, or selected records. No additional reset or reconnect, error-level ESP message, connection/handshake failure, disconnect, assertion, crash, or Task stopped message was found after reset. Connection/error candidates: 0. The log ends at sequence 405; it does not establish why capture ended. The shortfall is not an internal sequence gap.

This control excludes 165 pre-reset and 10 warm-up records; the selected session's TCP_TLS identity is explicit. No boot sessions are combined. The three control startup Wi-Fi warnings are documented in `tcp_tls_clumsy_control_1_summary.md`. Baseline session evidence remains in `tcp_tls_repeat_2_summary.md`. Raw logs, baseline CSV, figure files, and all earlier results remain unchanged.
