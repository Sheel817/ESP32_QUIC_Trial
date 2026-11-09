"""Create the HBPSN-09 attempt folder. No COM6, no launch. cwd = project root."""
import datetime as dt, difflib, hashlib, json, shutil, subprocess
from pathlib import Path

root = Path.cwd()
assert (root / 'HBPSN08_TASK.md').exists()
study = root / 'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
tools = root / 'tools/run_recorder'
A = {'HBPSN-04': study / 'runs/HBPSN-04/attempt_20261106T020052Z_host_preflight_continuation',
     'HBPSN-06': study / 'runs/HBPSN-06/attempt_20261107T015952Z',
     'HBPSN-07': study / 'runs/HBPSN-07/attempt_20261107T030606Z'}
CODE = ['collector_v2.py', 'reliability.py', 'monitor_instrumented_v2.py']
pre = root / 'runs/HBPSN-09/preflight_20261109T180918Z'


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Reference hashes must agree across all three runs
refs = {k: {f['path']: f['sha256'] for f in json.loads((d / 'collector_version.json').read_text(encoding='utf-8-sig'))['files']} for k, d in A.items()}
assert refs['HBPSN-04'] == refs['HBPSN-06'] == refs['HBPSN-07'] and set(refs['HBPSN-04']) == set(CODE)
want = refs['HBPSN-04']

# Frozen and configuration inputs
src = json.loads((A['HBPSN-04'] / 'preflight.json').read_text(encoding='utf-8'))
assert sh(study / 'EXPERIMENT_PLAN_PROPOSED_V1.md') == src['plan_sha256']
assert sh(study / 'freeze_manifest.json') == src['freeze_manifest_sha256']
for group in ('firmware_artifacts', 'configuration'):
    for item in src[group]:
        assert sh(item['path']) == item['sha256'], item['path']
assert sh('C:/Users/newsh/Downloads/clumsy-0.3-win64-a/clumsy.exe') == src['clumsy_executable_sha256']
assert sh(root / 'tcp_tls_server.py') == src['server_readiness']['source_sha256']
assert sh(root / 'server-cert.pem') == src['server_readiness']['certificate_sha256']
assert all(Path(p).exists() for p in src['server_log_sources'].values())
pid = subprocess.run(['powershell.exe', '-NoProfile', '-Command', '(Get-CimInstance Win32_Process -Filter "ProcessId=36536").CommandLine'], capture_output=True, text=True, timeout=30).stdout
assert 'tcp_tls_server.py' in pid, pid

now = dt.datetime.now(dt.timezone.utc)
attempt = 'attempt_' + now.strftime('%Y%m%dT%H%M%SZ')
folder = study / 'runs/HBPSN-09' / attempt
folder.mkdir(parents=True, exist_ok=False)

# 1. Code
for n in CODE:
    shutil.copy2(tools / n, folder / n)
    assert sh(folder / n) == want[n], n
    print('code', n, sh(folder / n), 'equals 04/06/07 collector_version: True')
shutil.copy2(A['HBPSN-04'] / 'collector_version.json', folder / 'collector_version.json')

# 2. preflight.json: only run_id and checked_utc change
out = dict(src)
out['run_id'] = 'HBPSN-09'
out['checked_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
old_text = (A['HBPSN-04'] / 'preflight.json').read_text(encoding='utf-8')
new_text = json.dumps(out, indent=2) + ('\n' if old_text.endswith('\n') else '')
(folder / 'preflight.json').write_text(new_text, encoding='utf-8')
print('=== preflight.json diff against HBPSN-04')
print('\n'.join(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), 'HBPSN-04/preflight.json', 'HBPSN-09/preflight.json', lineterm='', n=0)))

# 3. Setup evidence the collector requires, derived from today's real flash
rec = json.loads((pre / 'preflight_record.json').read_text(encoding='utf-8'))
fl = rec['flash']
assert fl['exit_code'] == 0 and fl['verified_image_count'] == 3 and rec['tls_probe']['passed'] is True
raw = (pre / 'flash.log').read_bytes().decode('utf-8', 'replace')
command_line = ' '.join(fl['command'])
(folder / 'flash.log').write_bytes((command_line + '\r\n' + raw).encode('utf-16'))
(folder / 'flash_result.json').write_text(json.dumps(dict(exit_code=fl['exit_code'], ended_utc=fl['ended_utc'], verified_image_count=fl['verified_image_count'], setup_only=True), indent=2), encoding='utf-8')
lines = raw.splitlines()
start = next(i for i, s in enumerate(lines) if s.startswith('esptool v'))
end = next(i for i, s in enumerate(lines) if s.startswith('MAC_EXT'))
header = 'DERIVED EXTRACT of the esptool output from the HBPSN-09 setup flash at ' + fl['started_utc'] + '. No separate flash-id command was run and COM6 was not opened for this file.'
(folder / 'identification.log').write_bytes((header + '\r\n' + '\r\n'.join(lines[start:end + 1]) + '\r\n').encode('utf-16'))
(folder / 'setup_evidence_provenance.json').write_text(json.dumps(dict(
    created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    source_preflight_record=str(pre / 'preflight_record.json'), source_preflight_record_sha256=sh(pre / 'preflight_record.json'),
    source_flash_log=str(pre / 'flash.log'), source_flash_log_sha256=sh(pre / 'flash.log'),
    flash_log='UTF-16 re-encoding of the source flash log, preceded by the command line, because collector_v2.py reads flash.log as UTF-16.',
    flash_result='Values copied from the flash section of the source preflight record.',
    identification_log='Derived extract of the same esptool output, because collector_v2.py requires the board MAC in identification.log. HBPSN-04 ran a separate esptool flash-id; HBPSN-09 did not.',
    automatic_post_flash_boot='Setup only; excluded from the formal session by the measured-reset log boundaries.'), indent=2), encoding='utf-8')

# 4. Replay collector_v2.py pre-launch file checks only (lines 190-197); nothing is started
pf = json.loads((folder / 'preflight.json').read_text())
checks = {
    'preflight status PASS': pf['status'] == 'PASS',
    'no reset_event.json': not (folder / 'reset_event.json').exists(),
    'no serial.raw.log': not (folder / 'serial.raw.log').exists(),
    'flash_result exit 0': json.loads((folder / 'flash_result.json').read_text(encoding='utf-8-sig'))['exit_code'] == 0,
    'flash.log has 3 verifications': (folder / 'flash.log').read_text(encoding='utf-16').count('Hash of data verified.') == 3,
    'identification.log has MAC': '40:4c:ca:56:bb:b0' in (folder / 'identification.log').read_text(encoding='utf-16'),
    'firmware hashes': all(sh(a['path']) == a['sha256'] for a in pf['firmware_artifacts']),
    'configuration hashes': all(sh(a['path']) == a['sha256'] for a in pf['configuration']),
    'plan hash': sh(study / 'EXPERIMENT_PLAN_PROPOSED_V1.md') == pf['plan_sha256'],
    'study path depth': folder.parents[2] == study,
}
print('=== collector pre-launch file checks')
for k, v in checks.items():
    print(v, k)
assert all(checks.values())
print('=== folder', folder)
for p in sorted(folder.iterdir()):
    print(p.name, p.stat().st_size, sh(p))
