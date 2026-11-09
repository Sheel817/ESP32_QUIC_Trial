# Recorder repair and TEST_ONLY evidence

## Frozen rule and HBPSN-01 review status

The unchanged [frozen plan](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md), line 30, says exactly:

> Save screenshots before reset and after recording, with UTC and hashes.

Line 32 says exactly:

> There is no impairment ramp or mid-run toggle. Settings must be stable before the measured reset and throughout the 37 minutes. For the next condition, finish/close the previous recording, configure/check the next setting, then begin the next boot session. Do not reset within a run to improve results.

Line 91 says:

> Keep missing fields blank with a reason, never populated with invented zeroes or assumed passes.

The plan specifies before reset / after recording and stability throughout the run. **It does not specify a numerical maximum post-recording screenshot delay or say a screenshot must occur at the exact deadline.** A stricter numerical rule must not be inferred or silently frozen now. HBPSN-01 remains **FAILED_SETTINGS**, unchanged pending review because its required original post-recording screenshot/check was not saved. No current screenshot is backdated or used to upgrade its status. Current screenshots are actual TEST_ONLY evidence and, relative to HBPSN-01, late supplementary observations only.

## Preservation and investigation

Original [collector](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/runs/HBPSN-01/attempt_20261104T002840Z/collector.py) and [traceback](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/runs/HBPSN-01/attempt_20261104T002840Z/collector_failure.json) remain untouched; exact copies plus heartbeat target/temp snapshots and original reset wrapper are in [preserved failure](./preserved_failure/). All 73 protected original files, including plan, freeze manifest and CSV/XLSX registers, passed before/after SHA-256 checks. Live monitor/server logs keep growing; their existing recording boundary is not rewritten.

The heartbeat temporary file was successfully written; Path.replace/os.replace of that file onto the existing heartbeat failed with WinError 5 at 00:46:45.650030 UTC. The unhandled exception escaped the main recording loop, preventing its deadline-finalizer call. Independent receipt-gated serial/server threads nevertheless continued the fixed original window. Current target attributes are not read-only, and current ACL grants the owner FullControl. This cannot prove historical handle state.

The [scratch Windows sharing-lock probe](./windows_share_lock_probe.json) opened its own target with read/write sharing but no FILE_SHARE_DELETE: replacement reproduced **WinError 5**, and immediately succeeded once that handle closed. This supports a transient sharing/reader-lock mechanism; it does not identify the actual original locking process. No historical handle trace/ProcMon data exists, and no security/ACL changes were made.

## Changes

- New [collector successor](../../../tools/run_recorder/collector_v2.py), [reliability module](../../../tools/run_recorder/reliability.py) and [host monitor wrapper](../../../tools/run_recorder/monitor_instrumented_v2.py); historical collector/process remains unchanged.
- Unique closed temp files; **three** replace attempts with only 25 ms then 50 ms waits. Each failure is recorded independently in an append-only journal. Exhaustion preserves an immutable report fallback and returns failure rather than aborting. Error-journal failure has memory/stderr fallback.
- A dedicated deadline worker, independent of heartbeat/main reporting, sets cutoff before report retries or evidence wait. Admission always uses the original monotonic window. Settings capture failure cannot skip finalization. Unexpected finalizer failures leave an explicit recovery-needed marker.
- Explicit nonce-linked pre-run and end-of-run screenshot requests. Record actual acquisition UTC interval, clock provenance, image hash, observation source and exact observed settings. Missing/invalid/mismatched evidence stays flagged. Pre-run evidence failure blocks before monitor/reset; end evidence failure still finalizes a flagged run. Default observer response timeout 30 seconds is an operational timeout, not a new frozen-plan validity rule.
- Prepared image/config hashes and plan hash checked before a future monitor/reset. Measurement interval, warm-up and first-415 rule unchanged; nearest-rank P95 retained explicitly.
- The historical register updater is HBPSN-01-specific. The successor emits a run-ID-specific update request for separate reviewed application instead of silently applying that updater to a different run. Neither dry run alters a register.

## Final-revision 60-second dry run

Source is **synthetic TEST_ONLY**, not board readings. Exact runtime source hashes/snapshot were saved before execution and verified unchanged. The report generator was completed afterwards and is separately hashed. Earlier 60-second tests remain preserved: the initial plumbing check passed; the second correctly finalized TEST_ONLY_FAILED_SETTINGS when the observer response arrived after its 45-second operational wait. That screenshot's real acquisition time was 02:05:41.179–02:05:41.369 UTC, and it remains late supplementary to that test; no result was relabelled. [Prior test outcomes](./prior_test_outcomes.json) records both. This final-revision test uses the same deadline/report/settings functions as the repaired collector, with the observer waiting at cutoff.

