import os, json, csv, hashlib, math, statistics, datetime as dt
from pathlib import Path

study = Path('results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED')
run = study / 'runs/HBPSN-07/attempt_20261107T030606Z'
now_utc = dt.datetime.now(dt.timezone.utc)
timestamp_str = now_utc.strftime('%Y%m%dT%H%M%SZ')
out = run / f'audit_review_{timestamp_str}'
out.mkdir(exist_ok=False)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(n, x):
    with (out / n).open('w', encoding='utf-8') as f:
        json.dump(x, f, indent=2)

plan = study / 'EXPERIMENT_PLAN_PROPOSED_V1.md'
plan_hash = sha(plan)

start = load(run / 'reset_event.json')
final = load(run / 'FINALIZED.json')
stats = load(run / 'statistics.json')
startup = load(run / 'startup_checks.json')
pre = load(run / 'pre_run_settings_check.json')['evidence']

allrows = list(csv.DictReader((run / 'all_rtts.csv').open(newline='', encoding='utf-8-sig')))
eligible = list(csv.DictReader((run / 'eligible_rtts.csv').open(newline='', encoding='utf-8-sig')))
selected = list(csv.DictReader((run / 'selected_first_415.csv').open(newline='', encoding='utf-8-sig')))
excluded = list(csv.DictReader((run / 'excluded_rtts.csv').open(newline='', encoding='utf-8-sig')))
extras = list(csv.DictReader((run / 'eligible_extra.csv').open(newline='', encoding='utf-8-sig')))

assert len(allrows) == 441
assert len(excluded) == 10
assert len(eligible) == 431
assert len(selected) == 415
assert len(extras) == 16
assert selected == eligible[:415]
assert extras == eligible[415:]

# Verify startup gate details
assert startup['pass_all'] is True
assert startup['assigned_ip'] == '192.168.137.112'
assert startup['reported_elf_prefix'] == '1f661a4f7'

# Calculate statistics
values = [float(r['app_rtt_ms']) for r in selected]
ordered = sorted(values)
N = len(values)
computed = {
    'count': N,
    'minimum_ms': min(values),
    'mean_ms': statistics.mean(values),
    'sample_sd_ms': statistics.stdev(values),
    'population_sd_ms': statistics.pstdev(values),
    'median_ms': statistics.median(values),
    'p95_ms': ordered[math.ceil(0.95 * N) - 1], # rank 395
    'maximum_ms': max(values)
}

assert abs(computed['minimum_ms'] - stats['minimum_ms']) < 1e-9
assert abs(computed['mean_ms'] - stats['mean_ms']) < 1e-9
assert abs(computed['median_ms'] - stats['median_ms']) < 1e-9
assert abs(computed['maximum_ms'] - stats['maximum_ms']) < 1e-9
assert abs(computed['p95_ms'] - stats['p95_ms']) < 1e-9

server_stderr = (run / 'server.stderr.raw.log').read_text(encoding='utf-8', errors='replace')
server_receipts = [json.loads(x) for x in (run / 'server.stderr.receipts.jsonl').read_text(encoding='utf-8').splitlines()]

# Screenshot status
# Note: Automatic capture timed out (MISSING). Direct API capture attempt returned ERROR_INVALID_HANDLE (headless/detached session).
screenshot_status = {
    'automatic_post_recording_check': load(run / 'post_recording_settings_check.json'),
    'post_deadline_screenshot_file': None,
    'post_deadline_sha256': None,
    'capture_delay_seconds': None,
    'api_capture_error': 'Win32 ERROR_INVALID_HANDLE (6): Background/agent subshell has no interactive desktop display device context; elevated Clumsy GUI cannot be captured without operator interaction or display attachment',
    'status': 'PENDING_OPERATOR_ACQUISITION_OR_CONFIRMATION'
}

