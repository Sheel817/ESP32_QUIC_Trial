"""HBPSN-09 closure. cwd = study dir. Default is a dry run that writes nothing.
Write mode needs: --apply --approval-text TEXT --approval-receipt-utc UTC"""
import argparse, csv, datetime as dt, hashlib, io, json, math, os, re, shutil, statistics, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
from xml.sax.saxutils import escape

ap = argparse.ArgumentParser()
ap.add_argument('--apply', action='store_true')
ap.add_argument('--approval-text')
ap.add_argument('--approval-receipt-utc')
args = ap.parse_args()
if args.apply:
    assert args.approval_text and args.approval_receipt_utc

study = Path.cwd()
assert (study / 'EXPERIMENT_PLAN_PROPOSED_V1.md').exists()
root = study.parents[2]
ATT = 'attempt_20261109T183955Z'
A = study / 'runs/HBPSN-09' / ATT
CSV = study / 'run_register.csv'
XL = root / 'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
SHEET = 'xl/worksheets/sheet1.xml'
MID_SRC = Path(r'C:\Users\newsh\Downloads\1794251880985_image.png')
LATE_SRC = Path(r'C:\Users\newsh\Pictures\Screenshots\Screenshot 2026-11-09 234408.png')
MID, LATE = 'clumsy_mid_run_remote_2117.png', 'clumsy_post_late_2344.png'


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def b_sh(b):
    return hashlib.sha256(b).hexdigest()


# Preconditions: nothing moved since the draft
assert sh(CSV) == '46e92f689035fac7323726b6394d02a407fb1ea05ac980c9e26a7339cf66bbc5', 'CSV changed since draft'
assert sh(XL) == '3088a1d9ad3ac4f35ea802ee63f9bf615d314125e30ac189dc174b2635004fab', 'XLSX changed since draft'
assert sh(A / 'SHA256SUMS.json') == '37d2fabebad5f3682774708a89fbd94991c99be149760627d0738a650a85486c', 'manifest changed since draft'
assert sh(MID_SRC) == '47bd1856336b66638777133fd17ddaf119467737c1bdd7729d26dabccc29e38b'
assert sh(LATE_SRC) == '5939bfd478a5cf432b0b8491c28a595296cf2ab33bf83604294a46f7cc0cf346'
items = json.loads((A / 'SHA256SUMS.json').read_text(encoding='utf-8'))
assert all(sh(A / e['path']) == e['sha256'] for e in items)
assert not (A / 'manual_review.json').exists() and not (A / MID).exists() and not (A / LATE).exists()

# Statistics come from the selected CSV
rows = list(csv.DictReader((A / 'selected_first_415.csv').open(encoding='utf-8-sig', newline='')))
v = [float(r['app_rtt_ms']) for r in rows]
o = sorted(v)
st = json.loads((A / 'statistics.json').read_text(encoding='utf-8'))
F = json.loads((A / 'FINALIZED.json').read_text(encoding='utf-8'))
assert len(v) == 415 and statistics.fmean(v) == st['mean_ms'] and o[0] == st['minimum_ms'] and o[-1] == st['maximum_ms'] and statistics.median(v) == st['median_ms']
SD = statistics.stdev(v)
P95 = o[math.ceil(.95 * len(v)) - 1]
assert st['resets'][0]['initial_designated_boot'] and len(st['resets']) == 1 and st['sequence_gaps'] == [] and st['connection_error_lines'] == []

STATEMENT = 'I did not change any Clumsy setting from when I confirmed the declaration until after the HBPSN-09 run ended.'
HOST_STATEMENT = 'Nothing was streaming or downloading on the laptop during the run.'
RECEIPT_UTC, RECEIPT_HEL = '2026-11-09T21:56:15.0385818Z', '2026-11-09T23:56:15.0427938+02:00'
CLOCK = 'First local clock observation while processing the operator message; original message send time unavailable'
FLAGS = ['PRE_RUN_IMAGE_DOES_NOT_SHOW_CLUMSY', 'SETTINGS_EVIDENCE_OPERATOR_REPORTED',
         'END_OF_RUN_OBSERVED_VALUES_FROM_PRE_LAUNCH_DECLARATION', 'NO_CLUMSY_IMAGE_BEFORE_2117_MID_RUN',
         'SUPPLEMENTARY_IMAGE_TIMES_OPERATOR_STATED',
         'LAUNCHED_WITHOUT_TEST_CAPTURE_SHOWING_CLUMSY', 'SERVER_STDERR_TCP_TLS_ERROR_UNATTRIBUTED',
         'IDENTIFICATION_LOG_DERIVED_NO_SEPARATE_FLASH_ID', 'WINDOWS_LISTENER_REPORTING_DISCREPANCY',
         'HOST_REMOTE_DESKTOP_AND_BROWSER_ACTIVITY_DURING_RUN', 'REGISTER_NOT_SET_RUNNING_DURING_RUN']
