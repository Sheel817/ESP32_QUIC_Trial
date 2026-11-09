"""One-shot HBPSN-08 closure writer. Run with cwd = project root."""
import csv, datetime as dt, hashlib, io, json, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
from xml.sax.saxutils import escape

root = Path.cwd()
assert (root / 'HBPSN08_TASK.md').exists()
study = root / 'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
CSV = study / 'run_register.csv'
XL = root / 'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
A10 = 'attempt_20261109T013410Z'
A39 = 'attempt_20261109T013239Z'
dirs10 = [root / 'runs/HBPSN-08' / A10, study / 'runs/HBPSN-08' / A10]
dirs39 = [root / 'runs/HBPSN-08' / A39, study / 'runs/HBPSN-08' / A39]


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


assert sh(CSV) == '79b500bf858378a0685576a8ccdd9cac07fdf010b4913f233e6431f46ebd6fb6', 'CSV changed since dry run'
assert sh(XL) == '7423b8f918e5f4700beba1067ac5b270017e9be8ee8cd920c8a985072d4a773f', 'XLSX changed since inspection'

now = dt.datetime.now(dt.timezone.utc)
ts = now.strftime('%Y%m%dT%H%M%SZ')

# 1. Backups
backups = {}
for p in [CSV, XL] + [d / 'SHA256SUMS.json' for d in dirs10 + dirs39]:
    b = p.with_name(p.name + '.bak_' + ts)
    assert not b.exists()
    shutil.copy2(p, b)
    assert sh(b) == sh(p)
    backups[str(p)] = b

# 2. Review record
DEVIATION = ('Initial boot Load access fault panic 7.57 s after reset release, then SW_CPU reboot before any APP_RTT. '
             'FAILED_STARTUP; 0 eligible of 439 recorded; post-reboot RTTs excluded. Same MEPC/RA as HBPSN-03; root cause '
             'not established. Device bootloader stamp matches TCP_TLS_PSN, no HBPSN-08 flash record. Earlier attempt 013239Z '
             'issued a measured reset and was aborted after 7.53 s; see its note.')
