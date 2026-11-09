import json
import re
from pathlib import Path

profile=Path(__file__).resolve().parent
root=profile.parents[1]
quic_build=root/'profiles/wifi_ps_none_20261103/build'
tcp_build=profile/'build'
def commands(build):
    result={}
    for entry in json.loads((build/'compile_commands.json').read_text()):
        file=entry['file'].replace('\\','/')
        command=entry['command'].replace('\\','/').replace(str(build).replace('\\','/'),'<BUILD>')
        command=command.replace('-DDEMO_TRANSPORT_TCP_TLS=0','-DDEMO_TRANSPORT_TCP_TLS=<TRANSPORT>').replace('-DDEMO_TRANSPORT_TCP_TLS=1','-DDEMO_TRANSPORT_TCP_TLS=<TRANSPORT>')
        command=re.sub(r'(?<= -o )\S+','<OBJECT_DESTINATION>',command)
        file=file.replace(str(build).replace('\\','/'),'<BUILD>')
        result.setdefault(file,set()).add(command)
    return result
q=commands(quic_build)
t=commands(tcp_build)
different=[name for name in q.keys()&t.keys() if q[name]!=t[name]]
report=dict(normalization='Build directory paths, DEMO_TRANSPORT_TCP_TLS=0/1 and -o object destinations. CMake hashes 11 long mbedTLS object destination paths in the longer TCP profile directory.',shared_translation_units=len(q.keys()&t.keys()),different_after_normalization=different,quic_only=sorted(q.keys()-t.keys()),tcp_tls_only=sorted(t.keys()-q.keys()))
(profile/'compile_settings_comparison.json').write_text(json.dumps(report,indent=2))
assert not different and not report['quic_only'] and not report['tcp_tls_only'],report
print(json.dumps(report,indent=2))
