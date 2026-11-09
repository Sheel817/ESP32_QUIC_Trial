"""Document completed TEST_ONLY evidence, preserving all formal run files."""
from pathlib import Path
import ast,csv,datetime as dt,hashlib,json,shutil

tools=Path(__file__).resolve().parent;root=tools.parents[1]
out=Path((tools/'test_output_path.txt').read_text().strip())
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
a=study/'runs/HBPSN-01/attempt_20261104T002840Z'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(out/name).write_text(json.dumps(x,indent=2),encoding='utf-8')
test=load(out/'TEST_ONLY_FINALIZED.json');cutoff=load(out/'recording_cutoff_observed.json')
assert test['status']=='TEST_ONLY_COMPLETE' and test['start']['duration_seconds']==60
assert test['all_accepted_before_deadline'] and test['late_record_excluded']
assert all(sha(Path(x['path']))==x['sha256'] for x in load(out/'protected_original_hashes.json'))
for row in load(out/'tested_code_hashes.json'):
    assert sha(Path(row['path']))==row['sha256'],row['path']
for p in tools.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:register=list(csv.DictReader(f))
assert register[0]['status']=='FAILED_SETTINGS' and all(r['status']=='NOT_RUN' for r in register[1:])
hb=load(a/'recovery_20261104T013757Z/statistics.json')
previous=Path(load(out/'TEST_ONLY_metadata.json')['previous_test'])
for name in ['heartbeat_current_acl.json','heartbeat_current_file_metadata.json']:
    if (previous/name).exists():shutil.copy2(previous/name,out/name)
