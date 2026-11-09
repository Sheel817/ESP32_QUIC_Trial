# HBPSN-02 finalized data with post-recording image, review pending

HOME_BOARD, TCP_TLS, WIFI_PS_NONE, LAG100_OUT. **Data processing FINALIZED. Validity NOT_APPROVED / PENDING_EVIDENCE_REVIEW. Operator stability confirmation PENDING.** Register status is FAILED_SETTINGS, preserving the original automatic missing-image flag; this report does not approve validity or retroactively erase that flag.

## Actual screenshot captured first

Before data analysis in this request and before any settings changes by the agent, an actual [Clumsy screenshot](./HBPSN-02_Clumsy_POST_RECORDING.jpg) was captured **2026-11-04T13:12:42.221Z–2026-11-04T13:12:42.694Z**, then the original JPEG bytes were saved and SHA-256 independently verified:

`7bc9f9b58ecd6adb835907f52cc500045181a4ce8c9f3f2d308d78b960fd553b`

This is an image, not a request. It was captured **1094.940958 seconds** (18 minutes 14.940958 seconds) after the fixed deadline; it is not backdated. The image metadata records actual acquisition and save times. No statement is invented about operator actions before this request.

Visible states match the actual [pre-reset image](../clumsy_actual_pre_reset.jpg), acquired 2026-11-04T12:17:11.463Z–2026-11-04T12:17:11.943Z (SHA-256 `338fe985dccaca6cd3e03b6b9cdaa51ed000636424438bca2ea4b8d1a08af829`):

- Filter exactly `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`.
- Capture running, Stop button visible.
- Lag checked, Delay 100 ms, Inbound unchecked, Outbound checked.
- Drop, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth all unchecked.

[Comparison with exact paths/hashes](./post_vs_pre_comparison.json). Matching endpoint screenshots do not prove continuous stability. Post-image and operator-confirmation review remain pending.

## Original fixed recording and automatic finalization

**4 November 2026, 14:17:27.280042–14:54:27.280042 Helsinki (UTC+02)**; UTC 12:17:27.280042–12:54:27.280042. Exactly **2,220 host-monotonic seconds** from the designated reset-release API completion; no extension and no later measurements included. Host API return is the anchor, not a measured electrical edge. ESP log timestamp defines eligibility.

The repaired deadline worker fired at 12:54:27.286055 UTC, about 6.0571 ms after its target. This scheduler latency did not change the inclusion cutoff. It requested a post image and waited its configured 30 seconds. No actual image arrived in that wait, so the original [automatic missing-evidence check](../post_recording_settings_check.json) remains MISSING and [automatic finalization](../FINALIZED.json) at 2026-11-04T12:54:57.640902+00:00 remains FAILED_SETTINGS / NOT_APPROVED / PENDING_MANUAL_REVIEW. That **30-second wait is an implementation timeout, not a frozen-plan numerical post-image deadline**. Today's actual image is added separately; the original marker, statistics, check, manifest and logs remain unchanged for review.

All raw serial/server receipt timestamps lie inside the original fixed interval; indexes are byte-contiguous and each raw line matches its source bytes. Serial [raw](../serial.raw.log), [receipt index](../serial_receipts.jsonl), [integrity checks](./fixed_window_integrity.json). Live monitor output after cutoff remains separate and was not added to the selected data. Server stdout, stderr and sensor tails independently closed at cutoff with source end offsets recorded.

## Counts, selection and RTT statistics

| Count | Records |
|---|---:|
| Raw serial lines | 580 |
| Raw numeric APP_RTT | 441 |
| Warm-up excluded, uptime below60,000ms | 10 |
| Other numeric exclusions | 0 |
| Eligible | 431 |
| Selected first eligible | 415 |
| Extra eligible retained | 16 |
| Shortfall | 0 |

Selected sequences **11–425**, source lines150–564, ESP timestamps **62,847–2,136,967 ms**, host receipt UTC **12:18:30.144005–12:53:04.241594** (Helsinki14:18:30.144005–14:53:04.241594). The entire raw series is sequences1–441; warm-up1–10; extras426–441. First415 selected in original arrival order. Outliers, including maximum867.649ms, are retained; no trimming, substitution or later-window fill.

