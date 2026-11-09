"""Manual evidence review; new audit files only, no register/result modification."""
from pathlib import Path
import csv,datetime as dt,hashlib,json
run=Path(__file__).resolve().parent;study=run.parents[2];root=study.parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
now=dt.datetime.now(dt.timezone.utc)
out=run/('manual_review_'+now.strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';assert sha(plan)=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
text=plan.read_text(encoding='utf-8')
rules=dict(images='Save screenshots before reset and after recording, with UTC and hashes.',stability='Settings must be stable before the measured reset and throughout the 37 minutes.',connection_errors='If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.')
assert all(v in text for v in rules.values())
post_dir=run/'post_recording_evidence_20261106T024143336Z'
post=load(post_dir/'capture_metadata.json');pre=load(run/'pre_run_settings_check.json')['evidence'];verified=load(post_dir/'POST_RECORDING_VERIFICATION.json')
assert sha(post_dir/post['image'])==post['sha256'] and sha(run/pre['screenshot'])==pre['sha256']
assert post['filter']==pre['observed']['filter'] and post['capture']==pre['observed']['capture']=='RUNNING'
assert not any(post['main_effects'].values())
original=load(run/'SHA256SUMS.json');assert all(sha(run/x['path'])==x['sha256'] for x in original)
assert verified['counts']['selected']==415 and verified['counts']['shortfall']==0
request=load(post_dir/'operator_confirmation_request.json')
assert request['exact_answer'] is None
final=load(run/'FINALIZED.json');stats=load(run/'statistics.json')
register_paths=[study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx']
before={str(p):sha(p) for p in register_paths}
register=list(csv.DictReader(register_paths[0].open(newline='',encoding='utf-8-sig')))
assert [r['status'] for r in register[:4]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','RUNNING']
review=dict(run_id='HBPSN-04',reviewed_utc=now.isoformat(),decision='NOT_APPROVED_PENDING_STABILITY_CONFIRMATION',validity_status='NOT_APPROVED',evidence_review_status='PENDING_OPERATOR_CONFIRMATION',plan_path=str(plan),plan_sha256=sha(plan),exact_original_rules=rules,findings=dict(fixed_window_pass=True,startup_gates_pass=True,selection_pass=True,pre_post_images_exist_hashes_match=True,visible_control_settings_match=True,post_actual_capture_start_utc=post['capture_started_utc'],post_actual_capture_end_utc=post['capture_completed_utc'],post_capture_started_seconds_after_deadline=verified['post_capture_seconds_after_deadline'],post_image_sha256=post['sha256'],pre_image_sha256=pre['sha256'],no_frozen_numeric_screenshot_cutoff=True,collector_30_second_wait_is_not_plan_cutoff=True,settings_continuity='NOT_ESTABLISHED: matching endpoint images do not establish unchanged filter/effects/capture between them; no exact operator stability statement has been received',operator_statement=None,operator_statement_receipt_utc=None,operator_confirmation_gate_source='Prior explicit user instruction requires operator review/confirmation; original plan independently requires stable settings, not a specific confirmation method',unattributed_server_error=dict(text=stats['server_stderr'],source_byte_range=[160,177],received_utc='2026-11-06T02:02:37.577340+00:00',peer_or_cause='UNKNOWN',assessment='Retain and flag under original non-reboot connection-error rule. Not automatically invalidating, not declared harmless, no error discarded.'),no_reboot_or_gap=True,shortfall=0),automatic_flags_preserved=dict(finalized_status=final['status'],completion_candidate=final['completion_candidate'],end_image_status=load(run/'post_recording_settings_check.json')['status'],note='Original automatic files unchanged; actual late post-image saved separately; flags do not establish a new lateness rule'),statistics=verified['statistics'],counts=verified['counts'],registers_modified=False,register_status='RUNNING remains because finalizer requests are not applied automatically; no status patch made while validity is pending',register_hashes_before=before,prior_outcomes={r['run_id']:r['status'] for r in register[:3]},unresolved_quic_crash_preserved=True,original_final_manifest_entries_verified=len(original),new_run_started=False,settings_changed=False)
with (out/'manual_review.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
report=f'''# HBPSN-04 review under the original frozen criteria

Decision: **NOT_APPROVED — pending operator stability confirmation.** No final COMPLETE/valid classification or register change was made. This is not a finding that settings actually changed.

## Original rules and assessment

The unchanged frozen plan says:

> {rules['images']}

> {rules['stability']}

Both actual images exist and their hashes verify. They show matching TCP14568 CONTROL settings: capture running, all main effects off. The post-image was acquired **{post['capture_started_utc']}–{post['capture_completed_utc']}**, **{verified['post_capture_seconds_after_deadline']:.6f} seconds after the deadline**. SHA256 `{post['sha256']}`. This real delay remains flagged. The original rule contains no numeric post-image timing cutoff. The collector's30-second wait does not create one, so lateness alone is not used to reject the run.

However, the operator has not supplied the requested exact stability statement covering the run start through screenshot completion. The current user message requests review and is not a statement that settings remained unchanged. Matching before/after images cannot establish continuous stability between them. The original plan's stability condition remains unverified; the user-required operator confirmation/review gate is also outstanding. No answer or receipt time has been invented or backdated. [Outstanding request](../post_recording_evidence_20261106T024143336Z/operator_confirmation_request.json).

The original error rule says:

> {rules['connection_errors']}

One new unattributed server line `TCP+TLS ERROR:` was received02:02:37.577340UTC from source bytes160–177. It remains in the fixed-window stderr and receipt ledger; its cause/peer are unknown. No reboot occurred. Under this rule it is retained as a session flag, not automatically treated as invalidating and not declared harmless. Historical probe errors are separate. Zero serial connection errors must not be presented as zero server errors.

## Data and preserved flags

Original window:6November2026,04:01:38.681783–04:38:38.681783 Helsinki,2220seconds. Automatic finalization succeeded. Startup gates passed. Raw RTTs441; warm-up excluded10; eligible431; selected415; extras16; shortfall0. Selected sequences11–425, ESP62367–2136487ms. No subsequent reboot, sequence gap or interruption was recorded. Mean69.455561ms, median67.507ms, minimum26.927ms, nearest-rankP95 107.536ms, maximum248.069ms.

Original automatic **FAILED_SETTINGS / MISSING end-image** flags are preserved intact. They describe the finalizer's evidence state at its response deadline; they do not erase the later actual image or impose a new frozen cutoff. All{len(original)} final-manifest file hashes verify. Raw measurements, screenshots, automatic summaries and prior snapshots were not rewritten.

Both registers are unchanged; HBPSN-04's row still reads RUNNING because automatic finalization emits an unapplied patch. Current data-processing state is FINALIZED, while validity remains NOT_APPROVED. No new pending status was added to the frozen register enum. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP remain unchanged. QUIC crash unresolved. No run or settings change occurred.

[Detailed decision and hashes](./manual_review.json), [post-recording verification](../post_recording_evidence_20261106T024143336Z/POST_RECORDING_VERIFICATION.json), [preserved automatic finalization](../FINALIZED.json), [server error](../server.stderr.raw.log).
'''
with (out/'REVIEW.md').open('x',encoding='utf-8') as f:f.write(report)
assert before=={str(p):sha(p) for p in register_paths}
with (out/'SHA256SUMS.json').open('x',encoding='utf-8') as f:json.dump([dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'],f,indent=2)
print(json.dumps(dict(decision=review['decision'],review=str(out/'REVIEW.md'),registers_unchanged=True),indent=2))