META = f'runs/HBPSN-09/{ATT}/manual_review.json'
SETTINGS_TYPE = 'operator_reported_declaration; pre_run_image_does_not_show_Clumsy; actual_mid_end_late_GUI_images_and_operator_reported_stability; manually_reviewed'
DEVIATION = (f'Manual review COMPLETE with retained flags ({", ".join(FLAGS)}). Operator exact statement "{STATEMENT}" not relayed; '
             f'local receipt {RECEIPT_UTC}, original send time unavailable. Operator exact statement "{HOST_STATEMENT}" not relayed, same receipt. Settings evidence is operator-reported: the pre-run image does not show Clumsy and the '
             'pre-reset state rests on the declaration confirmed 75.94 s before reset release and the operator statement. Clumsy images at 21:17 Helsinki (operator-stated), at end of run and at 23:44 Helsinki (operator-stated) show the CONTROL settings. '
             'One unattributed server TCP+TLS ERROR retained and counted as in HBPSN-04/07; no serial connection error, reboot, gap or shortfall. '
             f'N 415, Mean {st["mean_ms"]:.3f} ms, SD {SD:.3f} ms, Median {st["median_ms"]:.3f} ms, P95 {P95:.3f} ms, Min {o[0]:.3f} ms, Max {o[-1]:.3f} ms.')

now = dt.datetime.now(dt.timezone.utc)
ts = now.strftime('%Y%m%dT%H%M%SZ')
SETTINGS_SEEN = {'filter': 'tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)', 'capture_button': 'Stop', 'status_line': 'Started filtering. Enable functionalities to take effect.',
                 'all_8_function_checkboxes': 'unticked', 'lag_fields_while_off': 'Outbound ticked, Inbound unticked, Delay 100', 'drop_fields_while_off': 'Outbound ticked, Inbound unticked, Chance 1'}
