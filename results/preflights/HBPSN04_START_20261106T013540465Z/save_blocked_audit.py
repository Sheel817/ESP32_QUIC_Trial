"""Read-only validation of inputs; writes new preflight audit files only."""
from pathlib import Path
import csv, datetime as dt, hashlib, json, zipfile, xml.etree.ElementTree as E

out = Path(__file__).resolve().parent
root = out.parents[2]
study = root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
profile = root/'profiles/tcp_tls_wifi_ps_none_20261104'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name, value):
    with (out/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
rows = list(csv.DictReader((study/'run_register.csv').open(newline='', encoding='utf-8-sig')))
assert [r['status'] for r in rows[:4]] == ['FAILED_SETTINGS','COMPLETE','FAILED_STARTUP','NOT_RUN']
assert [rows[3][k] for k in ('run_id','transport','condition')] == ['HBPSN-04','TCP_TLS','CONTROL']
xlsx = root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
ns = {'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(xlsx) as archive:
    strings = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        strings = [''.join(x.itertext()) for x in E.fromstring(archive.read('xl/sharedStrings.xml')).findall('x:si',ns)]
    workbook_rows = []
    for row in E.fromstring(archive.read('xl/worksheets/sheet1.xml')).findall('.//x:sheetData/x:row',ns):
        values = {}
        for cell in row.findall('x:c',ns):
            value = cell.find('x:v',ns)
            text = value.text if value is not None else ''
            if cell.get('t') == 's': text = strings[int(text)]
            elif cell.get('t') == 'inlineStr': text = ''.join(cell.find('x:is',ns).itertext())
            values[''.join(c for c in cell.get('r') if c.isalpha())] = text
        workbook_rows.append(values)
for a,b in zip(rows,workbook_rows[1:]):
    assert all(a[k] == b[col] for k,col in [('run_id','C'),('transport','D'),('condition','E'),('status','G')])
assert sha(study/'run_register.csv') == '656b5c6a71cbe783c66b9fe14f74551776e09522a7354ab9b385fb1baa908aae'
assert sha(xlsx) == '63980c1b51d42099f00867e52a48dec17d91c53eb4dc8d8e32e1f12f936d78ea'
manifest = json.loads((study/'freeze_manifest.json').read_text())
validation = json.loads((profile/'validation.json').read_text())
artifacts = [dict(**a, actual_sha256=sha(a['path']), matches=sha(a['path'])==a['sha256']) for a in validation['artifacts'].values()]
assert all(a['matches'] for a in artifacts)
assert all(sha(a['path'])==a['sha256'] for a in manifest['artifacts'] if a['transport']=='TCP_TLS')
plan_hash = sha(study/'EXPERIMENT_PLAN_PROPOSED_V1.md')
assert plan_hash == '6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be'
diag = root/'results/diagnostics/TEST_ONLY_QUIC_HEAP_20261106T004758540Z'
dm = json.loads((diag/'SHA256SUMS.json').read_text())
assert all(sha(diag/a['path'])==a['sha256'] for a in dm['files'])
system = json.loads((out/'system_after_relaunch.json').read_text(encoding='utf-8-sig'))
save('PREFLIGHT_BLOCKED.json', dict(status='PREFLIGHT_BLOCKED_NOT_RUN', checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(), run_id='HBPSN-04', transport='TCP_TLS', condition='CONTROL', blocker='Fresh READY present but no confirmed TCP14568 LISTENING socket; raw CIM displayed State0, serialized State null, netstat no14568 listener. Cause unknown.', plan_sha256=plan_hash, both_registers_schedule_status_agree=True, register_hashes={str(p):sha(p) for p in [study/'run_register.csv',xlsx]}, artifacts=artifacts, diagnostic_stable_deliverables_unchanged=True, diagnostic_logger_closed=False, com6_opened=False, flash_attempted=False, reset_attempted=False, timer_started=False, settings_changed=False, registers_modified=False, previous_outcomes={r['run_id']:r['status'] for r in rows[:3]}, quic_crash='UNRESOLVED', system=system))
files = [dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file() and p.name not in ('SHA256SUMS.json','tcp_tls_server.stdout.log','tcp_tls_server.stderr.log')]
save('SHA256SUMS.json', dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), files=files, excluded_live=['tcp_tls_server.stdout.log','tcp_tls_server.stderr.log']))
print('PREFLIGHT_BLOCKED_NOT_RUN; formal artifacts verified; both registers and26 stable TEST_ONLY deliverables unchanged')