- Fixed UTC window **2026-11-04T02:06:46.910205+00:00–2026-11-04T02:07:46.910205+00:00**, exactly 60 monotonic seconds. Helsinki is UTC+02.
- Deadline observed **2026-11-04T02:07:46.918592+00:00**, 8.494600 ms after target. Admission did not move with that scheduling latency.
- Pre screenshot acquired **2026-11-04T02:06:40.274Z–2026-11-04T02:06:40.485Z**; end screenshot **2026-11-04T02:07:46.966Z–2026-11-04T02:07:47.167Z**. Both are actual capture brackets. Their screenshot-runtime monotonic fields are explicitly labelled estimates mapped from the host UTC/monotonic request anchor; direct actual acquisition UTC is retained.
- 306 injected heartbeat replacement PermissionErrors; all writes exhausted exactly three attempts. 3 separate optional-report replacement PermissionErrors. Error journal and immutable fallbacks retained.
- 102 synthetic arrivals accepted; 1 deliberately late arrival excluded. Every accepted receipt lies before the fixed cutoff. No synthetic RTT is a scientific result.
- Pre/end settings checks PASS; cutoff, post capture and finalizer executed. [TEST_ONLY finalization](./TEST_ONLY_FINALIZED.json), [cutoff evidence](./recording_cutoff_observed.json), [accepted synthetic CSV](./TEST_ONLY_accepted.csv), [full synthetic stream](./TEST_ONLY_synthetic_stream.jsonl), [error journal](./reporting_errors.jsonl), [pre screenshot](./TEST_ONLY_pre_run_clumsy.png), [end screenshot](./TEST_ONLY_end_of_run_clumsy.png), [request/response evidence](./settings_requests/).
- Five focused tests pass: retry exhaustion/recovery; missing evidence remains MISSING; capture PermissionError still invokes finalization; blocked reporting/main cannot prevent deadline; actual collector finalizer executes offline on synthetic fixtures with correct eligibility/mean/P95 and no register application. [Test log](./unit_tests.log).

Clumsy screenshot observations: frozen UDP 14567 filter, Stop button (capture running), all eight function checkboxes unchecked. Lag is disabled with 100 ms/outbound displayed; Drop is disabled with 10.0% and both directions displayed. Disabled configured values are retained as observed, not silently changed to another registered condition. Hashes bind each actual screenshot; small status-indicator changes can change the hash. Fresh capture times are saved separately.

## Limitations before another formal experiment

The 60-second synthetic tests validate host timer/report/evidence plumbing and the offline finalizer, not a new boot, serial hardware, network impairment or an uninterrupted 37-minute deployment. **A separate active, persistent read-only GUI observer is required** to service screenshot requests; the collector itself cannot take screenshots. The test used the current computer-use session to service those requests. Unattended 37-minute screenshot-service longevity has not been demonstrated. Do not start another formal run until that observer is prepared. Without it, preflight blocks or post evidence remains missing; no automatic PASS is fabricated.

Settings observations do not prove continuous GUI state or per-packet effect. No firmware rebuild/flash/reset, ping, network test, Clumsy setting change or new formal run occurred. Current server and serial monitor remain running.

## HBPSN-01 recovered statistics, validity unchanged

**FAILED_SETTINGS, pending review**. Original 4 November 2026, 02:38:26.327–03:15:26.327 Helsinki window only. Raw APP_RTT 441; warm-up excluded 10; eligible 431; selected 415; extra eligible 16; shortfall 0. Sequences 11–425; ESP timestamps 63,653–2,137,793 ms. No additional reset, sequence gap/repeat or logged connection error; three startup Wi-Fi warning lines retained.

Minimum **24.671 ms**, mean **67.5400265060 ms**, median **65.552 ms**, nearest-rank P95 **105.842 ms** (rank 395), maximum **165.999 ms**. No outliers removed. These descriptive measurements are retained without promoting the run's validity status.

See [original recovered report](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/runs/HBPSN-01/attempt_20261104T002840Z/recovery_20261104T013757Z/SUMMARY.md), [all evidence/code hashes](./SHA256SUMS.json), [protected original hashes](./protected_original_hashes.json), [tested code hashes](./tested_code_hashes.json), [final verification](./final_verification.json).
