# HBPSN-04 review under the original frozen criteria

Decision: **NOT_APPROVED — pending operator stability confirmation.** No final COMPLETE/valid classification or register change was made. This is not a finding that settings actually changed.

## Original rules and assessment

The unchanged frozen plan says:

> Save screenshots before reset and after recording, with UTC and hashes.

> Settings must be stable before the measured reset and throughout the 37 minutes.

Both actual images exist and their hashes verify. They show matching TCP14568 CONTROL settings: capture running, all main effects off. The post-image was acquired **2026-11-06T02:41:43.336Z–2026-11-06T02:41:44.503Z**, **184.654217 seconds after the deadline**. SHA256 `2d1a62515d045b781bb2f52902016322374aa430741155153c622289823639cf`. This real delay remains flagged. The original rule contains no numeric post-image timing cutoff. The collector's30-second wait does not create one, so lateness alone is not used to reject the run.

However, the operator has not supplied the requested exact stability statement covering the run start through screenshot completion. The current user message requests review and is not a statement that settings remained unchanged. Matching before/after images cannot establish continuous stability between them. The original plan's stability condition remains unverified; the user-required operator confirmation/review gate is also outstanding. No answer or receipt time has been invented or backdated. [Outstanding request](../post_recording_evidence_20261106T024143336Z/operator_confirmation_request.json).

The original error rule says:

> If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.

One new unattributed server line `TCP+TLS ERROR:` was received02:02:37.577340UTC from source bytes160–177. It remains in the fixed-window stderr and receipt ledger; its cause/peer are unknown. No reboot occurred. Under this rule it is retained as a session flag, not automatically treated as invalidating and not declared harmless. Historical probe errors are separate. Zero serial connection errors must not be presented as zero server errors.

## Data and preserved flags

Original window:6November2026,04:01:38.681783–04:38:38.681783 Helsinki,2220seconds. Automatic finalization succeeded. Startup gates passed. Raw RTTs441; warm-up excluded10; eligible431; selected415; extras16; shortfall0. Selected sequences11–425, ESP62367–2136487ms. No subsequent reboot, sequence gap or interruption was recorded. Mean69.455561ms, median67.507ms, minimum26.927ms, nearest-rankP95 107.536ms, maximum248.069ms.

Original automatic **FAILED_SETTINGS / MISSING end-image** flags are preserved intact. They describe the finalizer's evidence state at its response deadline; they do not erase the later actual image or impose a new frozen cutoff. All71 final-manifest file hashes verify. Raw measurements, screenshots, automatic summaries and prior snapshots were not rewritten.

Both registers are unchanged; HBPSN-04's row still reads RUNNING because automatic finalization emits an unapplied patch. Current data-processing state is FINALIZED, while validity remains NOT_APPROVED. No new pending status was added to the frozen register enum. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP remain unchanged. QUIC crash unresolved. No run or settings change occurred.

[Detailed decision and hashes](./manual_review.json), [post-recording verification](../post_recording_evidence_20261106T024143336Z/POST_RECORDING_VERIFICATION.json), [preserved automatic finalization](../FINALIZED.json), [server error](../server.stderr.raw.log).
