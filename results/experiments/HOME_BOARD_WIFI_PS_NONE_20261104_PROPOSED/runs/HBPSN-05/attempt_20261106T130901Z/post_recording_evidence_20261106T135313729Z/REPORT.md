# HBPSN-05 QUIC LAG100_OUT — finalized data, validity pending

Automatic finalization succeeded using the original **6November2026,15:13:20.156359–15:50:20.156359 Helsinki** window, UTC13:13:20.156359–13:50:20.156359, exactly2220monotonic seconds. No later measurement included. Cutoff observed5.3929ms late; admission still used the original fixed interval. Finalization finished13:50:50.594842UTC after the30-second evidence-response wait, not an extended data window.

## Actual post-recording image

[Image](./HBPSN-05_Clumsy_POST_RECORDING.jpg) captured **2026-11-06T13:53:13.729Z–2026-11-06T13:53:14.719Z**, Helsinki15:53:13.729–15:53:14.719. SHA256 **8ae304cd0655008f48067051582d78093de8bc7ebd6dd40637ffa8b0e0f04090**. Actual acquisition began **173.572641seconds after the deadline**. Delay retained, not backdated. The original plan has no numeric screenshot cutoff; the collector30-second wait is not a frozen cutoff.

Exact filter `udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)`; capture running; only Lag enabled100ms, Outbound checked, Inbound unchecked. Drop, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth disabled. Visible settings match the [pre-reset image](../clumsy_actual_pre_reset.jpg), captured 2026-11-06T13:13:01.204Z–2026-11-06T13:13:01.560Z, SHA256 `27a74e61624f5dd59798b32bcaf76fd6af1014b32a7e568562b3fc98107ff0ff`. Screenshot matching does not establish continuous stability; no settings were changed by the agent.

## Counts and selected statistics

Raw serial lines591; raw RTT records441; warm-up excluded10; other exclusions0; eligible431; selected415; extra eligible16; shortfall0. First415 eligible rows match source arrival order. Selected sequences11–425, ESP63973–2138133ms. All values/outliers retained.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | 125.069 |
| Mean | 190.899824 |
| Median | 185.994 |
| Nearest-rank P95 | 245.685 |
| Maximum | 525.973 |

Recomputed from [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [receipt index](../serial_receipts.jsonl).

## Errors, resets and evidence review

No serial connection error, server stderr error, sequence gap, interruption or server-tail failure recorded. One initial designated boot; no subsequent reboot. Three Wi-Fi warnings remain verbatim in [verification](./POST_RECORDING_VERIFICATION.json): password/authmode threshold, trace band/rate and ba-add. Earlier HBPSN-03 QUIC crash remains unresolved; this completed boot does not establish a fix.

Original automatic **FAILED_SETTINGS / MISSING end-image** flags preserved. The actual late image is supplementary evidence, not a rewrite of automatic files. Overall validity stays **NOT_APPROVED / PENDING_OPERATOR_AND_MANUAL_REVIEW**. Exact settings/capture stability confirmation requested from measured start through screenshot completion; no answer has yet been received or invented. No register change was made here. Its HBPSN-05 row still says RUNNING because automatic finalization only emits an unapplied update request; processing has finished.

All71 original final-manifest hashes verified. [Source hashes](./source_hashes.json), [verification](./POST_RECORDING_VERIFICATION.json), [original finalizer](../FINALIZED.json), [settings request status](../post_recording_settings_check.json). Raw originals preserved; no new run, reset, flash, build, process or settings change occurred.
