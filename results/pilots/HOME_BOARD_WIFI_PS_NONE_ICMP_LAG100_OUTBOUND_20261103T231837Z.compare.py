import csv
import hashlib
import json
from pathlib import Path

folder=Path(__file__).resolve().parent
stem='HOME_BOARD_WIFI_PS_NONE_ICMP_LAG100_OUTBOUND_20261103T231837Z'
control_stem='HOME_BOARD_WIFI_PS_NONE_ICMP_CAPTURE_20261103T231348Z'
run_path=folder/(stem+'.json')
control_path=folder/(control_stem+'.json')
run=json.loads(run_path.read_text(encoding='utf-8'))
control=json.loads(control_path.read_text(encoding='utf-8'))
assert round(control['mean_ms'],4)==2.6333 and control['median_ms']==2 and control['replies']==30
comparison=dict(label=run['label'],control_source=control_path.name,control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),control_mean_ms=control['mean_ms'],control_median_ms=control['median_ms'],control_replies=control['replies'],lag_source=run_path.name,lag_sha256=hashlib.sha256(run_path.read_bytes()).hexdigest(),lag_mean_ms=run.get('mean_ms'),lag_median_ms=run.get('median_ms'),lag_replies=run['replies'],lag_timeouts=run['timeouts'],lag_other_failures=run['other_failures'])
if not run['censored_replies']:
    comparison.update(mean_increase_ms=run['mean_ms']-control['mean_ms'],median_increase_ms=run['median_ms']-control['median_ms'])
    detail=f"Mean increased by **{comparison['mean_increase_ms']:.4f} ms**; median increased by **{comparison['median_increase_ms']:g} ms**."
    mean_text=f"{run['mean_ms']:.4f} ms"
else:
    comparison.update(mean_increase_lower_bound_ms=run['mean_lower_bound_ms']-control['mean_ms'],mean_increase_upper_bound_exclusive_ms=run['mean_upper_bound_exclusive_ms']-control['mean_ms'])
    detail=f"Mean increase is bounded by {comparison['mean_increase_lower_bound_ms']:.4f} <= increase < {comparison['mean_increase_upper_bound_exclusive_ms']:.4f} ms; censored observations remain unassigned."
    mean_text=f"[{run['mean_lower_bound_ms']:.4f}, {run['mean_upper_bound_exclusive_ms']:.4f}) ms"
text=f'''

## Comparison only with fresh PS_NONE capture-only control

[Control](./{control_stem}.md): mean **2.6333 ms**, median **2 ms**, **30 replies**, no timeouts.

Current outbound-Lag run: mean **{mean_text}**, **{run['replies']} replies**, **{run['timeouts']} timeouts**. {detail}

Both runs are HOME_BOARD WIFI_PS_NONE with Clumsy settings operator-reported. This comparison uses only the fresh capture-only control; no default-power-saving or university-board data are used. Every current result remains in request order in the raw output and CSV.
'''
with (folder/(stem+'.md')).open('a',encoding='utf-8') as f: f.write(text)
(folder/(stem+'.comparison.json')).write_text(json.dumps(comparison,indent=2,ensure_ascii=False),encoding='utf-8')
with (folder/(stem+'.comparison.csv')).open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(comparison))
    w.writeheader()
    w.writerow(comparison)
print(json.dumps(comparison,indent=2,ensure_ascii=False))
