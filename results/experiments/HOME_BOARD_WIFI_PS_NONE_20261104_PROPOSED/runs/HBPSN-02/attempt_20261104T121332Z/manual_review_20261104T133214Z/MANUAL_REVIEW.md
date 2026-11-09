# HBPSN-02 manual review under original frozen criteria

Decision: **COMPLETE, with retained flags**. Validity **APPROVED_UNDER_ORIGINAL_FROZEN_PLAN**. Review UTC: **2026-11-04T13:34:30.397217+00:00**. This separate manual decision supersedes the working register's provisional FAILED_SETTINGS entry; it does not rewrite the original automatic decision, raw measurements, earlier reviews, snapshots or frozen plan.

## Operator statement: exact words, actual receipt and coverage

> setting stayed unchanged

Receipt observed UTC: **2026-11-04T13:31:19.1952412Z**, the first real UTC clock observation while processing this user message. Platform chat-ingress time is not exposed; it is not invented. Statement saved UTC: **2026-11-04T13:32:14.758129+00:00**. These receipt/save times are later than the run and are not backdated.

The user's explicit clarification confirms no Clumsy filter/effect/capture changes or close/reopen from **2026-11-04T12:17:27.280042+00:00 through 2026-11-04T13:12:42.694Z**, covering the measured start, whole recording and interval until the actual post-image completed. Evidence type: **operator-reported stability**, not independently monitored continuous GUI state or packet-level verification. [Exact statement record](./operator_statement.json).

## Original settings criteria and image verification

The unchanged [frozen plan](../../../../EXPERIMENT_PLAN_PROPOSED_V1.md) says:

> Save screenshots before reset and after recording, with UTC and hashes.

> Settings must be stable before the measured reset and throughout the 37 minutes.

| Actual image | Capture UTC | SHA-256 |
|---|---|---|
| [Pre-reset](../clumsy_actual_pre_reset.jpg) | 12:17:11.463–12:17:11.943 | `338fe985dccaca6cd3e03b6b9cdaa51ed000636424438bca2ea4b8d1a08af829` |
| [Post-recording](../post_recording_evidence_20261104T131242221Z/HBPSN-02_Clumsy_POST_RECORDING.jpg) | 13:12:42.221–13:12:42.694 | `7bc9f9b58ecd6adb835907f52cc500045181a4ce8c9f3f2d308d78b960fd553b` |

Both original images were opened and visually reviewed again, and their current SHA-256 hashes match their capture records. Pre-image precedes designated reset12:17:27.280042; post-image follows fixed deadline12:54:27.280042. Both show exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture running, Lag checked100ms, Inbound unchecked, Outbound checked, and Drop/Throttle/Duplicate/Out of order/Tamper/Set TCP RST/Bandwidth unchecked. The operator statement supplies the intervening stability confirmation; matching images alone do not.

Post-image acquisition began **1094.940958 seconds (18 minutes14.940958 seconds)** after the deadline. This remains explicitly recorded. The frozen plan gives no numerical maximum post-image delay. The collector's30-second response wait is an implementation timeout, not a frozen acceptance rule. That original MISSING/FAILED_SETTINGS output remains preserved; the actual later image and retrospective statement are reviewed using the original rule, without backdating either.

Clumsy0.3 is visible in both images. Current executable hash/process metadata, observed at manual-review time, are saved separately as supplementary context and are not falsely labelled as a pre-reset binary-hash observation. Startup serial evidence includes SSID/BSSID, channel11, RSSI-31, AP beacon102400us and DTIM1. Host-load/background-traffic detail was not continuously instrumented; no per-packet impairment proof is claimed.

## New TCP error: retained, cause unknown, assessed by the frozen rule

The plan explicitly says:

> If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.

It separately requires a failed/interrupted run for reboot; none is recorded here. One NEW bare `TCP+TLS ERROR: ` line was host-received at **12:18:22.468737 UTC** within the fixed window, original source bytes[51,68). It lacks a peer/session ID and useful error detail. Its cause, responsible peer and true emission time cannot be inferred; no setup-connection or harmlessness explanation is asserted. It is retained and flagged, with register connection_error_count=1. Three historical errors before byte51 remain separate. There are zero serial connection-error lines and no observed reboot, sequence gap or interruption. The existing rule permits completion while retaining/flagging connection errors without reboot and reporting the actual shortfall, which is zero. No stricter automatic rejection rule is invented, and the error is not discarded to achieve COMPLETE.

## Other criteria and preserved measurements

Prepared BIN/ELF/bootloader/partition/configuration hashes still match preflight and the frozen firmware profile. HOME_BOARD identity, ELF digest prefix, WIFI_PS_NONE requested/returned0, TCP_TLS/MQTT/subscription, TLS1.3 AES128GCM suite1301 ALPNmqtt certificate modeNONE and TCP_NODELAY1 passed in the designated measured startup. The preflight/runtime/flash/reset records remain unchanged.

Fixed window **4 November2026, 14:17:27.280042–14:54:27.280042 Helsinki (UTC+02)**, exactly2220 monotonic seconds. Independent byte/receipt checks show raw data confined to the original window. Automatic finalization completed; no data after cutoff was added. Raw APP_RTT441; warm-up excluded10; eligible431; selected first415; extras16; shortfall0. Selected sequences11–425, ESP timestamps62847–2136967ms, with all outliers retained. No additional resets, regressions, gaps/repeats or malformed RTTs. Mean188.9541108434ms, min127.227, median187.392, nearest-rank P95248.170 (rank395), max867.649. Existing CSVs were read/verified, never rewritten.

Flags remain: post-image lateness, operator-reported continuity, one unattributed server error, three startup Wi-Fi warnings, and two real heartbeat replacement failures that recovered without retry exhaustion. The late-image automatic flags, original finalizer statistics and all earlier register snapshots remain in place. [Machine-readable manual review and full evidence references](./manual_review.json), [protected original evidence hashes](./protected_evidence_hashes.json), [before-review CSV](./register_before_manual_review.csv), [before-review XLSX](./register_before_manual_review.xlsx). Approval means the original completion/settings criteria are satisfied with these flags; it is not a clean/error-free label or a claim of exactly100ms added RTT.

## Register decision and next run

Only HBPSN-02's row is to change to existing permitted status **COMPLETE**, with updated evidence type, authoritative manual-review path and explicit flags. Counts, RTT values and error count remain unchanged. HBPSN-01 remains FAILED_SETTINGS, all other rows/order and the frozen plan remain unchanged. Application and preservation checks are documented separately after export.

Next scheduled run: **HBPSN-03 — QUIC — DROP1_OUT**, currently NOT_RUN. No replacement or new run is authorized or started by this review. No firmware/settings/device changes occurred.

Register application completed at 2026-11-04T13:35:05.991Z. Both registers now show HBPSN-02 COMPLETE. Only status, settings_evidence_type, metadata_path and deviation_reason changed. Numeric measurements, counts and error count are unchanged. [Application receipt](./register_manual_review_update.json), [preservation verification](./preservation_and_register_verification.json), [SHA-256 manifest](./SHA256SUMS.json).
