import json,re,sys,subprocess,os
P=sys.argv[1]; cc=json.load(open('profiles/wifi_ps_none_20261103/build/compile_commands.json'))
want={'wolfssl_quic.c':'wolfssl/src/quic.c','ngtcp2_crypto':'ngtcp2/crypto/wolfssl/wolfssl.c','ngtcp2_conn':'lib/ngtcp2_conn.c','main_sample':'main/ngtcp2_sample.c'}
nm='C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin/riscv32-esp-elf-nm.exe'
res={}
for name,suf in want.items():
    e=[x for x in cc if x['file'].replace(chr(92),'/').endswith(suf)][0]
    c=e.get('command') or ' '.join(e['arguments'])
    out=P+'/probe/'+name+'.o'
    c=re.sub(r'-o\s+\S+','-o '+out,c)
    c=re.sub(r'-c\s+\S+\.c\s*$','-c '+P+'/probe/probe.c',c.strip())
    c=re.sub(r'-MD\s+-MT\s+\S+\s+-MF\s+\S+','',c)
    import shlex
    a=shlex.split(c,posix=False); rsp=P+'/probe/'+name+'.rsp'
    open(rsp,'w').write(chr(10).join(x for x in a[1:]))
    r=subprocess.run([a[0].strip(chr(34)),'@'+rsp],capture_output=True,text=True,cwd=e.get('directory'))
    if r.returncode: print(name,'COMPILE FAIL',r.stderr[-600:]); continue
    n=subprocess.run([nm,'-S','--size-sort',out],capture_output=True,text=True).stdout
    d={}
    for l in n.splitlines():
        p=l.split()
        if len(p)>=4 and (p[3].startswith('sz_') or p[3].startswith('flag_')): d[p[3]]=int(p[1],16)
    res[name]=d
keys=sorted({k for d in res.values() for k in d})
print('%-28s'%'item',*['%14s'%n for n in res])
for k in keys: print('%-28s'%k,*['%14s'%(res[n].get(k,'-')) for n in res])
