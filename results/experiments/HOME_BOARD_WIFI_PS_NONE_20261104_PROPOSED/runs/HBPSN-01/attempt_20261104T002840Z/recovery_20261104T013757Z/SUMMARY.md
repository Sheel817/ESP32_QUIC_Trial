# HBPSN-01 final recovered result

HOME_BOARD, QUIC, WIFI_PS_NONE, CONTROL. UDP 14567 capture running, all effects off: operator-reported and observed in preflight GUI. No post-recording settings check was saved.

**Final register status: FAILED_SETTINGS. Recording status: RECOVERED_FIXED_WINDOW.** The complete 37-minute data window was recovered, but the required contemporaneous post-recording settings evidence is missing. This is an evidence limitation, not a finding that settings changed. Startup checks passed. No replacement run was made.

## Original fixed window

4 November 2026, **02:38:26.327–03:15:26.327 Helsinki (UTC+02)**. UTC 00:38:26.327–01:15:26.327. Original stored reset-release anchor is 00:38:26.326642+00:00, deadline 01:15:26.326642+00:00; the displayed millisecond times are rounded. Selection uses these original full-precision anchors and host-monotonic interval [507017.5434011, 509237.5434011), exactly 2,220 seconds. The reset anchor is host reset-API completion rather than a measured electrical edge.

## Automatic finalization and recovery

Automatic finalization **failed** at 00:46:45.650030 UTC (02:46:45.650 Helsinki). Windows raised WinError 5 Access denied replacing heartbeat.json.tmp with heartbeat.json. The original [failure traceback](../collector_failure.json) remains untouched; a [preserved copy](./collector_failure_preserved.json) and its hash are retained here. No automatic COMPLETE or final statistics existed. The main loop stopped, while the independent serial/server reader threads continued gating by the original monotonic deadline.

Offline recovery checked every raw line against its receipt, contiguous byte offsets, original UTC/monotonic window, and corresponding bytes in the live source logs. All checks passed. Server tails closed at 01:15:26.327186 and 01:15:26.327014 UTC. Serial recording ends at the last received line before cutoff, 01:15:24.292193 UTC; later live-monitor lines are not included. The fixed serial log remains immutable. Live source interval hashes identify the relevant bytes without hashing later appended data.

## Counts and selection

| Item | Count |
|---|---:|
| Raw serial lines | 591 |
| Raw numeric APP_RTT records | 441 |
| Warm-up excluded (ESP log uptime <60,000 ms) | 10 |
| Other excluded numeric records | 0 |
| Eligible within initial boot/window | 431 |
| Selected first eligible records | 415 |
| Extra eligible records retained outside primary subset | 16 |
| Shortfall | 0 |

All 441 numeric RTTs are sequences 1–441. Selected sequences are **11–425**, ESP log uptime **63,653–2,137,793 ms**. Selected host receipts are **00:39:29.994180–01:14:04.114527 UTC**, or **02:39:29.994180–03:14:04.114527 Helsinki**. Raw source lines 161–575. All numeric outliers remain in their original arrival order. Every eligible value, including the 16 extras (426–441), is preserved.

| Selected APP_RTT statistic | ms |
|---|---:|
| Minimum | 24.671 |
| Mean | 67.5400265060 |
| Median | 65.552 |
| Nearest-rank P95 | 105.842 |
| Maximum | 165.999 |

P95 is ascending sorted observation rank ceil(0.95 × 415) = **395**, with no interpolation. RTTs have the firmware's printed precision; no censoring or trimming was applied.

## Resets, errors and limitations

One designated startup; **0 additional resets**, **0 timestamp regressions**, **0 sequence gaps/repeats**, **0 unparsed APP_RTT lines**, and **0 logged connection errors**. Three startup Wi-Fi warning lines are retained in the [warning ledger](./warning_error_ledger.csv): WPA2 authentication-threshold adjustment, rate-table trace, and BA-add trace. No serial E-level lines were found. Server stderr is empty; server stdout has 0 error/warning/disconnect pattern matches. Server sensor CSV has 441 records, sequences 1–441, with 0 nonzero sensor errors. This corroborates matching sequences; receipt timing is not a network packet capture or independent impairment measurement.

The recorder supervisor's heartbeat failed during the run, so its later periodic liveness checks and automatic finalizer did not execute. Continuous sequence and byte receipt evidence shows no observed recording interruption; it cannot establish absence of every unlogged external event. Required post-recording GUI/settings evidence is missing. Preflight verified the frozen QUIC UDP filter and all effects unchecked; this does not establish per-packet effect state throughout the session. The monitor and server were left running; recovery performed no reset, build, flash, ping or settings change.

## Files, provenance and register

- [Original serial recording](../serial.raw.log), [serial receipt index](../serial_receipts.jsonl), [server stdout](../server.stdout.raw.log), [server stderr](../server.stderr.raw.log).
- [All RTTs](./all_rtts.csv), [warm-up exclusions](./excluded_rtts.csv), [eligible RTTs](./eligible_rtts.csv), [selected first 415](./selected_first_415.csv), [extra eligible RTTs](./eligible_extra.csv), [server sensor records](./server_sensor_records.csv).
- [Statistics](./statistics.json), [provenance and firmware/configuration hashes](./provenance.json), [byte/receipt integrity checks](./integrity_checks.json), [final verification](./final_verification.json), [source SHA-256](./source_hashes.json), [output and register SHA-256 manifest](./SHA256SUMS.json).
- [Run register CSV](../../../../run_register.csv) and [run register workbook](../../../../../../../outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx): only HBPSN-01 updated from RUNNING to FAILED_SETTINGS, with fixed deadline, counts, statistics and recovery path. Other 17 entries remain NOT_RUN and unchanged. [Update receipt](./register_final_update.json). Pre-recovery register copies retained here.
- Frozen plan SHA-256 `6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be`; freeze manifest SHA-256 `e37bf26c0701ab185ae2e03b1cd5e0c6e9f0f89a1abef5c50deafed6c385a60e`. Both unchanged. Earlier failed preflight report remains preserved outside the successful attempt.

Recovered at 2026-11-04T01:37:57.063869+00:00. No later measurements included and no recording extension made.
