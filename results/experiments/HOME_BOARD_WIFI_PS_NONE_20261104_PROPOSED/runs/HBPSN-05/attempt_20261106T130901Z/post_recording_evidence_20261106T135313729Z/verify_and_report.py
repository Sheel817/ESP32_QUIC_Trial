"""Offline verification; writes new post-evidence audit only."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,math,statistics
out=Path(__file__).resolve().parent;run=out.parent;study=run.parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):
    with (out/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def rows(n):return list(csv.DictReader((run/n).open(newline='',encoding='utf-8-sig')))
start=load(run/'reset_event.json');final=load(run/'FINALIZED.json');stats=load(run/'statistics.json');post=load(out/'capture_metadata.json');pre=load(run/'pre_run_settings_check.json')['evidence']
assert start['reset_release_utc']=='2026-11-06T13:13:20.156359+00:00' and start['deadline_utc']=='2026-11-06T13:50:20.156359+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert final['processing_status']=='FINALIZED' and final['deadline_utc']==start['deadline_utc']
allrows=rows('all_rtts.csv');eligible=rows('eligible_rtts.csv');selected=rows('selected_first_415.csv');excluded=rows('excluded_rtts.csv')
assert [len(x) for x in [allrows,eligible,selected,excluded]]==[441,431,415,10]
assert selected==eligible[:415]
assert all(start['reset_release_monotonic']<=float(r['host_monotonic'])<start['deadline_monotonic'] for r in allrows)
assert all(60000<=int(r['esp_log_uptime_ms'])<2220000 for r in eligible)
assert all(r['exclusion_reason']=='warmup_below_60000_ms' and int(r['esp_log_uptime_ms'])<60000 for r in excluded)
values=[float(r['app_rtt_ms']) for r in selected];ordered=sorted(values)
computed=dict(minimum_ms=min(values),mean_ms=statistics.mean(values),median_ms=statistics.median(values),p95_ms=ordered[math.ceil(.95*len(values))-1],maximum_ms=max(values))
assert all(abs(computed[k]-stats[k])<1e-10 for k in computed)
manifest=load(run/'SHA256SUMS.json');assert all(sha(run/r['path'])==r['sha256'] for r in manifest)
assert sha(run/pre['screenshot'])==pre['sha256'] and sha(out/post['image'])==post['sha256']
assert pre['observed']==post['observed']==load(run/'preflight.json')['expected_clumsy_settings']
assert not stats['connection_error_lines'] and not stats['sequence_gaps'] and not stats['interruptions'] and not stats['server_tail_errors'] and not stats['server_stderr']
assert len(stats['resets'])==1 and stats['resets'][0]['initial_designated_boot']
late=(dt.datetime.fromisoformat(post['capture_started_utc'])-dt.datetime.fromisoformat(start['deadline_utc'])).total_seconds()
register=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
assert [r['status'] for r in register[:5]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','RUNNING']
verification=dict(run_id='HBPSN-05',transport='QUIC',condition='LAG100_OUT',processing_status='FINALIZED_ORIGINAL_WINDOW_VERIFIED',validity_status='NOT_APPROVED',evidence_review_status='PENDING_OPERATOR_AND_MANUAL_REVIEW',window_utc=[start['reset_release_utc'],start['deadline_utc']],window_helsinki=['2026-11-06T15:13:20.156359+02:00','2026-11-06T15:50:20.156359+02:00'],fixed_seconds=2220,counts=dict(raw_serial_lines=stats['raw_serial_line_count'],raw_rtt=441,warmup_excluded=10,other_excluded=0,eligible=431,selected=415,eligible_extras=16,shortfall=0),statistics=computed,p95_method='Nearest rank ceil(0.95*N)',selected_sequence_range=[int(selected[0]['seq']),int(selected[-1]['seq'])],selected_esp_ms_range=[int(selected[0]['esp_log_uptime_ms']),int(selected[-1]['esp_log_uptime_ms'])],serial_connection_errors=stats['connection_error_lines'],server_stderr=stats['server_stderr'],warnings=stats['warning_error_lines'],reset_records=stats['resets'],subsequent_resets=0,sequence_gaps=stats['sequence_gaps'],interruptions=stats['interruptions'],server_tail_errors=stats['server_tail_errors'],pre_image=pre,post_image=post,visible_settings_match=True,post_capture_started_seconds_after_deadline=late,automatic_finalization=final,cutoff=load(run/'recording_cutoff_observed.json'),automatic_post_settings_flag=load(run/'post_recording_settings_check.json')['status'],automatic_flags_preserved=True,original_final_manifest_verified=len(manifest),operator_statement=None,operator_statement_receipt_utc=None,operator_statement_status='AWAITING_EXACT_REPLY',registers_modified=False,register_status='HBPSN-05 RUNNING remains; automatic final patch is emitted, not applied. Data processing is FINALIZED; no approval.',no_new_run=True,settings_changed=False,unresolved_quic_crash_preserved=True)
save('POST_RECORDING_VERIFICATION.json',verification)
save('operator_confirmation_request.json',dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),question='Did filter/effect/capture settings stay unchanged, with no Stop/Start or close/reopen, from6November2026,15:13:20.156Helsinki through15:53:14.719Helsinki? Please give exact statement.',covered_interval_start_utc=start['reset_release_utc'],covered_interval_end_utc=post['capture_completed_utc'],exact_answer=None,receipt_utc=None,status='AWAITING_REPLY',note='Record creation time, not earlier chat-question ingress time; no answer inferred.'))
sources=['serial.raw.log','serial_receipts.jsonl','all_rtts.csv','eligible_rtts.csv','selected_first_415.csv','excluded_rtts.csv','server.stdout.raw.log','server.stderr.raw.log','server.sensor_csv.raw.log','statistics.json','reset_event.json','FINALIZED.json','SHA256SUMS.json']
save('source_hashes.json',[dict(path=str(run/n),bytes=(run/n).stat().st_size,sha256=sha(run/n)) for n in sources])
report=f'''# HBPSN-05 QUIC LAG100_OUT — finalized data, validity pending

Automatic finalization succeeded using the original **6November2026,15:13:20.156359–15:50:20.156359 Helsinki** window, UTC13:13:20.156359–13:50:20.156359, exactly2220monotonic seconds. No later measurement included. Cutoff observed5.3929ms late; admission still used the original fixed interval. Finalization finished13:50:50.594842UTC after the30-second evidence-response wait, not an extended data window.

## Actual post-recording image

[Image](./{post['image']}) captured **{post['capture_started_utc']}–{post['capture_completed_utc']}**, Helsinki15:53:13.729–15:53:14.719. SHA256 **{post['sha256']}**. Actual acquisition began **{late:.6f}seconds after the deadline**. Delay retained, not backdated. The original plan has no numeric screenshot cutoff; the collector30-second wait is not a frozen cutoff.

Exact filter `udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)`; capture running; only Lag enabled100ms, Outbound checked, Inbound unchecked. Drop, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth disabled. Visible settings match the [pre-reset image](../{pre['screenshot']}), captured {pre['capture_started_utc']}–{pre['capture_completed_utc']}, SHA256 `{pre['sha256']}`. Screenshot matching does not establish continuous stability; no settings were changed by the agent.

## Counts and selected statistics

Raw serial lines591; raw RTT records441; warm-up excluded10; other exclusions0; eligible431; selected415; extra eligible16; shortfall0. First415 eligible rows match source arrival order. Selected sequences11–425, ESP63973–2138133ms. All values/outliers retained.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | {computed['minimum_ms']:.3f} |
| Mean | {computed['mean_ms']:.6f} |
| Median | {computed['median_ms']:.3f} |
| Nearest-rank P95 | {computed['p95_ms']:.3f} |
| Maximum | {computed['maximum_ms']:.3f} |

Recomputed from [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [receipt index](../serial_receipts.jsonl).

## Errors, resets and evidence review

No serial connection error, server stderr error, sequence gap, interruption or server-tail failure recorded. One initial designated boot; no subsequent reboot. Three Wi-Fi warnings remain verbatim in [verification](./POST_RECORDING_VERIFICATION.json): password/authmode threshold, trace band/rate and ba-add. Earlier HBPSN-03 QUIC crash remains unresolved; this completed boot does not establish a fix.

Original automatic **FAILED_SETTINGS / MISSING end-image** flags preserved. The actual late image is supplementary evidence, not a rewrite of automatic files. Overall validity stays **NOT_APPROVED / PENDING_OPERATOR_AND_MANUAL_REVIEW**. Exact settings/capture stability confirmation requested from measured start through screenshot completion; no answer has yet been received or invented. No register change was made here. Its HBPSN-05 row still says RUNNING because automatic finalization only emits an unapplied update request; processing has finished.

All{len(manifest)} original final-manifest hashes verified. [Source hashes](./source_hashes.json), [verification](./POST_RECORDING_VERIFICATION.json), [original finalizer](../FINALIZED.json), [settings request status](../post_recording_settings_check.json). Raw originals preserved; no new run, reset, flash, build, process or settings change occurred.
'''
with (out/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
save('SHA256SUMS.json',[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'])
print(json.dumps(dict(statistics=computed,post_lateness_seconds=late,original_manifest_verified=len(manifest),report=str(out/'REPORT.md')),indent=2))