META = f'runs/HBPSN-08/{A10}/manual_review.json'
review = {
    'run_id': 'HBPSN-08',
    'attempt_id': A10,
    'transport': 'QUIC',
    'condition': 'LAG100_OUT',
    'boot_replicate': 2,
    'disposition': 'FAILED_STARTUP',
    'validity_status': 'NOT_APPROVED',
    'reason': 'Uncontrolled SW_CPU reboot after Guru Meditation panic 7.57 s after reset release; 0 eligible of 439 recorded.',
    'reviewed_utc': now.isoformat(),
    'operator_decision': {
        'exact_statement': 'I am the operator and I accept HBPSN-08 attempt_20261109T013410Z as FAILED_STARTUP.',
        'relayed': False,
        'receipt_utc': '2026-11-09T18:06:20.7522475Z',
        'receipt_helsinki': '2026-11-09T20:06:20.7522475+02:00',
        'receipt_clock_source': 'First local clock observation while processing the operator decision message; original message send time unavailable',
        'statement_selection': 'The decision message contained template text for this field; the operator then selected this example sentence, unchanged, in the session question dialog.',
    },
    'reset_release_utc': '2026-11-09T01:34:15.271402+00:00',
    'fixed_deadline_utc': '2026-11-09T02:11:15.271435+00:00',
    'panic_after_release_seconds': 7.565793,
    'counts': {'raw_serial_lines': 787, 'raw_rtt': 439, 'eligible': 0, 'selected': 0, 'shortfall': 415,
               'excluded_subsequent_boot_or_timestamp_regression': 439},
    'statistics': {'mean_ms': None, 'sd_ms': None, 'median_ms': None, 'p95_ms': None, 'minimum_ms': None, 'maximum_ms': None},
    'evidence_lines': [
        {'line': 145, 'host_receipt_utc': '2026-11-09T01:34:22.837195+00:00', 'raw_line': "Guru Meditation Error: Core  0 panic'ed (Load access fault). Exception was unhandled."},
        {'line': 197, 'host_receipt_utc': '2026-11-09T01:34:23.175037+00:00', 'raw_line': 'Rebooting...'},
        {'line': 198, 'host_receipt_utc': '2026-11-09T01:34:23.224946+00:00', 'raw_line': 'ESP-ROM:esp32c6-20220919'},
        {'line': 200, 'host_receipt_utc': '2026-11-09T01:34:23.224946+00:00', 'raw_line': 'rst:0xc (SW_CPU),boot:0x6c (SPI_FAST_FLASH_BOOT)'},
    ],
    'panic_decode': {
        'application_elf_sha256': '9b23e164f8d6fd4702450b687c76ef3fa8ced802945dc23dd2f4d102c35c0f3d',
        'rom_elf_sha256': '788e1d38724aeb8fd974fa10c4a7b089c02627d35342ce84b9e0b12b239f3551',
        'mepc': '0x40021c40 tlsf_free+0x42',
        'ra': '0x400225c4 multi_heap_free_impl+0x46',
        'mcause': '0x5',
        'mtval': '0x41847f24',
        'faulting_instruction': 'lw a4,4(a5)',
        'computed_block_size': '0x01000000',
        'candidate_stack_not_verified_unwind': ['heap_caps_free', 'free', 'default_free', 'ngtcp2_mem_free', 'pktns_del', 'conn_discard_pktns', 'ngtcp2_conn_discard_initial_state', 'conn_write_handshake_pkts'],
        'same_fault_as': 'HBPSN-03 (identical MEPC and RA)',
        'root_cause': 'Not established',
    },
    'firmware_identity': {
        'printed_elf_prefix': '9b23e164f; prefix comparison, not a full on-device digest',
        'printed_bootloader_compile_time': 'Nov  4 2026 01:52:32; matches frozen TCP_TLS_PSN bootloader, not frozen QUIC_PSN bootloader (Nov  3 2026 18:33:04)',
        'flash_record': 'None found for HBPSN-08',
    },
    'post_recording_screenshot': 'clumsy_post_manual.png not found in attempt folder, project root or runs/HBPSN-08',
    'post_reboot_rtts': 'Retained in all_rtts.csv and excluded_rtts.csv; not selected or concatenated',
    'retained_flags': ['BOOTLOADER_STAMP_MATCHES_TCP_TLS_NOT_QUIC', 'NO_FLASH_RECORD_FOR_RUN', 'POST_SCREENSHOT_NOT_FOUND'],
}
NOTE = """# HBPSN-08 attempt_20261109T013239Z: aborted

Reset release 2026-11-09T01:32:39.970769Z (collector PID 32192). Last heartbeat 01:32:46.127979Z.
Last serial receipt 01:32:47.503820Z, 7.53 s after release. 145 serial lines, 0 APP_RTT, one ROM banner,
no panic, startup gates not verified, no finalization files. collector.stderr.log is empty.
The reason it stopped is not recorded.

This attempt set row 8 of run_register.csv and run_register.xlsx to RUNNING (logged 01:32:39.983212Z).
Attempt 013410Z overwrote those row 8 values at 01:34:15Z and set startup PASS at 01:34:32Z.

Deviation: this attempt issued a measured reset, and the plan has no rule for a second measured reset
under one run ID. Its log ends before the point where HBPSN-03 panicked, so it is not evidence of a crash-free boot.
"""
for d in dirs10:
    assert not (d / 'manual_review.json').exists()
    (d / 'manual_review.json').write_text(json.dumps(review, indent=2), encoding='utf-8')
for d in dirs39:
    assert not (d / 'ABORTED_ATTEMPT_NOTE.md').exists()
    (d / 'ABORTED_ATTEMPT_NOTE.md').write_bytes(NOTE.encode('utf-8'))

# 3. CSV: replace exactly one physical line
raw_old = CSV.read_bytes()
lines = raw_old.splitlines(keepends=True)
rows = list(csv.DictReader(io.StringIO(raw_old.decode('utf-8'))))
fields = list(rows[0].keys())
assert rows[7]['run_id'] == 'HBPSN-08' and rows[7]['status'] == 'RUNNING'
patch = {'status': 'FAILED_STARTUP', 'startup_status': 'FAIL', 'eligible_count': '0', 'selected_count': '0', 'shortfall': '415',
         'metadata_path': META, 'deviation_reason': DEVIATION}
