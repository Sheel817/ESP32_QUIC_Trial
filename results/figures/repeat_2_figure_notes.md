# Preliminary application RTT figures: repeat run 2

## Sources and selection

- QUIC: `results/quic_repeat_2.rtt.csv`, 415 selected measurements, from `log.quic_demo.20261024182008.txt`.
- TCP_TLS: `results/tcp_tls_repeat_2.rtt.csv`, 409 selected measurements, from `log.quic_demo.20261025135315.txt`.
- Each CSV contains `esp_log_timestamp_ms,seq,app_rtt_ms` and represents one identified post-reset boot session. Pre-reset sessions are excluded.
- Shared warm-up rule: exclude ESP log timestamps below 60000 ms. Exactly 60000 ms is eligible. Select up to the first 415 eligible measurements in chronological order, breaking ties by raw-log line order.
- QUIC contains the first 415 of 530 eligible measurements. TCP_TLS has only 409 eligible measurements, six fewer than 415. Use all 409; do not impute six values or substitute pre-reset/warm-up records. QUIC is not truncated to equalize counts.
- All selected measurements are plotted, including every outlier. No smoothing, binning, downsampling, or RTT-based filtering is applied.
- QUIC: sequences 11-425, ESP timestamps 63463-2137403 ms. TCP_TLS: sequences 11-419, ESP timestamps 62337-2106377 ms. No duplicate sequences, gaps, or order regressions were found in either selected CSV.

Application RTT is `(receive_time_us - send_time_us) / 1000.0`, from immediately before ESP32 MQTT_Publish to the sequence-matched publication echo callback. It includes application processing and scheduling and differs from transport RTT. Both RTT timestamps use the ESP32 clock. Laptop UTC is not subtracted from ESP uptime. The plotted ESP log timestamp is the APP_RTT log-line uptime, not an inferred send timestamp.

## Figures

- `application_rtt_vs_esp_uptime_repeat_2.png` and `.svg`: scatter plot of every selected measurement against ESP log uptime, converted from milliseconds to seconds. Different colors and marker shapes distinguish transports. Both share uptime and RTT axes; RTT spans 0-400 ms.
- `application_rtt_ecdf_repeat_2.png` and `.svg`: right-continuous ECDF, `F_n(x) = count(RTT <= x) / n`, with a jump of 1/n for each measurement. Both transports share axes and retain the complete 0-400 ms RTT range. Lines differ by color and dash style. ECDF steps use the actual measurements, not histogram bins.
- Counts are shown in both legends. The 367.506 ms TCP_TLS maximum is labelled in both figures. PNGs are exported at 200 dpi (2300 x 1300 pixels); SVGs are vector figures with text labels.

## TCP_TLS maximum and raw-log context

The unique TCP_TLS maximum is **367.506 ms**, **sequence 365**, at ESP log timestamp **1836157 ms** (**1836.157 s**, or 30 min 36.157 s since boot). It appears at **line 584** of `log.quic_demo.20261025135315.txt`.

| Raw-log line | ESP timestamp (ms) | Sequence | Application RTT (ms) |
|---:|---:|---:|---:|
| 582 | 1825797 | 363 | 28.022 |
| 583 | 1830827 | 364 | 47.481 |
| 584 | 1836157 | 365 | 367.506 |
| 585 | 1840887 | 366 | 87.818 |
| 586 | 1845917 | 367 | 107.418 |

The 21 raw-log lines from 574 through 594 (ten lines either side) contain only APP_RTT measurements. All timestamped messages within +/-60 seconds of the maximum also contain only APP_RTT measurements. There is no logged warning, error, reset, reconnect, disconnect, or other event in that neighborhood. Sequence 364 to 365 is separated by 5330 ms in log timestamps, and 365 to 366 by 4730 ms. These are log-line intervals, not evidence of a particular cause. The maximum's cause remains unexplained by this quiet log. Startup Wi-Fi warnings occurred much earlier, below 3400 ms, with no evidence linking them to this point.

This is a descriptive comparison of these two runs, one run per transport, with different sample counts and selected-window durations. It does not establish a causal transport-performance difference or repeated-run uncertainty. Raw logs, input CSVs, and earlier results are unchanged.

## Reproducibility and validation

Both CSVs were checked against the first up-to-415 eligible raw-log records after their single identified reset. Counts, ordering, sequence continuity, finite nonnegative RTTs, and the warm-up cutoff were checked. No rows were removed. Source SHA-256 digests:

- `results/quic_repeat_2.rtt.csv`: `ec589382f4c882dacbf05f106ea65dbae5872dd0bef4f1d1c0778e65b50e3446`.
- `log.quic_demo.20261024182008.txt`: `e373e597a08c6769a0d35047fa1c8fb82deb0a865738185b05371cf4b14f0096`.
- `results/tcp_tls_repeat_2.rtt.csv`: `bf805f3a5bf4abb3d2824b15dbfd58874e340d22db84a3fafb901e9a0bd34cf1`.
- `log.quic_demo.20261025135315.txt`: `ecfd99217ccef3674a77340a7ac19aed6a13b26066099874de0dc87264971b6c`.

Generated with Python 3.12.14, Matplotlib 3.11.2, NumPy 2.5.4. Reproduction script: `build/rtt_comparison/plot_repeat_2.py`; plotting dependencies are isolated under `build/figure_dependencies`.
