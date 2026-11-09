# HBPSN-06 TCP_TLS DROP1_OUT — finalized data, validity pending

Automatic finalization succeeded using the original **7November2026,04:04:34.926538–04:41:34.926538 Helsinki** window, UTC02:04:34.926538–02:41:34.926538, exactly2220monotonic seconds. No later measurement included. Cutoff observed13.7356ms late; all RTT receipts meet the original host window. Finalization finished02:42:05.547268UTC after evidence-response waiting, not an extended data window.

## Actual post-recording image

[Image](./HBPSN-06_Clumsy_POST_RECORDING.jpg) captured **2026-11-07T02:50:57.056Z–2026-11-07T02:50:58.162Z**, Helsinki04:50:57.056–04:50:58.162. SHA256 **72fa510983f6c4a416344bd85323ad9d9a076760741dd7b7706e7058ac8de36a**. Actual acquisition began **562.129462seconds after the deadline**. Delay retained, not backdated. The original plan has no numeric screenshot cutoff; collector30-second wait is not a frozen cutoff.

Exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`; capture running; only Drop enabled, configured Chance1.0%, Outbound checked, Inbound unchecked. Lag, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth disabled. Matches [pre-reset image](../clumsy_actual_pre_reset.jpg), captured 2026-11-07T02:04:16.789Z–2026-11-07T02:04:17.245Z, SHA256 `17f84edf6e5cea5a666890cde386dcd0d61cf3077aa222ed6a7c9a2775aa4f29`. No agent settings change. Matching endpoint images do not establish continuous stability. Configured1%Drop is not measured packet/message loss.

## Counts and selected statistics

Raw serial lines581; raw RTTs441; warm-up excluded10; other exclusions0; eligible431; selected415; extra eligible16; shortfall0. Selected sequences11–425, ESP62357–2136477ms; exact first415 eligible records in source order. Every value/outlier retained.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | 26.789 |
| Mean | 77.024414 |
| Median | 67.432 |
| Nearest-rank P95 | 108.204 |
| Maximum | 627.418 |

Recomputed from [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [receipts](../serial_receipts.jsonl).

## Errors, resets and limitations

No serial connection error, sequence gap, interruption or server-tail failure. One initial designated reset; no subsequent reboot. Three Wi-Fi warnings retained verbatim in [verification](./POST_RECORDING_VERIFICATION.json).

One NEW unattributed server error **`TCP+TLS ERROR:`** (empty exception text) was received **02:05:32.162784UTC**, source bytes194–211. [Raw server stderr](../server.stderr.raw.log), [receipt ledger](../server.stderr.receipts.jsonl). Cause/peer unknown; no silent discard or harmless classification. Original automatic serial-only connection_error_count0 excludes this separate server error. Older/probe-associated stderr bytes0–194 remain historical and excluded from this run's fresh tail. The server prints no traceback for this line, so none is available.

## Pending review and preservation

Original automatic **FAILED_SETTINGS / MISSING end-image** flags preserved intact. This actual late image is separate supplementary evidence. Overall validity remains **NOT_APPROVED / PENDING_NEW_HBPSN06_OPERATOR_AND_MANUAL_REVIEW**. A new HBPSN-06-specific confirmation covering run start through screenshot completion was requested; earlier runs' confirmations are not reused. No answer or receipt timestamp has been invented.

No register update made. HBPSN-06's row remains RUNNING because the finalizer only emits a patch; data processing is FINALIZED. Earlier outcomes unchanged; QUIC crash remains unresolved. All81 original final-manifest hashes verified. [Source hashes](./source_hashes.json), [verification](./POST_RECORDING_VERIFICATION.json), [original finalizer](../FINALIZED.json). Existing server/monitor left running; no new run, reset, flash, build or settings change.
