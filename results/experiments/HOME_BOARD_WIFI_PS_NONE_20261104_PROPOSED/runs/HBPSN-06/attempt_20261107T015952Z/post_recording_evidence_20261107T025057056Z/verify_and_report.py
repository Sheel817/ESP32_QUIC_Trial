"""Offline original-window verification; no original result/register modification."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,math,statistics
out=Path(__file__).resolve().parent;run=out.parent;study=run.parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):
    with (out/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def rows(n):return list(csv.DictReader((run/n).open(newline='',encoding='utf-8-sig')))
start=load(run/'reset_event.json');final=load(run/'FINALIZED.json');stats=load(run/'statistics.json');post=load(out/'capture_metadata.json');pre=load(run/'pre_run_settings_check.json')['evidence']
assert start['reset_release_utc']=='2026-11-07T02:04:34.926538+00:00' and start['deadline_utc']=='2026-11-07T02:41:34.926538+00:00'
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert final['processing_status']=='FINALIZED' and final['deadline_utc']==start['deadline_utc']
allrows=rows('all_rtts.csv');eligible=rows('eligible_rtts.csv');selected=rows('selected_first_415.csv');excluded=rows('excluded_rtts.csv')
assert [len(x) for x in [allrows,eligible,selected,excluded]]==[441,431,415,10]
assert selected==eligible[:415]
assert all(start['reset_release_monotonic']<=float(r['host_monotonic'])<start['deadline_monotonic'] for r in allrows)
assert all(60000<=int(r['esp_log_uptime_ms'])<2220000 for r in eligible)
assert all(int(r['esp_log_uptime_ms'])<60000 and r['exclusion_reason']=='warmup_below_60000_ms' for r in excluded)
values=[float(r['app_rtt_ms']) for r in selected];ordered=sorted(values)
computed=dict(minimum_ms=min(values),mean_ms=statistics.mean(values),median_ms=statistics.median(values),p95_ms=ordered[math.ceil(.95*len(values))-1],maximum_ms=max(values))
assert all(abs(computed[k]-stats[k])<1e-10 for k in computed)
manifest=load(run/'SHA256SUMS.json');assert all(sha(run/r['path'])==r['sha256'] for r in manifest)
assert sha(run/pre['screenshot'])==pre['sha256'] and sha(out/post['image'])==post['sha256']
assert pre['observed']==post['observed']==load(run/'preflight.json')['expected_clumsy_settings']
assert not any(stats[k] for k in ['connection_error_lines','sequence_gaps','interruptions','server_tail_errors'])
assert len(stats['resets'])==1 and stats['resets'][0]['initial_designated_boot']
server_error=(run/'server.stderr.raw.log').read_text();error_receipts=[json.loads(x) for x in (run/'server.stderr.receipts.jsonl').read_text().splitlines()]
assert server_error==stats['server_stderr']=='TCP+TLS ERROR: \n' and len(error_receipts)==1
late=(dt.datetime.fromisoformat(post['capture_started_utc'])-dt.datetime.fromisoformat(start['deadline_utc'])).total_seconds()
register=list(csv.DictReader((study/'run_register.csv').open(newline='',encoding='utf-8-sig')))
assert [r['status'] for r in register[:6]]==['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','COMPLETE','COMPLETE','RUNNING']
verification=dict(run_id='HBPSN-06',transport='TCP_TLS',condition='DROP1_OUT',processing_status='FINALIZED_ORIGINAL_WINDOW_VERIFIED',validity_status='NOT_APPROVED',evidence_review_status='PENDING_NEW_HBPSN06_OPERATOR_AND_MANUAL_REVIEW',window_utc=[start['reset_release_utc'],start['deadline_utc']],window_helsinki=['2026-11-07T04:04:34.926538+02:00','2026-11-07T04:41:34.926538+02:00'],fixed_seconds=2220,counts=dict(raw_serial_lines=stats['raw_serial_line_count'],raw_rtt=441,warmup_excluded=10,other_excluded=0,eligible=431,selected=415,eligible_extras=16,shortfall=0),statistics=computed,p95_method='Nearest rank ceil(0.95*N)',selected_sequence_range=[int(selected[0]['seq']),int(selected[-1]['seq'])],selected_esp_ms_range=[int(selected[0]['esp_log_uptime_ms']),int(selected[-1]['esp_log_uptime_ms'])],serial_connection_errors=stats['connection_error_lines'],warnings=stats['warning_error_lines'],server_errors=dict(count=1,raw_text=server_error,receipts=error_receipts,source_byte_range=[194,211],cause_or_peer='UNKNOWN; not discarded or declared harmless'),reset_records=stats['resets'],subsequent_resets=0,sequence_gaps=stats['sequence_gaps'],interruptions=stats['interruptions'],server_tail_errors=stats['server_tail_errors'],pre_image=pre,post_image=post,visible_settings_match=True,post_capture_started_seconds_after_deadline=late,automatic_finalization=final,cutoff=load(run/'recording_cutoff_observed.json'),automatic_post_settings_flag=load(run/'post_recording_settings_check.json')['status'],automatic_flags_preserved=True,original_final_manifest_verified=len(manifest),operator_statement=None,operator_statement_receipt_utc=None,operator_confirmation_status='AWAITING_NEW_HBPSN06_SPECIFIC_REPLY; previous runs confirmations not reused',registers_modified=False,register_status='HBPSN-06 RUNNING row unchanged; automatic final patch emitted but not applied. Data processing is FINALIZED; validity NOT_APPROVED.',no_new_run=True,settings_changed=False,unresolved_quic_crash_preserved=True)
save('POST_RECORDING_VERIFICATION.json',verification)
save('operator_confirmation_request.json',dict(run_id='HBPSN-06',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),question='For HBPSN-06 specifically, did filter/effects/capture remain unchanged, no Stop/Start or close/reopen, from7November2026,04:04:34.927Helsinki through04:50:58.162Helsinki? Please give exact statement.',covered_interval_start_utc=start['reset_release_utc'],covered_interval_end_utc=post['capture_completed_utc'],exact_answer=None,receipt_utc=None,status='AWAITING_NEW_HBPSN06_SPECIFIC_REPLY',note='Creation time of audit request, not earlier chat question presentation time. No answer inferred or borrowed from earlier runs.'))
sources=['serial.raw.log','serial_receipts.jsonl','all_rtts.csv','eligible_rtts.csv','selected_first_415.csv','excluded_rtts.csv','server.stdout.raw.log','server.stderr.raw.log','server.stderr.receipts.jsonl','server.sensor_csv.raw.log','statistics.json','reset_event.json','FINALIZED.json','SHA256SUMS.json']
save('source_hashes.json',[dict(path=str(run/n),bytes=(run/n).stat().st_size,sha256=sha(run/n)) for n in sources])
report=f'''# HBPSN-06 TCP_TLS DROP1_OUT — finalized data, validity pending

Automatic finalization succeeded using the original **7November2026,04:04:34.926538–04:41:34.926538 Helsinki** window, UTC02:04:34.926538–02:41:34.926538, exactly2220monotonic seconds. No later measurement included. Cutoff observed13.7356ms late; all RTT receipts meet the original host window. Finalization finished02:42:05.547268UTC after evidence-response waiting, not an extended data window.

## Actual post-recording image

[Image](./{post['image']}) captured **{post['capture_started_utc']}–{post['capture_completed_utc']}**, Helsinki04:50:57.056–04:50:58.162. SHA256 **{post['sha256']}**. Actual acquisition began **{late:.6f}seconds after the deadline**. Delay retained, not backdated. The original plan has no numeric screenshot cutoff; collector30-second wait is not a frozen cutoff.

Exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`; capture running; only Drop enabled, configured Chance1.0%, Outbound checked, Inbound unchecked. Lag, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth disabled. Matches [pre-reset image](../{pre['screenshot']}), captured {pre['capture_started_utc']}–{pre['capture_completed_utc']}, SHA256 `{pre['sha256']}`. No agent settings change. Matching endpoint images do not establish continuous stability. Configured1%Drop is not measured packet/message loss.

## Counts and selected statistics

Raw serial lines581; raw RTTs441; warm-up excluded10; other exclusions0; eligible431; selected415; extra eligible16; shortfall0. Selected sequences11–425, ESP62357–2136477ms; exact first415 eligible records in source order. Every value/outlier retained.

| Statistic | APP_RTT ms |
|---|---:|
| Minimum | {computed['minimum_ms']:.3f} |
| Mean | {computed['mean_ms']:.6f} |
| Median | {computed['median_ms']:.3f} |
| Nearest-rank P95 | {computed['p95_ms']:.3f} |
| Maximum | {computed['maximum_ms']:.3f} |

Recomputed from [selected CSV](../selected_first_415.csv), matching saved statistics. [All RTTs](../all_rtts.csv), [eligible records](../eligible_rtts.csv), [exclusions](../excluded_rtts.csv), [raw serial](../serial.raw.log), [receipts](../serial_receipts.jsonl).

## Errors, resets and limitations

No serial connection error, sequence gap, interruption or server-tail failure. One initial designated reset; no subsequent reboot. Three Wi-Fi warnings retained verbatim in [verification](./POST_RECORDING_VERIFICATION.json).

One NEW unattributed server error **`TCP+TLS ERROR:`** (empty exception text) was received **02:05:32.162784UTC**, source bytes194–211. [Raw server stderr](../server.stderr.raw.log), [receipt ledger](../server.stderr.receipts.jsonl). Cause/peer unknown; no silent discard or harmless classification. Original automatic serial-only connection_error_count0 excludes this separate server error. Older/probe-associated stderr bytes0–194 remain historical and excluded from this run's fresh tail. The server prints no traceback for this line, so none is available.

## Pending review and preservation

Original automatic **FAILED_SETTINGS / MISSING end-image** flags preserved intact. This actual late image is separate supplementary evidence. Overall validity remains **NOT_APPROVED / PENDING_NEW_HBPSN06_OPERATOR_AND_MANUAL_REVIEW**. A new HBPSN-06-specific confirmation covering run start through screenshot completion was requested; earlier runs' confirmations are not reused. No answer or receipt timestamp has been invented.

No register update made. HBPSN-06's row remains RUNNING because the finalizer only emits a patch; data processing is FINALIZED. Earlier outcomes unchanged; QUIC crash remains unresolved. All{len(manifest)} original final-manifest hashes verified. [Source hashes](./source_hashes.json), [verification](./POST_RECORDING_VERIFICATION.json), [original finalizer](../FINALIZED.json). Existing server/monitor left running; no new run, reset, flash, build or settings change.
'''
with (out/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
save('SHA256SUMS.json',[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'])
print(json.dumps(dict(statistics=computed,post_lateness_seconds=late,original_manifest_verified=len(manifest),report=str(out/'REPORT.md')),indent=2))
