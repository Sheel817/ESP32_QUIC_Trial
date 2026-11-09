"""Review original evidence and stage a narrowly scoped, authorized register change."""
from pathlib import Path
from decimal import Decimal
import csv,datetime as dt,hashlib,io,json,math,statistics

root=Path(__file__).resolve().parents[2];study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
out=Path(Path(__file__).with_name('hbpsn02_manual_review_path.txt').read_text().strip());a=out.parent
post=a/'post_recording_evidence_20261104T131242221Z'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(out/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def csvread(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
now=dt.datetime.now(dt.timezone.utc).isoformat()
operator=load(out/'operator_statement.json');comparison=load(post/'post_vs_pre_comparison.json');s=load(post/'verified_statistics.json');start=load(a/'reset_event.json');pf=load(a/'preflight.json')
plan=study/'EXPERIMENT_PLAN_PROPOSED_V1.md';text=plan.read_text()
assert sha(plan)==pf['plan_sha256']=='6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
assert sha(study/'freeze_manifest.json')==pf['freeze_manifest_sha256']
quotes=dict(images='Save screenshots before reset and after recording, with UTC and hashes.',stability='Settings must be stable before the measured reset and throughout the 37 minutes.',connection_errors='If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls. Do not silently discard the session.',reboot='If a reboot occurs, keep the entire fixed-window recording and mark the run failed/interrupted; identify each boot, but do not concatenate post-reboot RTTs into the initial-boot first-415 sample.')
assert all(q in text for q in quotes.values())
inputs=[p for p in a.rglob('*') if p.is_file() and out not in p.parents and p.name not in {'monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log','heartbeat.json'} and '__pycache__' not in p.parts]
inputs+=[plan,study/'freeze_manifest.json']
save('protected_evidence_hashes.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in inputs])
assert all(sha(Path(x['path']))==x['sha256'] for x in load(a/'hbpsn01_preservation_before.json'))
for x in pf['firmware_artifacts']+pf['configuration']:assert sha(Path(x['path']))==x['sha256']
pre_path=Path(comparison['pre_image']);post_path=Path(comparison['post_image'])
assert sha(pre_path)==comparison['pre_sha256'] and sha(post_path)==comparison['post_sha256']
assert load(a/'pre_run_settings_check.json')['evidence']['observed']==comparison['settings']==load(post/'capture_metadata.json')['observed']
t=lambda x:dt.datetime.fromisoformat(x)
assert t(comparison['pre_capture_completed_utc'])<t(start['reset_release_utc'])<t(start['deadline_utc'])<t(comparison['post_capture_started_utc'])
assert operator['exact_statement']=='setting stayed unchanged'
assert t(operator['covered_interval_start_utc'])==t(start['reset_release_utc'])
assert t(operator['covered_interval_end_utc'])==t(comparison['post_capture_completed_utc'])
assert t(operator['received_observed_utc'])>t(operator['covered_interval_end_utc'])
assert load(a/'startup_checks.json')['pass_all']
assert start['deadline_monotonic']-start['reset_release_monotonic']==2220
assert not s['gaps'] and not s['timestamp_regressions'] and s['additional_resets']==0
auto=load(a/'statistics.json')
assert not auto['interruptions'] and not auto['server_tail_errors']
assert s['selected_count']==415 and s['shortfall']==0 and s['raw_rtt_count']==441 and s['eligible_count']==431
selected=csvread(a/'selected_first_415.csv');eligible=csvread(a/'eligible_rtts.csv')
assert selected==eligible[:415]
assert [int(r['seq']) for r in selected]==list(range(11,426))
v=[Decimal(r['app_rtt_ms']) for r in selected]
assert abs(float(sum(v)/len(v))-s['mean_ms'])<1e-12
assert float(sorted(v)[math.ceil(.95*len(v))-1])==s['p95_nearest_rank_ms']
assert len(s['new_server_errors'])==1 and not s['serial_connection_errors']
assert (a/'server.stderr.raw.log').read_text().strip()=='TCP+TLS ERROR:'
assert len(s['reporting_errors'])==2 and not any(r.get('exhausted') for r in s['reporting_errors'])
integrity=load(post/'fixed_window_integrity.json')
assert all(r['all_receipts_in_original_window'] and r['source_bytes_match'] for r in integrity.values())
flags=['POST_IMAGE_CAPTURE_LATE_1094.940958_SECONDS_RETAINED','OPERATOR_REPORTED_STABILITY_NOT_PACKET_LEVEL_PROOF','ONE_NEW_UNATTRIBUTED_TCP_SERVER_ERROR_RETAINED','TWO_RECOVERED_HEARTBEAT_REPLACEMENT_ERRORS','THREE_STARTUP_WIFI_WARNINGS_RETAINED','AUTOMATIC_FAILED_SETTINGS_AND_MISSING_IMAGE_FLAGS_PRESERVED']
decision=dict(run_id='HBPSN-02',reviewed_utc=now,reviewer='Assistant manual evidence review under user conditional authorization; operator statement supplied by user',decision='COMPLETE',validity_status='APPROVED_UNDER_ORIGINAL_FROZEN_PLAN',evidence_review_status='REVIEWED',qualifier='Complete with retained flags; no clean/error-free or exact per-packet impairment claim',operator_statement=operator,original_plan_path=str(plan),original_plan_sha256=sha(plan),exact_criteria=quotes,screenshot_comparison=comparison,operator_confirmation_reviewed=True,settings_review='PASS: matching actual pre/post images plus explicit operator statement of unchanged filter/effects/capture and no close/reopen from run start through post-image completion',post_image_lateness_seconds=comparison['post_capture_started_seconds_after_deadline'],thirty_second_wait='Implementation timeout only; not a frozen-plan cutoff. Automatic failure preserved as historical processing decision, superseded by this separate manual review.',error_assessment=dict(new_server_errors=s['new_server_errors'],serial_connection_error_count=0,rule=quotes['connection_errors'],rationale='The rule requires retained evidence/eligible values, flagging and actual shortfall reporting when an error occurs without reboot. It does not require FAILED_STARTUP/FAILED_SETTINGS/INTERRUPTED for every connection error. Retain this event even though cause and peer are unknown; do not infer setup cause or dismiss it. No reboot, interruption or shortfall is recorded.'),measurement_summary=s,flags=flags,previous_automatic_status=load(a/'FINALIZED.json')['status'],previous_register_status='FAILED_SETTINGS',next_scheduled_run=dict(run_id='HBPSN-03',transport='QUIC',condition='DROP1_OUT',status='NOT_RUN'),source_records_preserved=True)
save('manual_review.json',decision)
before=csvread(study/'run_register.csv');assert before[0]['status']=='FAILED_SETTINGS' and before[1]['status']=='FAILED_SETTINGS'
patch=dict(status='COMPLETE',settings_evidence_type='actual_pre_post_GUI_images_and_operator_reported_stability; manually_reviewed',metadata_path=str((out/'manual_review.json').relative_to(study)).replace('\\','/'),deviation_reason='Manual review under original frozen plan: COMPLETE with flags. Operator exact statement setting stayed unchanged covers start through actual post-image; confirmation receipt observed 2026-11-04T13:31:19.1952412Z. Post-image 1094.940958s late; no frozen lateness cutoff. One new unattributed TCP server error retained (zero serial errors); no reboot/gap/shortfall. Two heartbeat retries recovered. Original automatic FAILED_SETTINGS/MISSING flags and prior registers preserved.')
target=dict(before[1]);target.update(patch)
with (study/'run_register.csv').open(newline='',encoding='utf-8-sig') as f:headers=next(csv.reader(f))
buf=io.StringIO(newline='');csv.DictWriter(buf,fieldnames=headers,quoting=csv.QUOTE_ALL,lineterminator='\r\n').writerow(target)
lines=(study/'run_register.csv').read_bytes().splitlines(keepends=True);assert len(lines)==19;lines[2]=buf.getvalue().encode()
staged=out/'register_manual_review.staged.csv';staged.write_bytes(b''.join(lines))
save('register_apply_request.json',dict(run_id='HBPSN-02',phase='MANUAL_REVIEW_APPROVED',output_dir=str(out),csv_staged_path=str(staged),patch=patch,review_evidence_path=str(out/'manual_review.json'),review_evidence_sha256=sha(out/'manual_review.json')))
report=f'''# HBPSN-02 manual review under original frozen criteria

Decision: **COMPLETE, with retained flags**. Validity **APPROVED_UNDER_ORIGINAL_FROZEN_PLAN**. Review UTC: **{now}**. This separate manual decision supersedes the working register's provisional FAILED_SETTINGS entry; it does not rewrite the original automatic decision, raw measurements, earlier reviews, snapshots or frozen plan.

## Operator statement: exact words, actual receipt and coverage

> setting stayed unchanged

Receipt observed UTC: **{operator['received_observed_utc']}**, the first real UTC clock observation while processing this user message. Platform chat-ingress time is not exposed; it is not invented. Statement saved UTC: **{operator['recorded_utc']}**. These receipt/save times are later than the run and are not backdated.

The user's explicit clarification confirms no Clumsy filter/effect/capture changes or close/reopen from **2026-11-04T12:17:27.280042+00:00 through 2026-11-04T13:12:42.694Z**, covering the measured start, whole recording and interval until the actual post-image completed. Evidence type: **operator-reported stability**, not independently monitored continuous GUI state or packet-level verification. [Exact statement record](./operator_statement.json).

## Original settings criteria and image verification

The unchanged [frozen plan](../../../../../EXPERIMENT_PLAN_PROPOSED_V1.md) says:

> {quotes['images']}

> {quotes['stability']}

| Actual image | Capture UTC | SHA-256 |
|---|---|---|
| [Pre-reset](../clumsy_actual_pre_reset.jpg) | 12:17:11.463–12:17:11.943 | `{comparison['pre_sha256']}` |
| [Post-recording](../post_recording_evidence_20261104T131242221Z/HBPSN-02_Clumsy_POST_RECORDING.jpg) | 13:12:42.221–13:12:42.694 | `{comparison['post_sha256']}` |

Both original images were opened and visually reviewed again, and their current SHA-256 hashes match their capture records. Pre-image precedes designated reset12:17:27.280042; post-image follows fixed deadline12:54:27.280042. Both show exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture running, Lag checked100ms, Inbound unchecked, Outbound checked, and Drop/Throttle/Duplicate/Out of order/Tamper/Set TCP RST/Bandwidth unchecked. The operator statement supplies the intervening stability confirmation; matching images alone do not.

Post-image acquisition began **1094.940958 seconds (18 minutes14.940958 seconds)** after the deadline. This remains explicitly recorded. The frozen plan gives no numerical maximum post-image delay. The collector's30-second response wait is an implementation timeout, not a frozen acceptance rule. That original MISSING/FAILED_SETTINGS output remains preserved; the actual later image and retrospective statement are reviewed using the original rule, without backdating either.

Clumsy0.3 is visible in both images. Current executable hash/process metadata, observed at manual-review time, are saved separately as supplementary context and are not falsely labelled as a pre-reset binary-hash observation. Startup serial evidence includes SSID/BSSID, channel11, RSSI-31, AP beacon102400us and DTIM1. Host-load/background-traffic detail was not continuously instrumented; no per-packet impairment proof is claimed.

## New TCP error: retained, cause unknown, assessed by the frozen rule

The plan explicitly says:

> {quotes['connection_errors']}

It separately requires a failed/interrupted run for reboot; none is recorded here. One NEW bare `TCP+TLS ERROR: ` line was host-received at **12:18:22.468737 UTC** within the fixed window, original source bytes[51,68). It lacks a peer/session ID and useful error detail. Its cause, responsible peer and true emission time cannot be inferred; no setup-connection or harmlessness explanation is asserted. It is retained and flagged, with register connection_error_count=1. Three historical errors before byte51 remain separate. There are zero serial connection-error lines and no observed reboot, sequence gap or interruption. The existing rule permits completion while retaining/flagging connection errors without reboot and reporting the actual shortfall, which is zero. No stricter automatic rejection rule is invented, and the error is not discarded to achieve COMPLETE.

## Other criteria and preserved measurements

Prepared BIN/ELF/bootloader/partition/configuration hashes still match preflight and the frozen firmware profile. HOME_BOARD identity, ELF digest prefix, WIFI_PS_NONE requested/returned0, TCP_TLS/MQTT/subscription, TLS1.3 AES128GCM suite1301 ALPNmqtt certificate modeNONE and TCP_NODELAY1 passed in the designated measured startup. The preflight/runtime/flash/reset records remain unchanged.

Fixed window **4 November2026, 14:17:27.280042–14:54:27.280042 Helsinki (UTC+02)**, exactly2220 monotonic seconds. Independent byte/receipt checks show raw data confined to the original window. Automatic finalization completed; no data after cutoff was added. Raw APP_RTT441; warm-up excluded10; eligible431; selected first415; extras16; shortfall0. Selected sequences11–425, ESP timestamps62847–2136967ms, with all outliers retained. No additional resets, regressions, gaps/repeats or malformed RTTs. Mean188.9541108434ms, min127.227, median187.392, nearest-rank P95248.170 (rank395), max867.649. Existing CSVs were read/verified, never rewritten.

Flags remain: post-image lateness, operator-reported continuity, one unattributed server error, three startup Wi-Fi warnings, and two real heartbeat replacement failures that recovered without retry exhaustion. The late-image automatic flags, original finalizer statistics and all earlier register snapshots remain in place. [Machine-readable manual review and full evidence references](./manual_review.json), [protected original evidence hashes](./protected_evidence_hashes.json), [before-review CSV](./register_before_manual_review.csv), [before-review XLSX](./register_before_manual_review.xlsx). Approval means the original completion/settings criteria are satisfied with these flags; it is not a clean/error-free label or a claim of exactly100ms added RTT.

## Register decision and next run

Only HBPSN-02's row is to change to existing permitted status **COMPLETE**, with updated evidence type, authoritative manual-review path and explicit flags. Counts, RTT values and error count remain unchanged. HBPSN-01 remains FAILED_SETTINGS, all other rows/order and the frozen plan remain unchanged. Application and preservation checks are documented separately after export.

Next scheduled run: **HBPSN-03 — QUIC — DROP1_OUT**, currently NOT_RUN. No replacement or new run is authorized or started by this review. No firmware/settings/device changes occurred.
'''
(out/'MANUAL_REVIEW.md').write_text(report,encoding='utf-8')
print(json.dumps(dict(decision='COMPLETE_WITH_FLAGS',reviewed_utc=now,report=str(out/'MANUAL_REVIEW.md'),register_request=str(out/'register_apply_request.json')),indent=2))