target = dict(rows[7])
target.update(patch)
s = io.StringIO(newline='')
csv.DictWriter(s, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator='\r\n').writerow(target)
new_lines = list(lines)
new_lines[8] = s.getvalue().encode('utf-8')
raw_new = b''.join(new_lines)
tmp = CSV.with_name(CSV.name + '.HBPSN08_CLOSE.tmp')
tmp.write_bytes(raw_new)
os.replace(tmp, CSV)

# 4. XLSX: replace cell bytes inside row 9 only; keep the AA9 formula
SHEET = 'xl/worksheets/sheet1.xml'
with zipfile.ZipFile(XL) as z:
    infos = z.infolist()
    parts = {i.filename: z.read(i.filename) for i in infos}
x_old = parts[SHEET]
m = re.search(rb'<(?:\w+:)?row\b[^>]*\br="9"[^>]*>.*?</(?:\w+:)?row>', x_old, re.S)
assert m
row_old = m.group()
print('row 9 formulas:', re.findall(rb'r="([A-Z]+9)"[^>]*><ns0:f>(.*?)</ns0:f>', row_old))


def cell_re(ref):
    return re.compile(rb'<ns0:c\b[^>]*\br="' + ref.encode() + rb'"[^>]*?(?:/>|>.*?</ns0:c>)', re.S)


def setcell(row, ref, payload):
    pat = cell_re(ref)
    found = pat.search(row)
    assert found, ref
    style = re.search(rb'\bs="(\d+)"', found.group()).group(1)
    return row[:found.start()] + payload(style) + row[found.end():]


def text(ref, value):
    return lambda st: b'<ns0:c r="' + ref.encode() + b'" s="' + st + b'" t="inlineStr"><ns0:is><ns0:t>' + escape(value).encode('utf-8') + b'</ns0:t></ns0:is></ns0:c>'


def num(ref, value):
    return lambda st: b'<ns0:c r="' + ref.encode() + b'" s="' + st + b'"><ns0:v>' + str(value).encode() + b'</ns0:v></ns0:c>'


formula = re.search(rb'<ns0:f>(.*?)</ns0:f>', cell_re('AA9').search(row_old).group(), re.S).group(1)
assert formula == b'IF(ISNUMBER(Z9),MAX(0,J9-Z9),"")', formula
row_new = row_old
for ref, val in [('G9', 'FAILED_STARTUP'), ('R9', 'FAIL'), ('AG9', META), ('AI9', DEVIATION)]:
    row_new = setcell(row_new, ref, text(ref, val))
row_new = setcell(row_new, 'Y9', num('Y9', 0))
row_new = setcell(row_new, 'Z9', num('Z9', 0))
row_new = setcell(row_new, 'AA9', lambda st: b'<ns0:c r="AA9" s="' + st + b'"><ns0:f>' + formula + b'</ns0:f><ns0:v>415</ns0:v></ns0:c>')
x_new = x_old[:m.start()] + row_new + x_old[m.end():]
tmp = XL.with_name(XL.name + '.HBPSN08_CLOSE.tmp')
with zipfile.ZipFile(tmp, 'w') as out:
    for i in infos:
        out.writestr(i, x_new if i.filename == SHEET else parts[i.filename])
os.replace(tmp, XL)

