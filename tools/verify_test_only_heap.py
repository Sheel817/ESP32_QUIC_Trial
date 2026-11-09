"""Offline build/protection report. No hardware or serial access."""
from pathlib import Path
import datetime as dt,difflib,hashlib,json,os,re,struct,subprocess,sys
root=Path(__file__).resolve().parents[1];p=root/'profiles/test_only_heap_20261106';src=p/'src';build=p/'build'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def load(f):return json.loads(f.read_text(encoding='utf-8-sig'))
def save(n,x):(p/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
results=[load(f) for f in sorted(p.glob('build_result_*.json'))]
assert results[-1]['exit_code']==0,'Build has not passed'
elf=build/'quic_demo.elf';assert elf.exists()
manifest=load(p/'baseline_source_manifest.json')
diff=[];changed=[]
for f in sorted(src.rglob('*')):
    if not f.is_file() or '__pycache__' in f.parts:continue
    rel=f.relative_to(src).as_posix();baseline=root/rel if rel in manifest else None
    old=baseline.read_bytes() if baseline else b'';new=f.read_bytes()
    if old==new:continue
    assert b'\0' not in old+new,rel
    changed.append(dict(path=rel,baseline_sha256=hashlib.sha256(old).hexdigest() if baseline else None,test_only_sha256=sha(f)))
    diff.extend(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),new.decode('utf-8').splitlines(keepends=True),fromfile='a/'+rel if baseline else '/dev/null',tofile='b/'+rel))
(p/'diagnostic_source.diff').write_bytes(''.join(diff).encode('utf-8'))
save('changed_source_files.json',changed)
formal=load(root/'profiles/wifi_ps_none_20261103/build/config/sdkconfig.json');actual=load(build/'config/sdkconfig.json')
configdiff={k:dict(formal=formal.get(k),test_only=actual.get(k)) for k in sorted(formal.keys()|actual.keys()) if formal.get(k)!=actual.get(k)}
assert all(k.startswith('ESP_COREDUMP_') or k=='FREERTOS_ISR_STACKSIZE' for k in configdiff),configdiff
save('effective_configuration_diff.json',configdiff)
rawconfig=''.join(difflib.unified_diff((p/'sdkconfig.baseline').read_text().splitlines(keepends=True),(p/'sdkconfig').read_text().splitlines(keepends=True),fromfile='formal/sdkconfig',tofile='TEST_ONLY/sdkconfig'))
(p/'sdkconfig.diff').write_text(rawconfig,encoding='utf-8')
nm='C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin/riscv32-esp-elf-nm.exe'
objdump=nm.replace('-nm.exe','-objdump.exe')
symbols=subprocess.check_output([nm,'-S','-n',str(elf)],text=True)
(p/'symbols.txt').write_text(symbols,encoding='utf-8')
found={}
for line in symbols.splitlines():
    m=re.match(r'([0-9a-f]+) ([0-9a-f]+) \w (g_test_only_heap_(?:control|trace))$',line)
    if m:found[m[3]]=dict(address=int(m[1],16),bytes=int(m[2],16))