plan=(study/'EXPERIMENT_PLAN_PROPOSED_V1.md').read_text()
quotes=['Save screenshots before reset and after recording, with UTC and hashes.','There is no impairment ramp or mid-run toggle. Settings must be stable before the measured reset and throughout the 37 minutes. For the next condition, finish/close the previous recording, configure/check the next setting, then begin the next boot session. Do not reset within a run to improve results.','Keep missing fields blank with a reason, never populated with invented zeroes or assumed passes.']
assert all(q in plan for q in quotes)
save('rule_and_review_status.json',dict(plan_path=str(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),plan_sha256=sha(study/'EXPERIMENT_PLAN_PROPOSED_V1.md'),exact_quotes=quotes,numerical_maximum_post_capture_delay_specified=False,hbpsn01_current_status='FAILED_SETTINGS',status_changed=False,review='No validity upgrade or reinterpretation applied. New screenshots are TEST_ONLY and late supplementary for HBPSN-01 only.'))
codefiles=[p for p in tools.glob('*') if p.suffix in ('.py','.md')]
save('final_verification.json',dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),formal_files_and_both_registers_unchanged=True,protected_file_count=len(load(out/'protected_original_hashes.json')),tested_code_unchanged=True,python_syntax_checks_pass=True,hbpsn01_status='FAILED_SETTINGS',other_17_status='NOT_RUN',deadline_lateness_ms=cutoff['lateness_ms'],actual_end_capture_utc=test['post_settings']['evidence']['capture_completed_utc'],no_device_reset_flash_build_or_settings_changes=True))
pre=test['pre_settings']['evidence'];post=test['post_settings']['evidence']
report=f'''# Recorder repair and TEST_ONLY evidence

## Frozen rule and HBPSN-01 review status

The unchanged [frozen plan](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md), line 30, says exactly:

> {quotes[0]}

Line 32 says exactly:

> {quotes[1]}

Line 91 says:

> {quotes[2]}

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

Source is **synthetic TEST_ONLY**, not board readings. Exact source hashes/snapshot were saved before execution. Earlier successful 60-second plumbing test remains separately preserved at `{previous.name}`. This final-revision test uses the same deadline/report/settings functions as the repaired collector.

- Fixed UTC window **{test['start']['reset_release_utc']}–{test['start']['deadline_utc']}**, exactly 60 monotonic seconds. Helsinki is UTC+02.
- Deadline observed **{cutoff['observed_utc']}**, {cutoff['lateness_ms']:.6f} ms after target. Admission did not move with that scheduling latency.
- Pre screenshot acquired **{pre['capture_started_utc']}–{pre['capture_completed_utc']}**; end screenshot **{post['capture_started_utc']}–{post['capture_completed_utc']}**. Both are actual capture brackets. Their screenshot-runtime monotonic fields are explicitly labelled estimates mapped from the host UTC/monotonic request anchor; direct actual acquisition UTC is retained.
- {test['heartbeat_permission_error_attempts']} injected heartbeat replacement PermissionErrors; all writes exhausted exactly three attempts. {test['report_permission_error_attempts']} separate optional-report replacement PermissionErrors. Error journal and immutable fallbacks retained.
- {test['accepted_count']} synthetic arrivals accepted; {test['rejected_count']} deliberately late arrival excluded. Every accepted receipt lies before the fixed cutoff. No synthetic RTT is a scientific result.
- Pre/end settings checks PASS; cutoff, post capture and finalizer executed. [TEST_ONLY finalization](./TEST_ONLY_FINALIZED.json), [cutoff evidence](./recording_cutoff_observed.json), [accepted synthetic CSV](./TEST_ONLY_accepted.csv), [full synthetic stream](./TEST_ONLY_synthetic_stream.jsonl), [error journal](./reporting_errors.jsonl), [pre screenshot](./TEST_ONLY_pre_run_clumsy.png), [end screenshot](./TEST_ONLY_end_of_run_clumsy.png), [request/response evidence](./settings_requests/).
- Five focused tests pass: retry exhaustion/recovery; missing evidence remains MISSING; capture PermissionError still invokes finalization; blocked reporting/main cannot prevent deadline; actual collector finalizer executes offline on synthetic fixtures with correct eligibility/mean/P95 and no register application. [Test log](./unit_tests.log). PowerShell wraps native stderr in NativeCommandError text in that raw log; unittest itself reports all five tests OK.

Clumsy screenshot observations: frozen UDP 14567 filter, Stop button (capture running), all eight function checkboxes unchecked. Lag is disabled with 100 ms/outbound displayed; Drop is disabled with 10.0% and both directions displayed. Disabled configured values are retained as observed, not silently changed to another registered condition. Identical screenshot hashes are expected for unchanged visible content; fresh capture times are separately saved.

## Limitations before another formal experiment

The 60-second synthetic tests validate host timer/report/evidence plumbing and the offline finalizer, not a new boot, serial hardware, network impairment or an uninterrupted 37-minute deployment. **A separate active, persistent read-only GUI observer is required** to service screenshot requests; the collector itself cannot take screenshots. The test used the current computer-use session to service those requests. Unattended 37-minute screenshot-service longevity has not been demonstrated. Do not start another formal run until that observer is prepared. Without it, preflight blocks or post evidence remains missing; no automatic PASS is fabricated.

Settings observations do not prove continuous GUI state or per-packet effect. No firmware rebuild/flash/reset, ping, network test, Clumsy setting change or new formal run occurred. Current server and serial monitor remain running.

## HBPSN-01 recovered statistics, validity unchanged

**FAILED_SETTINGS, pending review**. Original 4 November 2026, 02:38:26.327–03:15:26.327 Helsinki window only. Raw APP_RTT 441; warm-up excluded 10; eligible 431; selected 415; extra eligible 16; shortfall 0. Sequences 11–425; ESP timestamps 63,653–2,137,793 ms. No additional reset, sequence gap/repeat or logged connection error; three startup Wi-Fi warning lines retained.

Minimum **{hb['minimum_ms']:.3f} ms**, mean **{hb['mean_ms']:.10f} ms**, median **{hb['median_ms']:.3f} ms**, nearest-rank P95 **{hb['p95_nearest_rank_ms']:.3f} ms** (rank 395), maximum **{hb['maximum_ms']:.3f} ms**. No outliers removed. These descriptive measurements are retained without promoting the run's validity status.

See [original recovered report](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/runs/HBPSN-01/attempt_20261104T002840Z/recovery_20261104T013757Z/SUMMARY.md), [all evidence/code hashes](./SHA256SUMS.json), [protected original hashes](./protected_original_hashes.json), [tested code hashes](./tested_code_hashes.json), [final verification](./final_verification.json).
'''
(out/'REPAIR_REPORT.md').write_text(report,encoding='utf-8')
files=[p for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json']+codefiles
save('SHA256SUMS.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
print(json.dumps(dict(report=str(out/'REPAIR_REPORT.md'),summary_sha256=sha(out/'REPAIR_REPORT.md'),test_status=test['status'],formal_files_unchanged=True),indent=2))
