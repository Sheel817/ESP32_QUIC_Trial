# HBPSN-04 TCP_TLS CONTROL — finalized data, validity pending

Automatic finalization succeeded against the original **6November2026,04:01:38.681783–04:38:38.681783 Helsinki** window (UTC02:01:38.681783–02:38:38.681783), exactly2220 monotonic seconds. Cutoff observed7.7674ms late; raw line admission still uses the original monotonic interval. No later measurements were included. Processing finished02:39:09.078928UTC after the30-second evidence wait. That wait is implementation behavior, not a frozen-plan lateness cutoff.

## Actual post-recording image

[Actual screenshot](./HBPSN-04_Clumsy_POST_RECORDING.jpg) acquired **2026-11-06T02:41:43.336Z–2026-11-06T02:41:44.503Z**, Helsinki04:41:43.336–04:41:44.503. SHA256 **2d1a62515d045b781bb2f52902016322374aa430741155153c622289823639cf**. Capture started **184.654217seconds after the deadline**; actual lateness retained, not backdated.

Visible exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture running (Stop button and Started filtering), Lag/Drop/Throttle/Duplicate/Out of order/Tamper/Set TCP RST/Bandwidth all disabled. Saved inactive Lag100ms, Drop1%, outbound checked and inbound unchecked remain inactive. These match the [pre-reset screenshot](../clumsy_actual_pre_reset.jpg), captured 2026-11-06T02:01:16.400Z–2026-11-06T02:01:16.620Z, SHA256 `4f5e08d2b340b318c6a573edea87024357e797b7a2ee98134206201904390ed7`. No settings changed by the agent. Screenshot matching alone cannot establish continuous stability.

## Counts and selected statistics

- Raw serial lines581; parsed RTT records441.
- Warm-up excluded10; other exclusions0; eligible431.
- Selected415; eligible extras16; shortfall0. All outliers retained.
- Selected sequences11–425, ESP62367–2136487ms. First415 eligible rows match source arrival order exactly; every parsed RTT receipt lies within the original host window.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | 26.927 |
| Mean | 69.455561 |
| Median | 67.507 |
| Nearest-rank P95 | 107.536 |
| Maximum | 248.069 |

Recomputed from the actual [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [byte receipts](../serial_receipts.jsonl).

## Errors, resets and limitations

No post-start reboot, sequence gap, serial connection error, collector interruption or server-tail failure was recorded. One initial designated reset is present. Three Wi-Fi warnings are retained in [verification](./POST_RECORDING_VERIFICATION.json). The raw prefix includes buffered setup-boot text and a truncated coexist line joined to the initial ESP-ROM banner at the reset boundary; these bytes are preserved, not interpreted as an additional measured reboot. No affected RTT eligibility was detected.

One NEW **unattributed server error** `TCP+TLS ERROR:` (empty exception text) was received **02:02:37.577340UTC**, source bytes160–177, and retained in [server stderr](../server.stderr.raw.log) with its [receipt](../server.stderr.receipts.jsonl). Its cause/peer are unknown; it is not silently discarded or declared harmless. Historical probe errors occupy bytes0–160 and remain separate. The automatic serial connection_error_count0 does not include this one server error.

## Pending review and preservation

Automatic flags remain **FAILED_SETTINGS / MISSING end image** in the original finalizer files. This actual late image is separate supplementary evidence; those flags were not overwritten. Overall validity stays **NOT_APPROVED / PENDING_OPERATOR_AND_MANUAL_REVIEW**. Exact operator statement requested covering run start through screenshot completion; answer not yet received. This report does not classify the run valid. The new unattributed server error also requires review under the original criteria.

Both registers still have HBPSN-04 RUNNING because automatic finalization emitted a patch without applying it. No register was modified in this review. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with flags and HBPSN-03 FAILED_STARTUP preserved; QUIC crash unresolved.

All 71 original final-manifest entries matched their saved SHA256 hashes. [Source hashes](./source_hashes.json) cover original raw/CSV/statistics/finalization evidence. [Detailed verification](./POST_RECORDING_VERIFICATION.json). Existing monitor/server continue; no new run, reset, flash, build or settings change occurred.
