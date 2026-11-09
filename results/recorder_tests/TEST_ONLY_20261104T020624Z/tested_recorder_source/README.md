# Host recorder reliability repair

This directory is a successor to the failed HBPSN-01 host collector. It changes no firmware, frozen plan or existing run files. The historical process has not been patched or restarted. HBPSN-01 stays FAILED_SETTINGS pending review.

## Lifecycle

`collector_v2.py --run-dir <new-attempt-directory>` requires a fresh directory, approved matching prepared-profile preflight/flash evidence, and `expected_clumsy_settings` in preflight metadata. It verifies plan/artifact/config hashes before starting a monitor. It retains the fixed 2,220-second window, warm-up exclusion and first-415 rule. Never point it at an existing attempt. Do not execute it without authorization for that formal run and its designated reset.

The host-only monitor wrapper selects its run directory through RECORDER_RUN_DIR. It preserves the one-reset guard and reset-release anchor; report replacement uses the bounded writer. A failed anchor write preserves the report fallback and never authorizes another reset.

The independent deadline worker starts as soon as the designated anchor is available. Serial/server admission always tests the original monotonic interval; heartbeat progress cannot extend it. At cutoff the worker sets its stop event first, requests end settings evidence, then invokes finalization even if evidence acquisition/reporting failed. Capture/report completion latency is separate from recording duration. Finalization exceptions retain a failed-finalization marker and original raw logs for recovery.

Reports use unique, closed temporary files, three replacement attempts, and waits of 25 ms then 50 ms. Every failed attempt is appended to reporting_errors.jsonl; exhausted writes retain an immutable fallback. Error journaling has an in-memory/stderr fallback and cannot deliberately abort the timer. This addresses ordinary permission/sharing failures; it cannot guarantee recovery from process termination, OS suspension or an indefinitely hung storage API.

## Explicit screenshot observer contract

The recorder does not manipulate Clumsy. A **separate active read-only GUI observer** must service `settings_requests/pre_run.request.json` and `end_of_run.request.json`. The supplied 60-second dry run used the computer-use screenshot API and visual inspection. The recorder cannot take screenshots by itself: do not call it unattended-ready without a persistently available observer. Absence or failure is visible rather than a fabricated PASS.

Each request contains a unique nonce, phase, actual request UTC/monotonic time, expected settings, anchor and response timeout. The observer must take a fresh screenshot **after that request**, save it inside the attempt, and atomically submit `<phase>.response.json` with:

- nonce, screenshot relative path and SHA-256;
- actual capture_started_utc / capture_completed_utc;
- capture_started_monotonic / capture_completed_monotonic and clock provenance (the CUA dry-run estimates these from the request UTC/monotonic bridge and explicitly labels them as estimates);
- source_type GUI_observed or operator_reported, observed settings and a clear label;
- readable exact filter, capture state, enabled effects, configured values/directions and other function states, in screenshot and observation details.

The broker checks nonce, file containment, nonempty image, hash, time order, source type and expected/observed equality. Screenshot semantics require the observer's actual visual inspection; a hash does not independently read checkboxes. GUI-only observations do not prove continuous settings or per-packet impairment.

Pre-run capture must pass **before monitor startup/reset**. Post-run capture is requested immediately after the fixed cutoff; screenshot acquisition, response arrival and their delays are recorded separately. Default response wait is 30 seconds. This is an implementation timeout, **not a new frozen-plan maximum lateness rule**. MISSING, INVALID and MISMATCH remain flagged, and finalization still executes. Do not change a completed run's evidence or status merely by supplying a later screenshot. Store later material separately with actual timestamps and a late-supplementary label for review.

The exact frozen plan says “Save screenshots before reset and after recording, with UTC and hashes.” It contains no numerical maximum delay after recording. It separately requires settings to be stable before reset and throughout 37 minutes. Neither point is rewritten by this repair.

## Register safety and tests

The predecessor updater was hard-coded to HBPSN-01. The successor emits a run-ID-specific register update request and **does not apply it automatically**. Applying the request remains a separate reviewed step. TEST_ONLY never invokes that path or writes a formal register.

`test_reliability.py` tests replacement retry exhaustion/recovery, missing evidence, capture failure, independent deadline execution and the actual collector finalizer using isolated synthetic fixtures. `dry_run.py` runs 60 real host seconds of synthetic arrivals, repeated heartbeat PermissionErrors, a separate reporting failure, actual screenshot requests and a deliberately post-cutoff record. It never opens a serial port or server socket. Outputs belong only under results/recorder_tests/TEST_ONLY_*, never formal experiment directories. The test output path is recorded in test_output_path.txt; a test cannot overwrite an already-started directory.

The dry run validates timer/report/evidence plumbing, not a new firmware boot, serial hardware, an unattended 37-minute observer, TCP_TLS impairment or network behavior. Before another formal run, a persistent screenshot observer and the correct preflight settings must be ready. No formal run was started by this repair.