review = {
    'run_id': 'HBPSN-09', 'attempt_id': ATT, 'transport': 'TCP_TLS', 'condition': 'CONTROL', 'boot_replicate': 2,
    'reviewed_utc': now.isoformat() if args.apply else '<set at write time>',
    'disposition': 'COMPLETE with retained flags',
    'validity_status': 'APPROVED_UNDER_ORIGINAL_FROZEN_PLAN',
    'qualifier': 'COMPLETE with retained flags. Settings are operator-reported as allowed if labelled by plan line 30; no independent or continuous GUI observation is claimed, and no image shows Clumsy before the measured reset.',
    'operator_statement': {
        'exact_statement': STATEMENT, 'relayed': False, 'receipt_utc': RECEIPT_UTC, 'receipt_helsinki': RECEIPT_HEL,
        'receipt_clock_source': CLOCK,
        'scope_as_worded': 'From operator confirmation of the declaration (receipt 2026-11-09T18:56:50.3253449Z) until after the run ended (fixed deadline 2026-11-09T19:35:06.268682Z).', 'not_backdated': True},
    'operator_host_activity_statement': {'exact_statement': HOST_STATEMENT, 'relayed': False, 'receipt_utc': RECEIPT_UTC, 'receipt_helsinki': RECEIPT_HEL, 'receipt_clock_source': CLOCK, 'not_backdated': True,
                                         'limit': 'Operator-reported; host network use was not measured.'},
    'operator_disposition_approval': {'exact_text': args.approval_text or '<operator reply, set at write time>', 'relayed': False, 'receipt_utc': args.approval_receipt_utc or '<set at write time>',
                                      'receipt_clock_source': 'First local clock observation while processing the operator message; original message send time unavailable'},
    'plan_sha256': st['preflight']['plan_sha256'],
    'plan_rules_applied': {'line_30': 'Save screenshots before reset and after recording, with UTC and hashes. If settings are only operator-reported, label them explicitly.',
                           'line_32': 'Settings must be stable before the measured reset and throughout the 37 minutes.',
                           'line_77': 'If connection errors occur without reboot, retain all evidence and eligible values, flag the session, and report observed shortfalls.'},
    'criteria': {'fixed_window_2220_s': True, 'startup_all_gates_pass': st['startup']['pass_all'], 'first415_selection': True, 'one_initial_boot_no_reboot': True, 'sequence_gaps': 0, 'shortfall': 0,
                 'pre_run_image_saved_and_hash_matches': True, 'pre_run_image_shows_clumsy': False, 'end_of_run_image_shows_control_settings': True,
                 'end_of_run_capture_seconds_after_deadline': 0.018561, 'stability_operator_confirmed_as_worded': True},
    'recording': {'reset_release_utc': st['recording_start_utc'], 'fixed_deadline_utc': st['fixed_deadline_utc'], 'deadline_observed_lateness_ms': st['deadline_observed_lateness_ms'], 'boot_session_id': f'HBPSN-09/{st["recording_start_utc"]}', 'assigned_ip': st['startup']['assigned_ip']},
    'counts': {'raw_serial_lines': len((A / 'serial.raw.log').read_bytes().splitlines()), 'raw_rtt': st['all_rtt_count'], 'warmup_excluded': st['all_rtt_count'] - st['eligible_count'], 'eligible': st['eligible_count'], 'selected': 415, 'eligible_extras': st['eligible_count'] - 415, 'shortfall': 0, 'first_selected_seq': st['first_selected_seq'], 'last_selected_seq': st['last_selected_seq']},
    'statistics': {'n': 415, 'mean_ms': st['mean_ms'], 'sd_ms': SD, 'sd_definition': 'Sample SD (n-1), computed from selected_first_415.csv at review; not stored in statistics.json', 'median_ms': st['median_ms'], 'p95_ms': P95, 'p95_definition': 'Nearest rank 395 of 415', 'minimum_ms': o[0], 'maximum_ms': o[-1]},
    'settings_evidence': {
        'declaration': {'file': 'clumsy_declaration.json', 'sha256': sh(A / 'clumsy_declaration.json'), 'operator_confirmed_receipt_utc': '2026-11-09T18:56:50.3253449Z', 'seconds_before_reset_release': 75.94, 'finding': 'Only evidence of the Clumsy setting values before the measured reset; the operator statement reports no change after this confirmation.'},
        'pre_run_image': {'file': 'clumsy_operator_pre_run.png', 'sha256': 'f53e9a42c848363b650e65bface150464ad874e6f29c8093431f5f9fd499ac97', 'capture_started_utc': '2026-11-09T18:58:02.971833+00:00', 'shows_clumsy': False},
        'end_of_run_image': {'file': 'clumsy_operator_end_of_run.png', 'sha256': 'b32d1b1aefdfce3603e10754f71005aca0c8f464473611787021b6608802b3d5', 'capture_started_utc': '2026-11-09T19:35:06.287243+00:00', 'shows_clumsy': True, 'settings_seen': SETTINGS_SEEN, 'windows_tray_clock_in_image': '21.35 09/11/2026',
                             'limit': 'The helper PASS for this phase came from the pre-launch declaration; the settings_seen values come from visual review of this image.'},
        'supplementary_images': [
            {'file': MID, 'role': 'mid-run', 'source_path': str(MID_SRC), 'source_file_created_and_modified_helsinki': '2026-11-09T23:45:36+02:00', 'bytes': MID_SRC.stat().st_size, 'sha256': sh(MID_SRC),
             'time_label': 'OPERATOR-STATED: 21:17 Helsinki during the run. Not machine-recorded.', 'clocks_visible_in_image': 'Windows tray 21.17 09/11/2026 and outer remote-client shelf 21:17',
             'content_bound': 'The terminal in the image shows the helper waiting for end_of_run, which it answered at 19:35:06Z, and the chat panel cites the 18:58:06Z reset, so the image is from inside the run if it is an unaltered capture.',
             'source_file_time_note': 'The file time is when the file reached this laptop, not capture time. Filename prefix 1794251880985 reads as 2026-11-09T19:18:00.985Z if it is epoch milliseconds; this is not relied on.',
             'settings_seen': SETTINGS_SEEN, 'indicator_dot_next_to_stop': 'green', 'inspection': 'Visual review; not machine-read'},
            {'file': LATE, 'role': 'late post-run', 'source_path': str(LATE_SRC), 'source_file_created_and_modified_helsinki': '2026-11-09T23:44:08+02:00', 'bytes': LATE_SRC.stat().st_size, 'sha256': sh(LATE_SRC),
             'time_label': 'OPERATOR-STATED: about 23:44 Helsinki, about 2 h 09 min after the deadline. No clock in the image; file name and file time agree.',
             'settings_seen': SETTINGS_SEEN, 'indicator_dot_next_to_stop': 'grey', 'inspection': 'Visual review; not machine-read', 'limit': 'Shows the state after the recording, not during it.'}],
        'indicator_dot_note': 'The dot beside Stop is green in the 21:17 image and grey in the end-of-run and 23:44 images. Its meaning was not established; the button and status line are the same in all three.'},
    'warnings': st['warning_error_lines'], 'errors': st['connection_error_lines'],
    'server_stderr': {'text': st['server_stderr'], 'host_receipt_utc': '2026-11-09T18:59:03.624352+00:00', 'cause': 'Not established; not declared harmless',
                      'context': 'Received 62 ms after server stdout for seq 10 at 18:59:03.562Z. No serial connection error, disconnect or sequence gap.', 'register_count_treatment': 'Counted as 1, as in HBPSN-04 and HBPSN-07; the collector request counted serial lines only and gave 0.'},
    'resets': st['resets'], 'automatic_flags_preserved': F,
    'setup_notes': {'identification_log': 'Derived from the setup flash output; no separate flash-id command was run.', 'listener': 'Get-NetTCPConnection shows a blank state and netstat no LISTENING entry for 14568; functional TLS probe passed. Same discrepancy as HBPSN-04.',
                    'test_capture': 'The test capture did not show Clumsy and the operator launched without a second test.',
                    'host_activity': 'Chrome Remote Desktop session visible at 21:17; web browser windows open on the second display at end of run. Network use was not measured; see operator_host_activity_statement.',
                    'register': 'Row 9 stayed NOT_RUN during the run; register_running_request.json and register_final_request.json were not applied automatically and are applied by this review.'},
    'post_finalization_state_at_draft': {'observed_utc': '2026-11-09T21:47:52Z', 'still_running_pids': [37648, 9492, 32352, 9592], 'monitor_logs': 'monitor_stream.log (187723 bytes) and monitor_after_run.log (133411 bytes) were still open and growing, are not in SHA256SUMS.json and are not cited by this review. Statistics come from serial.raw.log-derived files only.'},
    'retained_flags': FLAGS,
    'register_patch_source': ['register_running_request.json', 'register_final_request.json', 'this review'],
    'only_hbpsn09_row_changes': True, 'unresolved_quic_crash_preserved': True, 'next_run_started': False,
}
review_text = json.dumps(review, indent=2)

