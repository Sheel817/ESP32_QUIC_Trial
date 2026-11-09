"""Offline post-recording verification; preserve automatic flags and originals."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,math,statistics
out=Path(__file__).resolve().parent;run=out.parent;study=run.parents[2];root=study.parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
    with (out/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def rows(n):return list(csv.DictReader((run/n).open(newline='',encoding='utf-8-sig')))
start=load(run/'reset_event.json');final=load(run/'FINALIZED.json');stats=load(run/'statistics.json');post=load(out/'capture_metadata.json');pre=load(run/'pre_run_settings_check.json')['evidence']
assert start['reset_release_utc']=='2026-11-06T02:01:38.681783+00:00'
assert start['deadline_utc']=='2026-11-06T02:38:38.681783+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert final['processing_status']=='FINALIZED' and final['deadline_utc']==start['deadline_utc']
all_rows=rows('all_rtts.csv');eligible=rows('eligible_rtts.csv');selected=rows('selected_first_415.csv');excluded=rows('excluded_rtts.csv')
assert len(all_rows)==441 and len(eligible)==431 and len(selected)==415 and len(excluded)==10
assert selected==eligible[:415]
assert all(60000<=int(x['esp_log_uptime_ms'])<2220000 for x in eligible)
assert all(start['reset_release_monotonic']<=float(x['host_monotonic'])<start['deadline_monotonic'] for x in all_rows)
assert all(int(x['esp_log_uptime_ms'])<60000 for x in excluded)
values=[float(x['app_rtt_ms']) for x in selected];ordered=sorted(values)
computed=dict(minimum_ms=min(values),mean_ms=statistics.mean(values),median_ms=statistics.median(values),p95_ms=ordered[math.ceil(.95*len(ordered))-1],maximum_ms=max(values))
assert all(abs(computed[k]-stats[k])<1e-10 for k in computed)
hashes=load(run/'SHA256SUMS.json');mismatches=[x['path'] for x in hashes if sha(run/x['path'])!=x['sha256']];assert not mismatches
assert sha(out/post['image'])==post['sha256'] and sha(run/pre['screenshot'])==pre['sha256']
expected=load(run/'preflight.json')['expected_clumsy_settings']
assert post['filter']==expected['filter'] and post['capture']==expected['capture']
assert not any(post['main_effects'].values()) and pre['observed']==expected
late=(dt.datetime.fromisoformat(post['capture_started_utc'])-dt.datetime.fromisoformat(start['deadline_utc'])).total_seconds()
register=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
assert [x['status'] for x in register[:4]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','RUNNING']
server_error=(run/'server.stderr.raw.log').read_text();receipts=[json.loads(x) for x in (run/'server.stderr.receipts.jsonl').read_text().splitlines()]
summary=dict(run_id='HBPSN-04',processing_status='FINALIZED_ORIGINAL_FIXED_WINDOW_VERIFIED',validity_status='NOT_APPROVED',evidence_review_status='PENDING_OPERATOR_AND_MANUAL_REVIEW',window_utc=[start['reset_release_utc'],start['deadline_utc']],window_helsinki=['2026-11-06T04:01:38.681783+02:00','2026-11-06T04:38:38.681783+02:00'],fixed_seconds=2220,counts=dict(raw_rtt=441,raw_serial_lines=stats['raw_serial_line_count'],warmup_excluded=10,other_excluded=0,eligible=431,selected=415,extra_eligible=16,shortfall=0),statistics=computed,p95_method='Nearest rank ceil(0.95*N)',selected_sequence_range=[int(selected[0]['seq']),int(selected[-1]['seq'])],selected_esp_ms_range=[int(selected[0]['esp_log_uptime_ms']),int(selected[-1]['esp_log_uptime_ms'])],serial_connection_errors=stats['connection_error_lines'],warnings=stats['warning_error_lines'],initial_reset=stats['resets'],subsequent_resets=0,sequence_gaps=stats['sequence_gaps'],interruptions=stats['interruptions'],server_tail_errors=stats['server_tail_errors'],unattributed_server_errors=dict(raw=server_error,receipts=receipts,count=len(server_error.splitlines()),cause='UNKNOWN; not discarded or classified harmless'),post_image=post,pre_image=pre,visible_settings_match=True,post_capture_seconds_after_deadline=late,automatic_flags_preserved=dict(status=final['status'],post_settings=load(run/'post_recording_settings_check.json')['status']),automatic_finalization_utc=final['finished_utc'],deadline_cutoff=load(run/'recording_cutoff_observed.json'),register_status='RUNNING; automatic final patch emitted but not applied; no register modification during this review',original_manifest_verified=len(hashes),original_manifest_mismatches=mismatches,operator_exact_answer=None,operator_answer_state='AWAITING_REPLY',answer_receipt_not_backdated=True)
save('POST_RECORDING_VERIFICATION.json',summary)
save('operator_confirmation_request.json',dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),question='Did Clumsy filter/effect/capture settings remain unchanged, with no stop/start or close/reopen, from2026-11-06T04:01:38.681783+02:00 through2026-11-06T04:41:44.503+02:00? Please give the exact statement to record.',covered_interval_start_utc=start['reset_release_utc'],covered_interval_end_utc=post['capture_completed_utc'],status='AWAITING_EXACT_REPLY',exact_answer=None,receipt_utc=None,note='Question presented to operator in chat; this timestamp is when the request record was saved, not the earlier chat presentation time. No confirmation inferred.'))
paths=['serial.raw.log','serial_receipts.jsonl','all_rtts.csv','eligible_rtts.csv','selected_first_415.csv','excluded_rtts.csv','server.stdout.raw.log','server.stderr.raw.log','server.sensor_csv.raw.log','reset_event.json','statistics.json','FINALIZED.json','SHA256SUMS.json']
save('source_hashes.json',[dict(path=str(run/p),bytes=(run/p).stat().st_size,sha256=sha(run/p)) for p in paths])
report=f'''# HBPSN-04 TCP_TLS CONTROL — finalized data, validity pending

Automatic finalization succeeded against the original **6November2026,04:01:38.681783–04:38:38.681783 Helsinki** window (UTC02:01:38.681783–02:38:38.681783), exactly2220 monotonic seconds. Cutoff observed7.7674ms late; raw line admission still uses the original monotonic interval. No later measurements were included. Processing finished02:39:09.078928UTC after the30-second evidence wait. That wait is implementation behavior, not a frozen-plan lateness cutoff.

## Actual post-recording image

[Actual screenshot](./{post['image']}) acquired **{post['capture_started_utc']}–{post['capture_completed_utc']}**, Helsinki04:41:43.336–04:41:44.503. SHA256 **{post['sha256']}**. Capture started **{late:.6f}seconds after the deadline**; actual lateness retained, not backdated.

Visible exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture running (Stop button and Started filtering), Lag/Drop/Throttle/Duplicate/Out of order/Tamper/Set TCP RST/Bandwidth all disabled. Saved inactive Lag100ms, Drop1%, outbound checked and inbound unchecked remain inactive. These match the [pre-reset screenshot](../{pre['screenshot']}), captured {pre['capture_started_utc']}–{pre['capture_completed_utc']}, SHA256 `{pre['sha256']}`. No settings changed by the agent. Screenshot matching alone cannot establish continuous stability.

## Counts and selected statistics

- Raw serial lines581; parsed RTT records441.
- Warm-up excluded10; other exclusions0; eligible431.
- Selected415; eligible extras16; shortfall0. All outliers retained.
- Selected sequences11–425, ESP62367–2136487ms. First415 eligible rows match source arrival order exactly; every parsed RTT receipt lies within the original host window.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | {computed['minimum_ms']:.3f} |
| Mean | {computed['mean_ms']:.6f} |
| Median | {computed['median_ms']:.3f} |
| Nearest-rank P95 | {computed['p95_ms']:.3f} |
| Maximum | {computed['maximum_ms']:.3f} |

Recomputed from the actual [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [byte receipts](../serial_receipts.jsonl).

## Errors, resets and limitations

No post-start reboot, sequence gap, serial connection error, collector interruption or server-tail failure was recorded. One initial designated reset is present. Three Wi-Fi warnings are retained in [verification](./POST_RECORDING_VERIFICATION.json). The raw prefix includes buffered setup-boot text and a truncated coexist line joined to the initial ESP-ROM banner at the reset boundary; these bytes are preserved, not interpreted as an additional measured reboot. No affected RTT eligibility was detected.

One NEW **unattributed server error** `TCP+TLS ERROR:` (empty exception text) was received **02:02:37.577340UTC**, source bytes160–177, and retained in [server stderr](../server.stderr.raw.log) with its [receipt](../server.stderr.receipts.jsonl). Its cause/peer are unknown; it is not silently discarded or declared harmless. Historical probe errors occupy bytes0–160 and remain separate. The automatic serial connection_error_count0 does not include this one server error.

## Pending review and preservation

Automatic flags remain **FAILED_SETTINGS / MISSING end image** in the original finalizer files. This actual late image is separate supplementary evidence; those flags were not overwritten. Overall validity stays **NOT_APPROVED / PENDING_OPERATOR_AND_MANUAL_REVIEW**. Exact operator statement requested covering run start through screenshot completion; answer not yet received. This report does not classify the run valid. The new unattributed server error also requires review under the original criteria.

Both registers still have HBPSN-04 RUNNING because automatic finalization emitted a patch without applying it. No register was modified in this review. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with flags and HBPSN-03 FAILED_STARTUP preserved; QUIC crash unresolved.

All {len(hashes)} original final-manifest entries matched their saved SHA256 hashes. [Source hashes](./source_hashes.json) cover original raw/CSV/statistics/finalization evidence. [Detailed verification](./POST_RECORDING_VERIFICATION.json). Existing monitor/server continue; no new run, reset, flash, build or settings change occurred.
'''
with (out/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
save('SHA256SUMS.json',[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'])
print(json.dumps(dict(statistics=computed,post_lateness_seconds=late,original_manifest_files_verified=len(hashes),report=str(out/'REPORT.md')),indent=2))
