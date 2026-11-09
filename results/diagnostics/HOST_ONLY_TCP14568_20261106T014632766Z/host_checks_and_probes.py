"""HOST_ONLY: read listener state and perform exactly two authorized TLS probes.
No MQTT, serial, process control, configuration or formal-register writes.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import socket
import ssl
import subprocess
import sys
import time
import traceback

out = Path(__file__).resolve().parent
root = out.parents[2]
source = root/'tcp_tls_server.py'
server_logs = root/'results/preflights/HBPSN04_START_20261106T013540465Z'
paths = {name:server_logs/f'tcp_tls_server.{name}.log' for name in ['stdout','stderr']}
paths['sensor_csv'] = root/'logs/sensor_tcp_tls_20261106T013631_157099Z_mrgf6j6d.csv'
study = root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
protected_paths = [source,root/'quic_server.py',root/'server-cert.pem',root/'server-key.pem',study/'EXPERIMENT_PLAN_PROPOSED_V1.md',study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx']
commands = []
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def save(name,value):
    with (out/name).open('x',encoding='utf-8') as f: json.dump(value,f,indent=2)
def boundary(label):
    stamp=utc();result={}
    for name,path in paths.items():
        end=path.stat().st_size
        with path.open('rb') as f: data=f.read(end)
        assert len(data)==end
        target=out/f'{label}.server.{name}.snapshot.log'
        target.write_bytes(data)
        result[name]=dict(source=str(path),byte_offset=end,prefix_sha256=sha(data),snapshot=target.name)
    value=dict(label='HOST_ONLY_PROBE_ASSOCIATED_NOT_FORMAL',utc=stamp,streams=result)
    save(label+'.boundaries.json',value)
    return value
def run(name,args):
    started=utc();begin=time.monotonic()
    try:
        p=subprocess.run(args,cwd=root,capture_output=True,timeout=35)
        stdout,stderr,code=p.stdout,p.stderr,p.returncode
        error=None
    except Exception:
        stdout=b'';stderr=traceback.format_exc().encode();code=None;error=traceback.format_exc()
    (out/(name+'.stdout.raw')).write_bytes(stdout)
    (out/(name+'.stderr.raw')).write_bytes(stderr)
    (out/(name+'.stdout.txt')).write_text(stdout.decode('utf-8-sig',errors='replace'),encoding='utf-8')
    (out/(name+'.stderr.txt')).write_text(stderr.decode('utf-8-sig',errors='replace'),encoding='utf-8')
    record=dict(name=name,argv=args,cwd=str(root),started_utc=started,ended_utc=utc(),elapsed_seconds=time.monotonic()-begin,exit_code=code,stdout_bytes=len(stdout),stderr_bytes=len(stderr),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr),exception=error)
    commands.append(record);save(name+'.command.json',record)
    return stdout
def ps(name,command):
    prefix="$OutputEncoding=[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $ErrorActionPreference='Stop'; "
    return run(name,[os.environ['SystemRoot']+'/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command',prefix+command])
def checks(phase):
    ps(phase+'_powershell_all_tcp','Get-NetTCPConnection | Format-List *')
    ps(phase+'_powershell_14568','Get-NetTCPConnection -LocalPort 14568 | Format-List *')
    ps(phase+'_powershell_listen','Get-NetTCPConnection -LocalPort 14568 -State Listen | Format-List *')
    ps(phase+'_cim_14568',"Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'LocalPort = 14568' | Format-List *")
    ps(phase+'_cim_state_raw',"Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'LocalPort = 14568' | ForEach-Object { $_.CimInstanceProperties | Format-List * }")
    run(phase+'_netstat',[os.environ['SystemRoot']+'/System32/netstat.exe','-ano','-p','TCP'])

assert str(Path(sys.prefix).resolve()).lower()==str((root/'.quic-venv').resolve()).lower(),sys.prefix
assert not (out/'PROBES_STARTED.json').exists(),'Never rerun these probes'
protected_before={str(p):sha(p.read_bytes()) for p in protected_paths}
save('protected_before.json',protected_before)
(out/'tcp_tls_server.source.snapshot.py').write_bytes(source.read_bytes())
(out/'asyncio_base_events.snapshot.py').write_bytes((Path(sys.base_prefix)/'Lib/asyncio/base_events.py').read_bytes())
save('runtime.json',dict(utc=utc(),python=sys.executable,prefix=sys.prefix,version=sys.version,openssl=ssl.OPENSSL_VERSION,timeout_seconds=5,timeout_scope='Single shared five-second TCP+TLS deadline per address; no retries',certificate_policy='Existing lab CERT_NONE / hostname verification disabled; explicit post-handshake DER SHA256 pin comparison',mqtt_packets_sent=0))
identity_bytes=ps('server_identity',"Get-CimInstance Win32_Process -Filter 'ProcessId=36536' | ConvertTo-Json -Depth 8")
identity=json.loads(identity_bytes.decode('utf-8-sig'))
assert identity['ProcessId']==36536 and 'ESP32_QUIC_Trial' in identity['CommandLine'] and '.quic-venv' in identity['CommandLine'] and 'tcp_tls_server.py' in identity['CommandLine']
schema_path=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules/NetTCPIP/MSFT_NetTCPConnection.cdxml'
(out/'MSFT_NetTCPConnection.cdxml.snapshot').write_bytes(schema_path.read_bytes())
ps('cim_state_schema',"$s=(Get-CimClass -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection).CimClassProperties['State']; $s | Format-List *; $s.Qualifiers | ForEach-Object { $_ | Format-List *; $_.Value | Out-String -Width 4096 }")
initial=boundary('before_checks')
checks('before')
pem=(root/'server-cert.pem').read_text()
expected_der=ssl.PEM_cert_to_DER_cert(pem)
expected=sha(expected_der)
save('expected_certificate.json',dict(pem_file=str(root/'server-cert.pem'),pem_file_sha256=sha(pem.encode()),certificate_der_sha256=expected,preserved_pem_sha256='dad4aa42a253793e77b161ac0846e6a1b39447b4d207572739b24b41dbfce462'))
assert sha((root/'server-cert.pem').read_bytes())=='dad4aa42a253793e77b161ac0846e6a1b39447b4d207572739b24b41dbfce462'
save('PROBES_STARTED.json',dict(utc=utc(),addresses=['127.0.0.1','192.168.137.1'],one_attempt_each=True))
results=[]
for ordinal,host in enumerate(['127.0.0.1','192.168.137.1'],1):
    before=boundary(f'probe_{ordinal}_before')
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
    ctx.minimum_version=ssl.TLSVersion.TLSv1_3;ctx.maximum_version=ssl.TLSVersion.TLSv1_3
    ctx.set_alpn_protocols(['mqtt'])
    sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);wrapped=None
    began=time.monotonic();deadline=began+5
    record=dict(label='HOST_ONLY_PROBE_ASSOCIATED_NOT_FORMAL',ordinal=ordinal,address=host,port=14568,started_utc=utc(),tcp='NOT_ATTEMPTED',tls='NOT_ATTEMPTED',timeout_seconds=5,mqtt_packets_sent=0,exception=None)
    try:
        record['tcp']='ATTEMPTING';sock.settimeout(max(.001,deadline-time.monotonic()))
        sock.connect((host,14568));record.update(tcp='CONNECTED',tcp_completed_utc=utc(),tcp_elapsed_seconds=time.monotonic()-began,local_address=sock.getsockname(),peer_address=sock.getpeername())
        record['tls']='HANDSHAKING'
        sock.settimeout(max(.001,deadline-time.monotonic()))
        wrapped=ctx.wrap_socket(sock,server_hostname=host,do_handshake_on_connect=False)
        wrapped.settimeout(max(.001,deadline-time.monotonic()));wrapped.do_handshake()
        der=wrapped.getpeercert(binary_form=True)
        (out/f'probe_{ordinal}.peer_certificate.der').write_bytes(der)
        record.update(tls='NEGOTIATED',handshake_completed_utc=utc(),negotiated_tls=wrapped.version(),cipher=wrapped.cipher(),alpn=wrapped.selected_alpn_protocol(),local_address=wrapped.getsockname(),peer_address=wrapped.getpeername(),peer_certificate_sha256=sha(der),certificate_matches_preserved=sha(der)==expected,total_tcp_tls_seconds=time.monotonic()-began)
    except Exception as error:
        record.update(exception=dict(type=type(error).__name__,repr=repr(error),message=str(error),traceback=traceback.format_exc(),errno=getattr(error,'errno',None),winerror=getattr(error,'winerror',None)),failed_phase=record['tls'] if record['tcp']=='CONNECTED' else 'TCP_CONNECT')
        if record['tcp']=='ATTEMPTING':record['tcp']='FAILED'
        elif record['tls']=='HANDSHAKING':record['tls']='FAILED'
    finally:
        try:
            (wrapped or sock).close()
        except Exception:record['close_exception']=traceback.format_exc()
        record.update(ended_utc=utc(),elapsed_seconds=time.monotonic()-began)
    results.append(record);save(f'probe_{ordinal}.json',record)
    # Brief host-only drain interval for server stdout/stderr, never a retry.
    time.sleep(.3)
    after=boundary(f'probe_{ordinal}_after')
    for name,path in paths.items():
        first=before['streams'][name]['byte_offset'];last=after['streams'][name]['byte_offset']
        with path.open('rb') as f:f.seek(first);data=f.read(last-first)
        (out/f'probe_{ordinal}.server.{name}.delta.log').write_bytes(data)
checks('after')
final=boundary('after_checks')
save('probe_results.json',results)
save('commands.json',commands)
protected_after={str(p):sha(p.read_bytes()) for p in protected_paths}
save('protected_after.json',dict(utc=utc(),all_unchanged=protected_after==protected_before,hashes=protected_after))
assert protected_after==protected_before
print(json.dumps(dict(results=results,output_dir=str(out),protected_files_unchanged=True),indent=2))