# CSV: exactly one physical line
raw_old = CSV.read_bytes()
lines = raw_old.splitlines(keepends=True)
reg = list(csv.DictReader(io.StringIO(raw_old.decode('utf-8'))))
fields = list(reg[0])
assert reg[8]['run_id'] == 'HBPSN-09' and reg[8]['status'] == 'NOT_RUN'
patch = {'status': 'COMPLETE with retained flags', 'preflight_status': 'PASS', 'startup_status': 'PASS', 'settings_evidence_type': SETTINGS_TYPE,
         'boot_session_id': review['recording']['boot_session_id'], 'reset_release_utc': st['recording_start_utc'], 'recording_end_utc': st['fixed_deadline_utc'],
         'actual_duration_seconds': '2220', 'actual_assigned_ip': st['startup']['assigned_ip'], 'eligible_count': '431', 'selected_count': '415', 'shortfall': '0',
         'connection_error_count': '1', 'sequence_gap_count': '0', 'mean_app_rtt_ms': repr(st['mean_ms']), 'minimum_app_rtt_ms': repr(o[0]), 'maximum_app_rtt_ms': repr(o[-1]),
         'metadata_path': META, 'raw_serial_path': f'runs/HBPSN-09/{ATT}/serial.raw.log', 'deviation_reason': DEVIATION}