review = {
    'run_id': 'HBPSN-07',
    'transport': 'TCP_TLS',
    'condition': 'DROP1_OUT',
    'boot_replicate': 2,
    'reviewed_utc': now_utc.isoformat(),
    'plan_sha256': plan_hash,
    'window_utc': [start['reset_release_utc'], start['deadline_utc']],
    'window_helsinki': ['2026-11-07T05:09:19.159995+02:00', '2026-11-07T05:46:19.159995+02:00'],
    'defined_duration_seconds': 2220,
    'startup_verification': {
        'status': 'PASS',
        'assigned_ip': startup['assigned_ip'],
        'reported_elf_prefix': startup['reported_elf_prefix'],
        'protocol_readback': {
            'transport': 'TCP_TLS/MQTT',
            'wifi_ps_mode': 'WIFI_PS_NONE(0) (requested=0, returned=0)',
            'tcp_nodelay': 1,
            'tls_version': 'TLSv1.3',
            'cipher_suite': 'TLS_AES_128_GCM_SHA256 (suite 0x1301)',
            'alpn': 'mqtt',
            'certificate_verification': 'NONE (mode 0)'
        }
    },
    'counts': {
        'raw_serial_lines': stats['raw_serial_line_count'],
        'raw_rtt': 441,
        'warmup_excluded_below_60000ms': 10,
        'other_excluded': 0,
        'eligible': 431,
        'selected_first_415': 415,
        'eligible_extras': 16,
        'shortfall': 0,
        'selected_seq_range': [int(selected[0]['seq']), int(selected[-1]['seq'])],
        'selected_esp_uptime_ms_range': [int(selected[0]['esp_log_uptime_ms']), int(selected[-1]['esp_log_uptime_ms'])]
    },
    'summary_metrics': computed,
    'diagnostics': {
        'wifi_warnings': stats['warning_error_lines'],
        'serial_connection_errors': stats['connection_error_lines'],
        'sequence_gaps': stats['sequence_gaps'],
        'resets': stats['resets'],
        'server_errors': {
            'count': 1,
            'raw_text': server_stderr,
            'receipts': server_receipts,
            'source_byte_range': [211, 228],
            'receipt_utc': '2026-11-07T03:10:14.826668+00:00',
            'assessment': 'One new unattributed server error TCP+TLS ERROR: retained under original non-reboot error rule; peer/cause unknown'
        }
    },
    'clumsy_pre_image': pre,
    'clumsy_post_screenshot_status': screenshot_status,
    'validity_status': 'NOT_APPROVED',
    'evidence_review_status': 'PENDING_OPERATOR_CONFIRMATION_AND_POST_SCREENSHOT',
    'register_status': 'HBPSN-07 RUNNING row preserved; validity pending operator confirmation. Prior runs HBPSN-01 to HBPSN-06 preserved unchanged.'
}

save('manual_review.json', review)

req = {
    'run_id': 'HBPSN-07',
    'transport': 'TCP_TLS',
    'condition': 'DROP1_OUT',
    'boot_replicate': 2,
    'recorded_utc': now_utc.isoformat(),
    'question': 'For HBPSN-07 specifically, did filter tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568) and Drop 1.0% outbound-only remain running and stable throughout the 37-minute window (2026-11-07 05:09:19 to 05:46:19 Helsinki) without Stop/Start, effect changes, or restart? Please provide your run-specific confirmation and post-run screenshot if available.',
    'exact_answer': None,
    'receipt_utc': None,
    'status': 'AWAITING_NEW_HBPSN07_SPECIFIC_REPLY'
}
save('operator_confirmation_request.json', req)

sources = ['serial.raw.log','serial_receipts.jsonl','all_rtts.csv','eligible_rtts.csv','selected_first_415.csv','excluded_rtts.csv','server.stdout.raw.log','server.stderr.raw.log','server.stderr.receipts.jsonl','server.sensor_csv.raw.log','statistics.json','reset_event.json','FINALIZED.json','SHA256SUMS.json']
save('source_hashes.json', [{'path': str(run/n), 'bytes': (run/n).stat().st_size, 'sha256': sha(run/n)} for n in sources])

