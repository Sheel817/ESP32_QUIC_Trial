"""Separate dated review documentation; never edits a formal run/register."""
from pathlib import Path
import ast,csv,datetime as dt,hashlib,json

root=Path(__file__).resolve().parents[2]
out=Path(Path(__file__).with_name('review_output_path.txt').read_text().strip())
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
now=dt.datetime.now(dt.timezone.utc).isoformat()
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md'
policy='No automatic replacement or extra run to improve results. Any later approved replacement gets a new ID and a deviation record and never overwrites the original or silently becomes the primary scheduled session.'
assert policy in plan.read_text()
statement='The operator cannot confirm whether Clumsy remained unchanged during and after HBPSN-01.'
before=json.loads((out/'protected_original_hashes.json').read_text())
assert all(sha(Path(row['path']))==row['sha256'] for row in before)
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
assert rows[0]['run_id']=='HBPSN-01' and rows[0]['status']=='FAILED_SETTINGS'
assert [rows[1][k] for k in ('run_id','transport','condition','status')]==['HBPSN-02','TCP_TLS','LAG100_OUT','NOT_RUN']
note=f'''# HBPSN-01 separate operator review note

Recorded UTC: **{now}**. This is the time this review note was saved, not the time of the experiment or of any screenshot.

Operator statement, supplied by the user in this session:

> {statement}

Disposition: **FAILED_SETTINGS retained, validity NOT APPROVED**. The operator cannot confirm stability during the original fixed recording or afterwards. No stability confirmation is inferred from a pair of screenshots, unchanged-looking later GUI state, recovered RTTs or absence of logged connection errors. No current/late material is backdated. No original report, log, screenshot, recovery result, register row or frozen plan has been altered. This note is separate review evidence and does not classify the run as valid.

Original window: 4 November 2026, 02:38:26.327–03:15:26.327 Helsinki (UTC+02). HBPSN-01 remains the original QUIC CONTROL failed scheduled session. The earlier failed preflight and measured attempt remain preserved; neither is replaced or rerun by this note.

## Retry/replacement policy

The [unchanged frozen plan](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md), under Reporting and failed-run policy, states exactly:

> {policy}

It also distinguishes preflight-only failed attempts from a measured run: once a measured reset starts, retain the run even when startup/settings/connection checks fail. HBPSN-01 had a measured reset and therefore is not a preflight-only retry.

**Next scheduled run ID: HBPSN-02 — TCP_TLS — LAG100_OUT**, block 1, boot replicate 1, HOME_BOARD, WIFI_PS_NONE; configured 100 ms outbound Lag, other effects off, capture running. Its current status remains NOT_RUN. This identifies the next frozen-order session only; it does not authorize starting it now or changing settings now.

**No replacement attempt ID is currently approved or specified by the plan.** A replacement of HBPSN-01 would require later explicit approval, a genuinely new unique run ID and a dated deviation record. Do not reuse HBPSN-01, quietly add another measured attempt beneath it, overwrite the original attempt, assign HBPSN-02 as its replacement, or silently count replacement data as the original primary session. No replacement ID has been reserved or added to the 18-row register.

## Future evidence review gate

Use the [manual evidence checklist](./MANUAL_EVIDENCE_CHECKLIST.md). Automatic fixed-deadline processing remains enabled and unchanged. It can preserve raw logs and compute statistics even when evidence is missing. Processing completion is not evidence approval.

The successor recorder now reports automatic success candidates as PENDING_EVIDENCE_REVIEW, validity_status NOT_APPROVED, evidence_review_status PENDING_MANUAL_REVIEW. FINALIZED.json means processing finished. It does not emit an automatic COMPLETE.json or apply a positive register status. The register-update request omits status while review is pending; frozen register status vocabulary is unchanged. Operator confirmation must be considered by the reviewer, not inferred by the program.

No future run is to be called valid until required screenshots, timing/order, settings, operator stability confirmation and the rest of the frozen run checks have been reviewed. Missing, uncertain or contradictory confirmation remains flagged. Neither a screenshot-only PASS nor successful automatic analysis bypasses that review. The local pending-review label does not modify the frozen plan or retroactively change HBPSN-01.

Five focused tests passed, including automatic finalization with nominally passing machine checks staying NOT_APPROVED and omitting positive register status. See [test log](./review_gate_tests.log) and [preservation verification](./verification.json). No new 60-second or formal recording was needed for this review-gate change.

No board reset, firmware build/flash, Clumsy setting change, server/monitor reconfiguration or new formal run was performed.
'''
checklist='''# Manual settings-evidence checklist for each future run

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
'''
(out/'REVIEW_NOTE.md').write_text(note,encoding='utf-8')
(out/'MANUAL_EVIDENCE_CHECKLIST.md').write_text(checklist,encoding='utf-8')
for name in ['collector_v2.py','test_reliability.py']:
    ast.parse((root/'tools/run_recorder'/name).read_text())
verification=dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),operator_statement=statement,statement_recorded_utc=now,hbpsn01_status='FAILED_SETTINGS',validity='NOT_APPROVED',protected_file_count=len(before),all_original_hashes_unchanged=True,register_csv_unchanged=True,register_xlsx_unchanged=True,frozen_plan_unchanged=True,next_scheduled_run=dict(run_id='HBPSN-02',transport='TCP_TLS',condition='LAG100_OUT',status='NOT_RUN'),approved_replacement_id=None,automatic_deadline_processing_retained=True,manual_evidence_review_required=True,focused_tests_passed=5)
(out/'verification.json').write_text(json.dumps(verification,indent=2))
files=[p for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json']+[root/'tools/run_recorder'/n for n in ['collector_v2.py','test_reliability.py','README.md']]
(out/'SHA256SUMS.json').write_text(json.dumps([dict(path=str(p),sha256=sha(p)) for p in files],indent=2))
print(json.dumps(dict(review_note=str(out/'REVIEW_NOTE.md'),checklist=str(out/'MANUAL_EVIDENCE_CHECKLIST.md'),verification=verification),indent=2))
