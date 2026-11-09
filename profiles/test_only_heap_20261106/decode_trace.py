"""TEST_ONLY offline raw RAM decoder. No serial or device APIs."""
import argparse,json,struct
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('directory',type=Path)
args=parser.parse_args();d=args.directory
c=(d/'TEST_ONLY_trace_control.bin').read_bytes();b=(d/'TEST_ONLY_trace_ring.bin').read_bytes()
assert len(c)==24 and len(b)==256*36,'TEST_ONLY wrong memory lengths'
control=dict(zip(('magic','version','capacity','next_sequence','dropped','frozen'),struct.unpack('<6I',c)))
assert (control['magic'],control['version'],control['capacity'])==(0x544f4844,1,256),'TEST_ONLY wrong trace schema'
rows=[];skipped=[]
for i in range(256):
    r=dict(zip(('writing','commit','sequence','cycles','phase','task','pointer','related','detail'),struct.unpack_from('<9I',b,i*36)))
    if r['writing'] or not r['commit'] or r['commit']!=r['sequence']:
        skipped.append(i);continue
    r['slot']=i;rows.append(r)
rows.sort(key=lambda r:r['sequence'])
with (d/'TEST_ONLY_trace_recovered.json').open('x',encoding='utf-8') as f:
    json.dump(dict(label='TEST_ONLY',control=control,rows=rows,skipped_slots=skipped),f,indent=2)
print('TEST_ONLY recovered',len(rows),'committed entries; skipped',len(skipped))