# 5. Verification
print('=== CSV')
after = CSV.read_bytes().splitlines(keepends=True)
before = Path(backups[str(CSV)]).read_bytes().splitlines(keepends=True)
print('line count', len(before), len(after), 'changed physical lines', [i for i in range(len(before)) if before[i] != after[i]])
print('header+rows1-7 sha before', hashlib.sha256(b''.join(before[:8])).hexdigest(), 'after', hashlib.sha256(b''.join(after[:8])).hexdigest())
print('rows9-18 sha before', hashlib.sha256(b''.join(before[9:])).hexdigest(), 'after', hashlib.sha256(b''.join(after[9:])).hexdigest())
assert before[:8] == after[:8] and before[9:] == after[9:]
print('=== XLSX')
ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
with zipfile.ZipFile(backups[str(XL)]) as a, zipfile.ZipFile(XL) as b:
    assert a.testzip() is None and b.testzip() is None
    print('parts same list', a.namelist() == b.namelist())
    diff_parts = [n for n in a.namelist() if a.read(n) != b.read(n)]
    print('parts with changed bytes', diff_parts)
    sa, sb = a.read(SHEET), b.read(SHEET)
    ma, mb = re.search(rb'<(?:\w+:)?row\b[^>]*\br="9"[^>]*>.*?</(?:\w+:)?row>', sa, re.S), re.search(rb'<(?:\w+:)?row\b[^>]*\br="9"[^>]*>.*?</(?:\w+:)?row>', sb, re.S)
    print('sheet bytes outside row 9 identical', sa[:ma.start()] == sb[:mb.start()] and sa[ma.end():] == sb[mb.end():])
    ta, tb = E.fromstring(sa), E.fromstring(sb)


def cells(tree):
    out = {}
    for r in tree.iter(ns + 'row'):
        out[('row', r.get('r'))] = dict(r.attrib)
        for c in r:
            out[c.get('r')] = (dict(c.attrib), E.tostring(c))
    return out


ca, cb = cells(ta), cells(tb)
assert set(ca) == set(cb)
outside = [k for k in ca if not (isinstance(k, str) and re.fullmatch(r'[A-Z]+9', k)) and k != ('row', '9')]
print('cells/rows compared outside row 9:', len(outside), 'differences:', [k for k in outside if ca[k] != cb[k]])
assert all(ca[k] == cb[k] for k in outside)
inside = sorted(k for k in ca if isinstance(k, str) and re.fullmatch(r'[A-Z]+9', k) and ca[k] != cb[k])
print('changed cells in row 9:', inside)
print('row 9 styles unchanged:', all(ca[k][0].get('s') == cb[k][0].get('s') for k in ca if isinstance(k, str) and re.fullmatch(r'[A-Z]+9', k)))
print('AA9 now:', cb['AA9'][1][:220])

# 6. Manifests
def entry(p, label):
    return {'path': label, 'bytes': Path(p).stat().st_size, 'sha256': sh(p)}


rel = lambda p: Path(p).relative_to(root).as_posix()
for d in dirs10:
    mf = d / 'SHA256SUMS.json'
    data = json.loads(mf.read_text(encoding='utf-8'))
    names = {e['path'] for e in data}
    add = [entry(d / 'manual_review.json', 'manual_review.json'),
           entry(backups[str(mf)], Path(backups[str(mf)]).name),
           entry(CSV, rel(CSV)), entry(backups[str(CSV)], rel(backups[str(CSV)])),
           entry(XL, rel(XL)), entry(backups[str(XL)], rel(backups[str(XL)]))]
    assert not names & {e['path'] for e in add}
    mf.write_text(json.dumps(data + add, indent=2), encoding='utf-8')
for d in dirs39:
    mf = d / 'SHA256SUMS.json'
    data = json.loads(mf.read_text(encoding='utf-8'))
    add = [entry(d / 'ABORTED_ATTEMPT_NOTE.md', 'ABORTED_ATTEMPT_NOTE.md'), entry(backups[str(mf)], Path(backups[str(mf)]).name)]
    mf.write_text(json.dumps(data + add, indent=2), encoding='utf-8')

print('=== run vs mirror')
for a, b, n in [(dirs10[0], dirs10[1], 'manual_review.json'), (dirs10[0], dirs10[1], 'SHA256SUMS.json'), (dirs39[0], dirs39[1], 'ABORTED_ATTEMPT_NOTE.md'), (dirs39[0], dirs39[1], 'SHA256SUMS.json')]:
    print(n, sh(a / n) == sh(b / n), sh(a / n))
print('=== hashes')
print('timestamp', ts, 'reviewed_utc', now.isoformat())
for p in [CSV, XL]:
    print(rel(p), sh(p), 'backup', rel(backups[str(p)]), sh(backups[str(p)]))
for d in dirs10 + dirs39:
    print(rel(d / 'SHA256SUMS.json'), sh(d / 'SHA256SUMS.json'))
