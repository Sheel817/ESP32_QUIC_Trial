# Manual settings-evidence checklist for each future run

This is an operational review checklist requested after HBPSN-01, not a revision of the frozen experiment plan. Leave unobserved fields blank and explicitly record unknowns. Do not pre-tick confirmation. Fill it for the actual run/attempt, not for another run or an earlier setup boot.

Run ID: ______  Attempt/session ID: ______  Board: ______
Transport: ______  Condition: ______  Operator: ______
Frozen plan version and SHA-256: ______

## 1. Actual screenshot before measured reset

- [ ] Capture a fresh, readable screenshot of the actual Clumsy window before the designated measured reset, with logging ready. Do not substitute a prior-run screenshot or setup image.
- [ ] Show exact transport-specific frozen filter, capture RUNNING, Lag/Drop enabled states, configured values, inbound/outbound direction and every other effect's state. Record tool version/executable hash. Preserve displayed inactive values as observed.
- [ ] Save the original image under a new run-specific filename. Record actual acquisition UTC start/end, source (GUI observed / operator reported), observer name and SHA-256. Never backdate timestamps.
- [ ] Check the intended transport/condition against frozen run order and inspect the actual image. Resolve a failed/missing preflight before any measured reset; do not silently retry a measured run.

Pre-image path: ______  SHA-256: ______
Actual capture UTC start/end: ______
Observed filter/settings and source: ______
Measured reset request/release UTC: ______
Reviewer confirms image was acquired before reset: YES / NO / UNKNOWN

## 2. Leave settings unchanged during recording

- [ ] Keep the verified filter, capture state and all function/value/direction settings unchanged throughout the fixed 37-minute recording.
- [ ] Do not toggle effects, change transport/filter, reset the board, extend the window, run pings or other tests to improve results.
- [ ] If any change, uncertainty, interruption or accidental action occurs, preserve raw recording and record what happened and its actual UTC. Do not conceal it, restart the same session or silently replace the run.
- [ ] Keep automatic deadline processing active. Recording ends at the original fixed deadline regardless of screenshot availability or RTT count.

Original start/deadline UTC: ______
Observed changes, interruptions or uncertainty (or explicit none known): ______

## 3. Actual screenshot after recording, before changes

- [ ] After the fixed recording ends, capture another fresh, readable screenshot **before any settings changes**, while the actual end condition is still displayed.
- [ ] Record actual acquisition UTC start/end, screenshot path, SHA-256 and source. Retain request, capture and response times separately when using the broker.
- [ ] Verify exact filter, capture state, effects, values and direction against pre-run evidence and registered condition. Preserve both original images even if they differ.
- [ ] If capture is late, occurred after a change or is missing, explicitly label that limitation. Later screenshots remain supplementary; do not backdate or present them as original end-state evidence.

Post-image path: ______  SHA-256: ______
Actual capture UTC start/end: ______
Elapsed time after recording deadline: ______
Any settings change before this capture? YES / NO / UNKNOWN
If yes/unknown, actual details/times: ______

The frozen plan says before reset / after recording, with UTC and hashes. It specifies no numerical maximum post-capture delay. This checklist does not invent one; actual timing and stability still require review.

## 4. Explicit operator stability confirmation and review

- [ ] Ask the operator to state whether Clumsy's verified filter, capture and effect settings remained unchanged from the pre-reset screenshot, throughout recording, and until the post-recording screenshot.
- [ ] Save the operator's exact statement, name/source and actual confirmation UTC. Record YES / NO / CANNOT CONFIRM; never infer YES from screenshots or RTTs.
- [ ] Review both screenshots, hashes/timestamps/order, registered settings, operator statement, startup checks, resets/errors and any deviations. Machine evidence PASS alone is insufficient for validity.
- [ ] Record reviewer, actual review UTC, decision and reasons. Until review completes, keep validity NOT_APPROVED / PENDING_EVIDENCE_REVIEW in local metadata. Apply any approved register decision separately, using only the frozen statuses.
- [ ] If stability cannot be confirmed, retain the failed/settings-limited evidence and do not classify the run as valid. A replacement needs separate approval, a new run ID and a deviation record; it never overwrites the original.

Operator exact statement: ______
Stability response: YES / NO / CANNOT CONFIRM (select explicitly)
Operator/source and actual confirmation UTC: ______
Reviewer and actual review UTC: ______
Evidence review decision, limitations and reasons: ______
Approved register status, if any, and separate application record: ______
