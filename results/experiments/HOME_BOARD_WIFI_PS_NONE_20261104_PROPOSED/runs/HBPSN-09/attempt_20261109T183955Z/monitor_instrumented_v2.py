"""ESP-IDF monitor with a host-only RTS-release timestamp hook."""
import datetime as dt
import json
from pathlib import Path
import time
import os
from reliability import Reports
import esp_pylib.serial_reset as primitives
from esp_idf_monitor.base.reset import Reset
from esp_idf_monitor.idf_monitor import main
folder=Path(os.environ['RECORDER_RUN_DIR'])
active=False
released=False
request=None
original_set_rts=primitives.set_rts
original_hard=Reset.hard
def observed_rts(port,value):
    global released
    original_set_rts(port,value)
    if active and value==primitives.PIN_HIGH and not released:
        monotonic=time.monotonic()
        now=dt.datetime.now(dt.timezone.utc)
        paths=json.loads((folder/'preflight.json').read_text())['server_log_sources']
        event=dict(reset_request_utc=request,reset_release_utc=now.isoformat(),reset_release_monotonic=monotonic,deadline_monotonic=monotonic+2220,deadline_utc=(now+dt.timedelta(seconds=2220)).isoformat(),method='SDK RTS reset release; host clocks sampled after successful release API return',boundary_precision='Host API completion, not a physical edge measurement',server_boundaries={n:dict(source=p,byte_offset=Path(p).stat().st_size) for n,p in paths.items()})
        if not Reports(folder).save('reset_event.json',event):
            raise RuntimeError('Reset already issued but anchor report failed; preserve fallback; never reset again')
        released=True
def observed_hard(self):
    global active,request
    if released:raise RuntimeError('Second commanded reset forbidden')
    if self.custom_hard_seq:raise RuntimeError('Custom reset sequence not accepted')
    request=dt.datetime.now(dt.timezone.utc).isoformat()
    active=True
    try:original_hard(self)
    finally:active=False
primitives.set_rts=observed_rts
Reset.hard=observed_hard
if __name__=='__main__':main()