target = dict(reg[8]); target.update(patch)
s = io.StringIO(newline='')
csv.DictWriter(s, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator='\r\n').writerow(target)
new_lines = list(lines); new_lines[9] = s.getvalue().encode('utf-8')
csv_new = b''.join(new_lines)

# XLSX: replace cell bytes inside row 10 only; row 10 uses the x: prefix
with zipfile.ZipFile(XL) as z:
    infos = z.infolist(); parts = {i.filename: z.read(i.filename) for i in infos}
x_old = parts[SHEET]
ROW = rb'<(?:\w+:)?row\b[^>]*\br="10"[^>]*>.*?</(?:\w+:)?row>'
m = re.search(ROW, x_old, re.S)
row_old = m.group()
assert row_old.startswith(b'<x:row')


def cell_re(ref):
    return re.compile(rb'<x:c\b[^>]*\br="' + ref.encode() + rb'"[^>]*?(?:/>|>.*?</x:c>)', re.S)


def setcell(row, ref, build):
    f = cell_re(ref).search(row); assert f, ref
    st_ = re.search(rb'\bs="(\d+)"', f.group()).group(1)
    return row[:f.start()] + build(st_) + row[f.end():]


def text(ref, val):
    return lambda q: b'<x:c r="' + ref.encode() + b'" s="' + q + b'" t="inlineStr"><x:is><x:t>' + escape(val).encode('utf-8') + b'</x:t></x:is></x:c>'


def num(ref, val):
    return lambda q: b'<x:c r="' + ref.encode() + b'" s="' + q + b'"><x:v>' + str(val).encode() + b'</x:v></x:c>'


formula = re.search(rb'<x:f>(.*?)</x:f>', cell_re('AA10').search(row_old).group(), re.S).group(1)
assert formula == b'IF(ISNUMBER(Z10),MAX(0,J10-Z10),"")', formula
row_new = row_old
for ref, key in [('G10', 'status'), ('Q10', 'preflight_status'), ('R10', 'startup_status'), ('S10', 'settings_evidence_type'), ('T10', 'boot_session_id'), ('U10', 'reset_release_utc'), ('V10', 'recording_end_utc'), ('X10', 'actual_assigned_ip'), ('AG10', 'metadata_path'), ('AH10', 'raw_serial_path'), ('AI10', 'deviation_reason')]:
    row_new = setcell(row_new, ref, text(ref, patch[key]))
for ref, key in [('W10', 'actual_duration_seconds'), ('Y10', 'eligible_count'), ('Z10', 'selected_count'), ('AB10', 'connection_error_count'), ('AC10', 'sequence_gap_count'), ('AD10', 'mean_app_rtt_ms'), ('AE10', 'minimum_app_rtt_ms'), ('AF10', 'maximum_app_rtt_ms')]:
    row_new = setcell(row_new, ref, num(ref, patch[key]))
row_new = setcell(row_new, 'AA10', lambda q: b'<x:c r="AA10" s="' + q + b'"><x:f>' + formula + b'</x:f><x:v>0</x:v></x:c>')
x_new = x_old[:m.start()] + row_new + x_old[m.end():]
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as out:
    for i in infos:
        out.writestr(i, x_new if i.filename == SHEET else parts[i.filename])
xl_new = buf.getvalue()