| Selected APP_RTT statistic | ms |
|---|---:|
| Minimum | 127.227 |
| Mean | 188.9541108434 |
| Median | 187.392 |
| Nearest-rank P95 | 248.170 |
| Maximum | 867.649 |

P95 is ascending sorted observation rank ceil(0.95 ×415)=**395**, without interpolation. Independent Decimal-based recalculation from actual selected CSV agrees with the automatic statistics to recorded precision. [Verified statistics and first/last records](./verified_statistics.json).

## Errors, gaps and limitations

- **0 additional resets**, 0 timestamp regressions, 0 sequence gaps/repeats, 0 unparsed APP_RTT lines, 0 serial connection-error lines, no recorded monitor/server-tail interruption.
- Three startup Wi-Fi warnings retained: WPA2 threshold adjustment, rate-table trace and BA-add trace. No serial E-level error lines were found.
- **One NEW server line `TCP+TLS ERROR: `**, host-received at **12:18:22.468737 UTC** (Helsinki14:18:22.468737). It occupies original source bytes[51,68), inside the measured window. It has no timestamp, error detail, peer or session ID of its own; the receipt gives host arrival time, not a proved event time. It cannot conclusively be attributed to the measured ESP connection. This new line is retained and counted separately from zero serial connection errors. Three historical bare errors before source byte51 remain excluded from this run.
- Two real heartbeat replacement WinError5 events occurred at12:23:58.313678 and12:51:24.586378 UTC, both first-attempt failures with no retry exhaustion. The repaired writer recovered; the deadline and finalizer completed. Original [error journal](../reporting_errors.jsonl) remains intact.
- 441 matching sensor records, sequences1–441, zero nonzero sensor_error values. This does not prove a packet-level impairment rate or exact +100ms effect.

[Complete error/warning evidence](./errors_and_warnings.json), [new server stderr](../server.stderr.raw.log), [stderr receipt index](../server.stderr.receipts.jsonl). A gap-free RTT sequence does not establish an error-free server or uninterrupted GUI settings. Operator stability confirmation remains necessary.

## Files and register state

- [All441 RTTs](../all_rtts.csv), [warm-up exclusions](../excluded_rtts.csv), [all431 eligible](../eligible_rtts.csv), [selected415](../selected_first_415.csv), [extra16](../eligible_extra.csv).
- [Serial raw](../serial.raw.log), [server stdout raw](../server.stdout.raw.log), [server stderr raw](../server.stderr.raw.log), [sensor CSV raw tail](../server.sensor_csv.raw.log), [parsed sensor records](../server_sensor_records.csv).
- [Reset/start/source boundaries](../reset_event.json), [startup verification](../startup_checks.json), [runtime version hashes](../collector_version.json), [firmware/configuration provenance](../preflight.json).
- [Original automatic statistics](../statistics.json), [automatic finalization preserved](./automatic_finalization_preserved.json), [all original finalization hashes before this review](./original_finalization_hashes.json), [review/output/register hashes](./SHA256SUMS.json).

CSV and XLSX register entries were synchronized for **HBPSN-02 only**: FAILED_SETTINGS (the existing automatic missing-image flag), fixed duration2220, eligible431/selected415/shortfall0, RTT statistics, and one new unattributed server error explicitly distinguished from zero serial errors. Review remains pending, validity NOT_APPROVED. The former RUNNING state is no longer stale. The machine's original register request counted serial errors only; the reviewed bookkeeping now includes the separately retained server error without changing the original request or statistics.

HBPSN-01 remains FAILED_SETTINGS, its original files remain hash-identical, and every other CSV row is byte-identical to the pre-update register; workbook guards checked other rows unchanged. The frozen plan/order remain unchanged; no next run started. [Register update receipt](./register_final_review_update.json), [preservation verification](./final_preservation_verification.json).

No Clumsy settings, firmware, board reset, server or monitor settings were changed by this review. The current server and monitor remain running. Keep actual settings-stability claims unconfirmed until the operator statement is supplied and reviewed.