report = f"""# HBPSN-07 TCP_TLS DROP1_OUT (Replicate 2) - Audit Review

Original recording completed for the fixed 2,220-second window:
- **Start**: 2026-11-07 05:09:19.159995 Helsinki (03:09:19.159995 UTC)
- **Deadline**: 2026-11-07 05:46:19.159995 Helsinki (03:46:19.159995 UTC)
- **Monotonic duration**: exactly 2,220 seconds (775268.4760111 to 777488.4760111)

## 1. Startup Log Verification
- **Board identity**: HOME_BOARD (MAC `40:4c:ca:56:bb:b0`, COM6)
- **Assigned IP**: `192.168.137.112`
- **Firmware ELF Prefix**: `1f661a4f7` (matches preserved TCP_TLS WIFI_PS_NONE build `1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6`)
- **Wi-Fi Power Save Readback**: `requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)`
- **Socket Options**: `TCP_NODELAY=1; connect/I/O timeout=5000 ms`
- **TLS Parameters**: `TLS=TLSv1.3`, cipher=`TLS_AES_128_GCM_SHA256`, suite=`0x1301`, ALPN=`mqtt`, cert_mode=`NONE (0)`
- **MQTT**: `MQTT connected over TCP_TLS`

## 2. Sample Selection and Summary Metrics
- **Raw RTT count**: 441
- **Warmup excluded (< 60,000 ms ESP uptime)**: 10 records (seq 1 to 10)
- **Eligible count (>= 60,000 ms ESP uptime)**: 431 records
- **Selected first-415**: 415 records (seq 11 to 425; ESP uptime 62,357 ms to 2,136,477 ms)
- **Extra eligible records**: 16 records (seq 426 to 441)
- **Shortfall**: 0

| Metric | Computed Value | Frozen Plan Rule |
|---|---|---|
| Count | 415 | First 415 eligible records in source arrival order |
| Mean | 77.053949 ms | Arithmetic mean of 415 records |
| Sample SD | 65.569142 ms | Sample standard deviation (N-1) |
| Population SD | 65.490095 ms | Population standard deviation (N) |
| Minimum | 26.986 ms | Minimum APP_RTT observed |
| Median | 67.436 ms | Median APP_RTT |
| Nearest-rank P95 | 107.940 ms | Rank ceil(0.95 * 415) = rank 395 |
| Maximum | 627.760 ms | Maximum APP_RTT observed |

## 3. Diagnostics and Preserved Ledger
- **Resets**: Exactly 1 initial designated reset (at line 2); zero subsequent reboots.
- **Serial Connection Errors**: 0
- **Sequence Gaps**: 0
- **Wi-Fi Warnings**: 3 warnings retained verbatim (WPA2 password length, 2G phymode trace, ba-add).
- **Server Errors**: 1 new unattributed server error `TCP+TLS ERROR: ` at 2026-11-07 05:10:14.826668 Helsinki (03:10:14.826668 UTC), source bytes 211-228. Retained under the original non-reboot error rule.

## 4. Clumsy Settings and Validity Status
- **Pre-reset Clumsy image**: [clumsy_actual_pre_reset.jpg](../clumsy_actual_pre_reset.jpg), captured 2026-11-07 05:09:00.897-05:09:01.272 Helsinki, SHA-256 `f677ee483e9a0d1116e29c7cfa7d9bd07ca646ca6078c625cf905a2150b1d72a`. Shows filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture Running, Drop 1.0% outbound only, all other effects off.
- **Post-deadline screenshot**: Automatic capture timed out at finalization; agent subshell attempt returned `ERROR_INVALID_HANDLE` (6) due to headless/detached desktop DC.
- **Validity**: **NOT_APPROVED (PENDING OPERATOR CONFIRMATION & POST-SCREENSHOT)**.
- **Registers**: Both registers retain HBPSN-07 row status `RUNNING`; no completed runs or registers modified.
"""
with (out / 'REVIEW.md').open('w', encoding='utf-8') as f:
    f.write(report)

save('SHA256SUMS.json', [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS.json'])
print(f'Successfully created audit review at: {out}')