assert found['g_test_only_heap_trace']['bytes']==256*36 and found['g_test_only_heap_control']['bytes']==24
asm=subprocess.check_output([objdump,'-d','--disassemble=test_only_heap_trace',str(elf)],text=True)
(p/'trace_producer_disassembly.txt').write_text(asm,encoding='utf-8')
assert not any(name in asm for name in ['<malloc>','<calloc>','<realloc>','<free>','<esp_log','<esp_rom_printf','<xQueueSemaphoreTake>','<vTaskDelay>'])
assert 'xTaskGetCurrentTaskHandle' in asm
# Synthetic core-memory validation of the real offline GDB recovery script.
validation=p/'host_validation';validation.mkdir(exist_ok=True)
control=struct.pack('<6I',0x544f4844,1,256,258,1,1);trace=bytearray(256*36)
def entry(slot,writing,commit,seq,phase):struct.pack_into('<9I',trace,slot*36,writing,commit,seq,1234,phase,0x40812340,0x40840000,0,4)
entry(0,0,257,257,7);entry(1,1,0,258,8);entry(2,0,3,3,2)
header=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+b'\0'*9,4,243,1,0,52,0,1,52,32,2,0,0,0)
ph1=struct.pack('<8I',1,4096,found['g_test_only_heap_control']['address'],0,len(control),len(control),6,4)
ph2=struct.pack('<8I',1,8192,found['g_test_only_heap_trace']['address'],0,len(trace),len(trace),6,4)
blob=bytearray(8192+len(trace));blob[:52]=header;blob[52:116]=ph1+ph2;blob[4096:4096+len(control)]=control;blob[8192:]=trace
core=validation/'SYNTHETIC_TEST_ONLY.core';core.write_bytes(blob)
gdb='C:/Espressif/tools/riscv32-esp-elf-gdb/17.1_20260402/riscv32-esp-elf-gdb/bin/riscv32-esp-elf-gdb.exe'
cmd=[gdb,'--batch','--nx',str(elf),str(core),'-x',str(p/'recover_trace.gdb')]
run=subprocess.run(cmd,cwd=validation,capture_output=True,text=True,timeout=30)
(validation/'gdb_recovery.log').write_text(run.stdout+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
decode=subprocess.run([sys.executable,'-B',str(p/'decode_trace.py'),str(validation)],capture_output=True,text=True,timeout=15)
(validation/'decode.log').write_text(decode.stdout+decode.stderr,encoding='utf-8')
assert decode.returncode==0,decode.stderr
recovered=load(validation/'TEST_ONLY_trace_recovered.json')
assert run.returncode==0 and [r['sequence'] for r in recovered['rows']]==[3,257] and 1 in recovered['skipped_slots']
save('host_validation.json',dict(label='TEST_ONLY_SYNTHETIC_NOT_BOARD_DATA',gdb_command=cmd,exit_code=run.returncode,committed_records_sorted=True,in_progress_record_skipped=True,limitation='Validates actual recovery script against synthetic ELF core memory. Does not validate physical UART capture, SDK core generation on corruption or reproduction.'))
# ESP-IDF partition binary: application type0 entries have uint32 offset,size.
part=(build/'partition_table/partition-table.bin').read_bytes();entries=[]
for off in range(0,len(part),32):
    if part[off:off+2]!=b'\xaa\x50':continue
    magic,typ,sub,offset,size,label,flags=struct.unpack_from('<HBBII16sI',part,off)
    entries.append(dict(type=typ,subtype=sub,offset=offset,size=size,label=label.rstrip(b'\0').decode()))
app=next(x for x in entries if x['type']==0);appsize=(build/'quic_demo.bin').stat().st_size
assert appsize<=app['size']
artifacts=[dict(path=str(build/n),bytes=(build/n).stat().st_size,sha256=sha(build/n)) for n in ['quic_demo.bin','quic_demo.elf','bootloader/bootloader.bin','partition_table/partition-table.bin','flash_args','flasher_args.json']]
compile_commands=load(build/'compile_commands.json')
bad=[x['file'] for x in compile_commands if str(root/'main').replace('\\','/') in x['file'].replace('\\','/') or str(root/'components').replace('\\','/') in x['file'].replace('\\','/') or str(root/'managed_components').replace('\\','/') in x['file'].replace('\\','/')]
assert not bad,'Formal project sources used in diagnostic compile'
main=next(x for x in compile_commands if x['file'].endswith('quic_demo_main.c'))
assert 'DEMO_WIFI_PS_NONE=1' in main['command'] and 'DEMO_TRANSPORT_TCP_TLS=0' in main['command']
report=dict(label='TEST_ONLY_BUILT_NOT_FLASHED',checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),build_link='PASS',partition='PASS',app_bytes=appsize,app_partition_bytes=app['size'],app_partition_free_bytes=app['size']-appsize,partitions=entries,artifacts=artifacts,build_attempts=results,effective_config_diff=configdiff,source_changes=changed,trace_symbols=found,trace_ram_bytes=9240,trace_hook_check='Compiled disassembly contains no allocation/free/logging/delay/semaphore-take calls; word atomics required lock-free by static assert. Real allocator executes outside trace producer.',private_project_compile_paths_verified=True,app_defines_verified=True,host_validation='PASS_SYNTHETIC_ONLY',recovery_gdb=gdb,hardware_test='NOT_PERFORMED',formal_run_register_update=False)
save('BUILD_REPORT.json',report)
print('Build/link/partition/host checks PASS. Verifying protected originals...',flush=True)
before=load(p/'protected_before.json');errors=[]
for x in before:
    f=Path(x['path'])
    if not f.exists() or f.stat().st_size!=x['bytes'] or sha(f)!=x['sha256']:errors.append(x['path'])
save('protection_verification.json',dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),protected_file_count=len(before),changed_or_missing=errors,pass_all=not errors,excluded='Continuously growing monitor streams/after-run/supervisor logs, caches, node_modules/junctions; immutable formal raw/results/configs/builds and both registers included.'))
assert not errors,errors
print(json.dumps(dict(profile=str(p),app_bytes=appsize,free=app['size']-appsize,protected_files=len(before),artifacts=artifacts[:2]),indent=2))
