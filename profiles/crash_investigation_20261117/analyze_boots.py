"""Per-boot summary of a diagnostic capture log. Usage: python -I analyze_boots.py <log>"""
import re, sys, collections
t = open(sys.argv[1], encoding='utf-8', errors='replace').read().split('\n')
boots = []; cur = None
for l in t:
    if 'ESP-ROM:' in l: cur = []; boots.append(cur)
    if cur is not None: cur.append(l)
rows = []; c = collections.Counter(); first = collections.Counter(); notes = collections.Counter(); tails = []
for b in boots:
    txt = '\n'.join(b)
    cf = re.search(r'CHECKPOINT FAIL seq=(\d+) name=(\S+) last_pass=(\S+)', txt)
    n = re.search(r'DIAG NOTE conn_alloc addr_mod8 buflen sizeof_conn (\d+) (\d+) (\d+)', txt)
    mod = n[1] if n else '-'
    if cf: k = 'FAIL'; first[(cf[2], cf[3])] += 1
    elif re.search(r'DIAG CYCLE \d+ PASS', txt): k = 'PASS'
    elif 'DIAG CYCLE' in txt or 'DIAG BANNER' in txt: k = 'OTHER'
    else: continue
    other = ''
    if k == 'OTHER':
        other = ' | '.join(sorted(set(re.findall(r'(Guru Meditation[^\n]*|CORRUPT HEAP[^\n]{0,60}|abort\(\)[^\n]{0,30}|task_wdt[^\n]{0,30})', txt))))[:150]
    rows.append((k, mod, n[2] if n else '-', n[3] if n else '-', other))
    c[(k, mod)] += 1
    if 'task_wdt' in txt: notes['boots_with_task_wdt'] += 1
    for m in re.findall(r'Bad tail at (0x[0-9a-f]+)', txt)[:1]: tails.append(m)
print('boots with a cycle:', len(rows)); print('outcome by conn allocation address mod 8:', dict(c))
print('first failing checkpoint:', dict(first)); print(dict(notes))
print('other outcomes:', [r for r in rows if r[0] == 'OTHER'])
mods = collections.Counter((r[2], r[3]) for r in rows if r[1] != '-'); print('buflen,sizeof(ngtcp2_conn):', dict(mods))