def verify(csv_before, csv_after, xl_before, xl_after):
    a, b = csv_before.splitlines(keepends=True), csv_after.splitlines(keepends=True)
    print('CSV line count', len(a), len(b), 'changed physical lines', [i for i in range(len(a)) if a[i] != b[i]])
    print('CSV header+rows1-8 sha before', b_sh(b''.join(a[:9])), 'after', b_sh(b''.join(b[:9])))
    print('CSV rows10-18 sha before', b_sh(b''.join(a[10:])), 'after', b_sh(b''.join(b[10:])))
    assert a[:9] == b[:9] and a[10:] == b[10:]
    p_before, p_after = list(csv.DictReader(io.StringIO(csv_before.decode()))), list(csv.DictReader(io.StringIO(csv_after.decode())))
    print('CSV row 9 fields changed', sorted(k for k in fields if p_before[8][k] != p_after[8][k]))
    assert all(p_after[8][k] == patch[k] for k in patch)
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with zipfile.ZipFile(io.BytesIO(xl_before)) as za, zipfile.ZipFile(io.BytesIO(xl_after)) as zb:
        assert za.testzip() is None and zb.testzip() is None
        print('XLSX parts same list', za.namelist() == zb.namelist(), 'parts with changed bytes', [n for n in za.namelist() if za.read(n) != zb.read(n)])
        sa, sb = za.read(SHEET), zb.read(SHEET)
    ma, mb = re.search(ROW, sa, re.S), re.search(ROW, sb, re.S)
    print('XLSX sheet bytes outside row 10 identical', sa[:ma.start()] == sb[:mb.start()] and sa[ma.end():] == sb[mb.end():])

    def cells(raw):
        out = {}
        for r in E.fromstring(raw).iter(ns + 'row'):
            out[('row', r.get('r'))] = dict(r.attrib)
            for c in r:
                out[c.get('r')] = (dict(c.attrib), E.tostring(c))
        return out
    ca, cb = cells(sa), cells(sb)
    assert set(ca) == set(cb)
    in_row = lambda k: isinstance(k, str) and re.fullmatch(r'[A-Z]+10', k)
    outside = [k for k in ca if not in_row(k) and k != ('row', '10')]
    print('XLSX cells/rows compared outside row 10', len(outside), 'differences', [k for k in outside if ca[k] != cb[k]])
    assert all(ca[k] == cb[k] for k in outside)
    print('XLSX changed cells in row 10', sorted(k for k in ca if in_row(k) and ca[k] != cb[k]))
    print('XLSX row 10 styles unchanged', all(ca[k][0].get('s') == cb[k][0].get('s') for k in ca if in_row(k)))
    print('XLSX AA10', cb['AA10'][1][:200])


if not args.apply:
    print('=== DRY RUN: nothing written')
    print(review_text)
    print('=== patch'); print(json.dumps(patch, indent=1))
    print('=== old csv line'); print(lines[9].decode())
    print('=== new csv line'); print(new_lines[9].decode())
    verify(raw_old, csv_new, XL.read_bytes(), xl_new)
    print('would-be csv sha', b_sh(csv_new), 'manual_review bytes (with placeholders)', len(review_text.encode()))
    raise SystemExit

# Backups, then writes
backups = {}
for p in (CSV, XL, A / 'SHA256SUMS.json'):
    b = p.with_name(p.name + '.bak_' + ts); assert not b.exists()
    shutil.copy2(p, b); assert sh(b) == sh(p); backups[p] = b
xl_old = XL.read_bytes()
shutil.copy2(MID_SRC, A / MID); shutil.copy2(LATE_SRC, A / LATE)
assert sh(A / MID) == sh(MID_SRC) and sh(A / LATE) == sh(LATE_SRC) and MID_SRC.exists() and LATE_SRC.exists()
(A / 'manual_review.json').write_text(review_text, encoding='utf-8')
for p, data in ((CSV, csv_new), (XL, xl_new)):
    t = p.with_name(p.name + '.HBPSN09_CLOSE.tmp'); t.write_bytes(data); os.replace(t, p)
verify(raw_old, CSV.read_bytes(), xl_old, XL.read_bytes())


def entry(p, label, **more):
    return {'path': label, 'bytes': Path(p).stat().st_size, 'sha256': sh(p), **more}


rel = lambda p: Path(p).relative_to(root).as_posix()
mf = A / 'SHA256SUMS.json'
add = [entry(A / MID, MID, time_label='OPERATOR-STATED 21:17 Helsinki, mid-run'), entry(A / LATE, LATE, time_label='OPERATOR-STATED about 23:44 Helsinki, late post-run'),
       entry(A / 'manual_review.json', 'manual_review.json'), entry(backups[mf], backups[mf].name),
       entry(CSV, rel(CSV)), entry(backups[CSV], rel(backups[CSV])), entry(XL, rel(XL)), entry(backups[XL], rel(backups[XL]))]
assert not {e['path'] for e in items} & {e['path'] for e in add}
mf.write_text(json.dumps(items + add, indent=2), encoding='utf-8')
print('=== hashes', ts)
for e in add:
    print(e['path'], e['sha256'])
print('SHA256SUMS.json', sh(mf))
