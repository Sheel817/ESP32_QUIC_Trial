"""Offline extraction/symbolization only. Never opens serial or operates processes."""
from pathlib import Path
import datetime as dt,hashlib,json,os,re,subprocess
root=Path(__file__).resolve().parents[2]
study=root/'results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED'
run=Path(Path(__file__).with_name('active_hbpsn03_path.txt').read_text().strip())
out=root/'results/diagnostics'/('HBPSN03_FIRST_CRASH_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(parents=True,exist_ok=False)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(out/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def link(p):return os.path.relpath(p,out).replace('\\','/')
protected=[study/'run_register.csv',root/'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx',run/'reset_event.json',run/'startup_checks.json',run/'collector_v2.py',run/'reliability.py',run/'monitor_instrumented_v2.py']
before={str(p):sha(p) for p in protected}
elf=root/'profiles/wifi_ps_none_20261103/build/quic_demo.elf'
assert sha(elf)=='9b23e164f8d6fd4702450b687c76ef3fa8ced802945dc23dd2f4d102c35c0f3d'
rom=Path('C:/Users/newsh/.espressif/tools/esp-rom-elfs/20241011/esp32c6_rev0_rom.elf')
binpath=Path('C:/Users/newsh/.espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin')
commands=[]
def tool(name,args,output):
    cmd=[str(binpath/('riscv32-esp-elf-'+name+'.exe'))]+list(map(str,args))
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    (out/output).write_text(p.stdout+p.stderr,encoding='utf-8')
    commands.append(dict(command=cmd,exit_code=p.returncode,output=output,utc=utc()))
    assert p.returncode==0
    return p.stdout
raw=(run/'serial.raw.log').read_bytes()
records=[json.loads(s) for s in (run/'serial_receipts.jsonl').read_text().splitlines()]
lines=raw.splitlines(keepends=True);decoded=[s.decode('utf-8',errors='replace').rstrip('\r\n') for s in lines]
panic=next(i for i,s in enumerate(decoded) if 'Guru Meditation Error:' in s)
reboot=next(i for i in range(panic,len(decoded)) if 'Rebooting...' in decoded[i])
rom2=next(i for i in range(reboot+1,len(decoded)) if 'ESP-ROM:esp32c6' in decoded[i])
reason=next(i for i in range(rom2,len(decoded)) if 'rst:' in decoded[i])
end=next(i+1 for i in range(rom2,len(decoded)) if 'Subscription acknowledged' in decoded[i])
assert decoded[0].endswith('ESP-ROM:esp32c6-20220919')
spans={}
def extract(name,start,stop):
    a=sum(map(len,lines[:start]));b=sum(map(len,lines[:stop]));chunk=raw[a:b]
    (out/name).write_bytes(chunk)
    spans[name]=dict(source=str(run/'serial.raw.log'),source_byte_start_inclusive=a,source_byte_end_exclusive=b,source_first_line=start+1,source_last_line=stop,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest(),first_receipt=records[start],last_receipt=records[stop-1])
    return chunk.decode('utf-8',errors='replace')
context=extract('startup_crash_reboot_context.raw.log',0,end)
crash=extract('first_crash_complete.raw.log',panic,rom2)
regstart=next(i for i in range(panic,reboot) if 'MEPC ' in decoded[i]);regend=next(i+1 for i in range(regstart,reboot) if 'MHARTID ' in decoded[i])
registertext=extract('register_dump.raw.log',regstart,regend)
stackstart=next(i for i in range(panic,reboot) if 'Stack memory:' in decoded[i]);stackend=next(i for i in range(stackstart,reboot) if 'ELF file SHA256:' in decoded[i])
stacktext=extract('stack_memory_and_original_decode_errors.raw.log',stackstart,stackend)
extract('reset_reason_and_following_startup.raw.log',rom2,end)
(out/'context_serial_receipts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records[:end]),encoding='utf-8')
registers={k:'0x'+v.lower() for k,v in re.findall(r'([A-Z][A-Z0-9/]+)\s*:\s*0x([0-9a-fA-F]+)',registertext)}
save('registers.json',registers)
addresses=[]
for s in [registertext,stacktext,decoded[reason+1]]:
    for a in re.findall(r'0x[0-9a-fA-F]{8}',s):
        a=a.lower()
        if a not in addresses:addresses.append(a)
# Decode data-like words too, but retain their origin and do not call them frames.
plain=tool('addr2line',['-a','-f','-C','-e',elf]+addresses,'application_addr2line_all_words.txt').splitlines()
mapping={}
for i in range(0,len(plain),3):
    if i+2<len(plain):mapping[plain[i].lower()]=dict(function=plain[i+1],location=plain[i+2])
romaddresses=[a for a in addresses if 0x40000000<=int(a,16)<0x40080000]
romplain=tool('addr2line',['-a','-f','-C','-e',rom]+romaddresses,'rom_addr2line.txt').splitlines()
rommap={romplain[i].lower():dict(function=romplain[i+1],location=romplain[i+2]) for i in range(0,len(romplain)-2,3)}
save('address_decodes.json',[dict(address=a,application=mapping.get(a),rom=rommap.get(a),classification='Register or stack word; not automatically an unwound frame') for a in addresses])
codewords=[a for a in addresses if 0x40800000<=int(a,16)<0x40818588 or 0x42000020<=int(a,16)<0x42131488]
tool('addr2line',['-a','-f','-i','-C','-e',elf]+codewords,'application_code_candidates_inline.txt')
tool('addr2line',['-a','-f','-i','-C','-e',elf]+[hex(int(a,16)-1) for a in codewords],'application_code_candidates_minus1.txt')
tool('readelf',['-h',elf],'application_elf_header.txt')
tool('objdump',['-h',elf],'application_sections.txt')
tool('objdump',['-d','--disassemble=tlsf_free',rom],'rom_tlsf_free_disassembly.txt')
tool('objdump',['-d','--disassemble=multi_heap_free_impl',rom],'rom_multi_heap_free_disassembly.txt')
for name,address in [('heap_caps_free',0x40800b56),('pktns_del',0x42016208),('conn_discard_pktns',0x4201b1d0),('ngtcp2_conn_discard_initial_state',0x4201b250),('client_write_streams',0x42011742)]:
    tool('objdump',['-d',f'--start-address={hex(address-16)}',f'--stop-address={hex(address+8)}',elf],name+'_callsite_disassembly.txt')
source_manifest_path=root/'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json'
frozen_sources=json.loads(source_manifest_path.read_text())
source_specs=[(root/'main/ngtcp2_sample.c',[(534,568)]),(root/'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c',[(757,768),(2480,2518),(2750,2770)]),(root/'components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c',[(30,43),(62,72)]),(Path('C:/esp/v6.1/esp-idf/components/heap/heap_caps_base.c'),[(67,90)]),(Path('C:/esp/v6.1/esp-idf/components/esp_libc/src/heap.c'),[(25,38)])]
sources=[];excerpts=[]
for p,ranges in source_specs:
    rel=p.relative_to(root).as_posix() if p.is_relative_to(root) else None
    expected=frozen_sources.get(rel) if rel else None
    actual=sha(p)
    if expected:assert actual==expected,'Source no longer matches recorded build source'
    sources.append(dict(path=str(p),sha256=actual,recorded_source_sha256=expected,matches_recorded_source=(actual==expected) if expected else None,source_provenance='Recorded source manifest hash match' if expected else 'Existing local SDK source; application ELF DWARF line mapping. Not separately frozen by that source manifest.'))
    content=p.read_text(encoding='utf-8',errors='replace').splitlines()
    excerpts.append('\n'+str(p)+'\n'+'\n'.join(f'{n}: {content[n-1]}' for a,b in ranges for n in range(a,b+1)))
(out/'source_excerpts.txt').write_text('\n'.join(excerpts),encoding='utf-8')
save('source_references.json',sources)
anchor=json.loads((run/'reset_event.json').read_text());startup=json.loads((run/'startup_checks.json').read_text())
save('source_intervals.json',spans)
save('commands.json',commands)
save('analysis_provenance.json',dict(created_utc=utc(),run_id='HBPSN-03',status='FAILED_STARTUP',validity_status='NOT_APPROVED',fixed_window=anchor,application_elf=dict(path=str(elf),sha256=sha(elf),printed_digest_prefix='9b23e164f',comparison='Printed prefix only; full local ELF hash verified'),rom_elf=dict(path=str(rom),sha256=sha(rom),basis='Existing local ESP32-C6 rev0 ROM symbol ELF; identification rev0.0, ROM banneresp32c6-20220919. Supplemental ROM mapping, not application firmware ELF; ROM source lines unavailable.'),tools=[dict(path=str(binpath/('riscv32-esp-elf-'+n+'.exe')),sha256=sha(binpath/('riscv32-esp-elf-'+n+'.exe'))) for n in ['addr2line','objdump','readelf']],source_manifest=dict(path=str(source_manifest_path),sha256=sha(source_manifest_path)),raw_prefix_snapshot=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),note='In-memory prefix observed while original recording remained open. Exact immutable extracted intervals have individual hashes.'),startup=startup,backtrace_limit='No explicit Backtrace: frame list was printed. Complete RISC-V stack memory preserved; decoded stack words are candidate return PCs, may include stale frames/data, not a verified unwind.'))
report=f'''# HBPSN-03 first Load access fault â€” offline analysis

Status remains **FAILED_STARTUP**, validity **NOT_APPROVED**. Original measured window: **2026-11-05 22:24:54.413525â€“23:01:54.413525 Helsinki** (UTC20:24:54.413525â€“21:01:54.413525). No retry, reset, serial connection, firmware edit/build, Clumsy change or register edit was performed for this analysis. The existing recorder continues to its unchanged deadline. Post-reboot RTTs remain excluded from primary selection.

## Evidence and exact identity

The [complete first panic output](./first_crash_complete.raw.log), [register dump](./register_dump.raw.log), [full stack dump including original decoder failures](./stack_memory_and_original_decode_errors.raw.log), [initial startup through subsequent subscription](./startup_crash_reboot_context.raw.log), and [software reset reason and following startup](./reset_reason_and_following_startup.raw.log) are byte-exact extracts from the existing [serial recording]({link(run/'serial.raw.log')}). Original files were not rewritten. [Byte/line intervals, receipt timestamps and SHA256 hashes](./source_intervals.json) identify each extract; [matching receipts](./context_serial_receipts.jsonl) preserve host timing.

Matching [application ELF]({link(elf)}) SHA256: **{sha(elf)}**. Boot and panic print9b23e164f, which matches that local ELF prefix; this is not a full on-device digest measurement. The application is RISC-V, not Xtensa. Existing monitor attempted xtensa-esp32-elf-addr2line and logged WinError2. Those failures are retained. Offline symbolization used the installed riscv32-esp-elf tools, without altering the running monitor environment. [Commands](./commands.json), [tool/input hashes and provenance](./analysis_provenance.json).

## Confirmed findings

- First panic received at **{records[panic]['utc']}**; printed monitor time22:25:02 Helsinki. It follows QUIC TLS negotiation and QUIC connection establishment, then MQTT transport initialization and stream0 creation, before any initial-boot MQTT connection/subscription acknowledgement.
- Registers: **MEPC0x40021c40**, **RA0x400225c4**, **MCAUSE0x5**, **MTVAL0x41847f0c**, **A1=0x40847f0c**, **A4=0x40847f08**, **A5=0x41847f08**, **SP0x40839030**. Panic explicitly reports Load access fault.
- Application ELF alone reports unknown ROM function/source at MEPC and RA. The already-installed ESP32-C6 rev0 [ROM symbol ELF]({link(rom)}) identifies **tlsf_free+0x42** at MEPC and **multi_heap_free_impl+0x46** at RA. [ROM address results](./rom_addr2line.txt). No ROM source-line metadata is available; no source line is invented.
- At MEPC the [ROM disassembly](./rom_tlsf_free_disassembly.txt) is `lw a4,4(a5)`: a read from **0x41847f08+4=0x41847f0c**, exactly matching MTVAL. The preceding path loads a size word from A1âˆ’4, masks its low two bits, and adds A1âˆ’4 to obtain A5. Recorded A5âˆ’(A1âˆ’4) is **0x01000000 =16MiB**, an implausible heap-block size for this on-chip heap. This demonstrates an inconsistent allocator size/pointer computation at the fault, assuming this matching rev0 ROM mapping. It does not expose the earlier write that caused it.
- The app stack contains return PCs mapping to `heap_caps_free` ([SDK source]({link(Path('C:/esp/v6.1/esp-idf/components/heap/heap_caps_base.c'))}:86 callsite), `free`, `default_free`, `ngtcp2_mem_free`, `pktns_del` ([ngtcp2_conn.c]({link(root/'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c')}:766, `ngtcp2_mem_free(mem,pktns)`), `conn_discard_pktns`:2500, `ngtcp2_conn_discard_initial_state`:2514, `conn_write_handshake_pkts`:2766 and packet-writing wrappers, with `client_write_streams` ([ngtcp2_sample.c]({link(root/'main/ngtcp2_sample.c')}:563, `ngtcp2_conn_writev_stream(...)`). These are verified address-to-symbol/line mappings, not proof that every stack word is a live frame. [All word decodes](./address_decodes.json), [inline code candidates](./application_code_candidates_inline.txt), [return-PC-minus1 callsite mapping](./application_code_candidates_minus1.txt), [source excerpts](./source_excerpts.txt), [source hashes](./source_references.json).
- The next ROM banner/reset line is **{decoded[reason]}**; its host receipt is **{records[reason]['utc']}**. The ROM savedPC0x4001975a maps to `software_reset_cpu`. This confirms a software CPU restart after the panic. Later successful QUIC/MQTT belongs to a different boot and cannot repair the initial failure.

## Interpretation and limits

The strongest supported localization is **allocator failure while freeing ngtcp2 Initial packet-number-space state during early QUIC packet writing**. Source and the candidate stack path agree on `pktns_del` freeing the packet-number-space allocation as the client discards Initial state. The ROM instruction/register arithmetic is consistent with corrupt allocation metadata or an invalid/freed allocation reaching `free`.

**Hypotheses, not established causes:** an earlier out-of-bounds write, use-after-free, double-free/invalid free, pointer corruption, or a lifetime/race bug could produce this state. This log cannot choose among them or identify a corrupting instruction. Source comments about a mutex do not establish the runtime absence/presence of a race. There is no basis to blame configured Drop1%, Chrome Remote Desktop, a particular packet or hardware. The packet-loss rate itself was not measured. The detection location in TLSF/ngtcp2 is not proof that either library originated the corruption.

There is **no explicit backtrace frame list** in this output. The entire stack memory dump is preserved, but symbolizing stack words is not equivalent to unwinding validated frames; wolfSSL/lwIP or other mapped words may be stale return PCs or data. Callsite-minus1 is a documented source-line convention for candidate return addresses; original addresses and decodes are retained. No RAM/core dump, allocator history, packet capture or runtime test was added. ROM function mapping uses a compatible local symbol file, not a newly read on-device ROM image. Project-source hashes were checked against the recorded source manifest where present; local SDK source is separately identified and hashed, not silently claimed frozen by that manifest.

## Preservation

The frozen deadline, collector code, initial startup result and both registers were hashed before/after this analysis. Earlier HBPSN-01/HBPSN-02 immutable files were checked against their preserved manifest. [Preservation verification](./preservation_verification.json). HBPSN-01 stays FAILED_SETTINGS; HBPSN-02 stays COMPLETE with retained flags; HBPSN-03 stays FAILED_STARTUP. Subsequent-boot evidence is retained, not promoted to primary RTTs.
'''
(out/'ANALYSIS.md').write_text(report,encoding='utf-8')
assert before=={str(p):sha(p) for p in protected}
old=json.loads((run/'earlier_runs_preservation_before.json').read_text())
assert all(sha(x['path'])==x['sha256'] for x in old)
save('preservation_verification.json',dict(verified_utc=utc(),protected_original_hashes=before,protected_originals_unchanged=True,earlier_run_files_checked=len(old),earlier_run_originals_unchanged=True,original_log_extracted_intervals_unchanged=all(hashlib.sha256((run/'serial.raw.log').read_bytes()[s['source_byte_start_inclusive']:s['source_byte_end_exclusive']]).hexdigest()==s['sha256'] for s in spans.values()),collector_heartbeat_observed=json.loads((run/'heartbeat.json').read_text()),collector_not_signalled=True,primary_selection_policy='Initial boot only; post-reboot RTTs excluded. Original frozen window unchanged.'))
save('SHA256SUMS.json',[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()])
print(json.dumps(dict(output=str(out),report=str(out/'ANALYSIS.md'),crash_lines=[panic+1,rom2],fault_pc=registers['MEPC'],fault_function='tlsf_free+0x42',candidate_project_callsite='main/ngtcp2_sample.c:563',fixed_deadline_utc=anchor['deadline_utc'],registers_unchanged=True),indent=2))
