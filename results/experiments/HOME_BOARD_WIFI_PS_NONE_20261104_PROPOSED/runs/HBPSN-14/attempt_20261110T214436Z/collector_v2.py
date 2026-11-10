"""Persistent single-run recorder. No build/flash/ping; one designated reset only."""
import csv,datetime as dt,hashlib,json,os,re,statistics,subprocess,sys,threading,time,traceback
from pathlib import Path
import argparse
from reliability import Reports, SettingsEvidence, arm_deadline
parser=argparse.ArgumentParser(description='Preserved-image recorder; explicit fresh run directory required')
parser.add_argument('--run-dir',type=Path,required=True)
args=parser.parse_args()
folder=args.run_dir.resolve()
assert not (folder/'serial.raw.log').exists(), 'Never overwrite/reuse a historical run directory'
reports=Reports(folder)
study=folder.parents[2];root=study.parents[2]
node='C:/Users/newsh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
preflight=json.loads((folder/'preflight.json').read_text())
run_id=preflight['run_id']; transport=preflight['transport']; condition=preflight['condition']
assert transport in ('QUIC','TCP_TLS')
assert preflight['plan_sha256']==hashlib.sha256((study/'EXPERIMENT_PLAN_PROPOSED_V1.md').read_bytes()).hexdigest()
evidence=SettingsEvidence(reports,preflight['expected_clumsy_settings'],timeout=30)
finalization_done=threading.Event()
startup_state=None;interruption_state=[]
lock=threading.RLock();reset_cache=None;monitor=None;monitor_exit=None;tail_errors=[]
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,value):
    return reports.save(name,value)
def event():
    global reset_cache
    if reset_cache is None and (folder/'reset_event.json').exists():reset_cache=json.loads((folder/'reset_event.json').read_text())
    return reset_cache
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def csv_save(name,rows,fields):
    with (folder/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def control_exit():
    p=folder/'monitor_control.txt'
    if p.exists() and p.read_text().strip()=='exit':
        monitor.stdin.write(b'exit\n');monitor.stdin.flush()
        p.rename(folder/('monitor_exit_requested_'+str(time.monotonic_ns())+'.txt'))
def register(patch,final=False):
    # Emit a reviewable request only. Never call the historical HBPSN-01-only updater.
    save('register_final_request.json' if final else 'register_running_request.json',
         dict(run_id=run_id,patch=patch,final=final,automatic_register_apply=False))


stream=open(folder/'monitor_stream.log','ab',buffering=0)
setup=open(folder/'serial_setup.log','ab',buffering=0)
after=open(folder/'monitor_after_run.log','ab',buffering=0)
raw_serial=open(folder/'serial.raw.log','ab',buffering=0)
index=open(folder/'serial_receipts.jsonl','a',encoding='utf-8',buffering=1)
def serial_reader():
    global monitor_exit
    while True:
        line=monitor.stdout.readline()
        if not line:break
        received=time.monotonic();stamp=utc()
        with lock:
            stream_offset=stream.tell();stream.write(line)
            start=event()
            if start and start['reset_release_monotonic']<=received<start['deadline_monotonic']:
                offset=raw_serial.tell();raw_serial.write(line)
                index.write(json.dumps(dict(utc=stamp,monotonic=received,offset=offset,length=len(line),monitor_stream_offset=stream_offset))+'\n')
            elif start and received>=start['deadline_monotonic']:after.write(line)
            else:setup.write(line)
    monitor_exit=dict(utc=utc(),monotonic=time.monotonic(),returncode=monitor.poll())
    save('monitor_exit.json',monitor_exit)

tail_threads=[]
def tail_server(name):
    try:
        while event() is None:time.sleep(.02)
        start=event();boundary=start['server_boundaries'][name]
        p=Path(boundary['source']);position=boundary['byte_offset']
        with p.open('rb') as source,open(folder/f'server.{name}.raw.log','ab',buffering=0) as target,open(folder/f'server.{name}.receipts.jsonl','a',encoding='utf-8',buffering=1) as receipts:
            source.seek(position)
            while time.monotonic()<start['deadline_monotonic']:
                if p.stat().st_size<position:raise RuntimeError('Server source log truncated')
                line=source.readline()
                now=time.monotonic()
                if line and now<start['deadline_monotonic']:
                    offset=target.tell();target.write(line)
                    receipts.write(json.dumps(dict(utc=utc(),monotonic=now,source_offset=position,offset=offset,length=len(line)))+'\n')
                    position+=len(line)
                elif not line:time.sleep(min(.03,max(0,start['deadline_monotonic']-time.monotonic())))
            save(f'server_{name}_boundary_end.json',dict(source=str(p),start_byte=boundary['byte_offset'],end_byte=position,deadline_utc=start['deadline_utc'],tail_closed_utc=utc()))
    except Exception as error:
        tail_errors.append(dict(source=name,error=repr(error),utc=utc()))
        save(f'server_{name}_tail_failure.json',tail_errors[-1])

def startup_check():
    text=(folder/'serial.raw.log').read_text(encoding='utf-8',errors='replace')
    prefix=re.search(r'ELF file SHA256:\s*([a-f0-9]+)',text)
    expected=next(a['sha256'] for a in preflight['firmware_artifacts'] if a['path'].endswith('quic_demo.elf'))
    ip=re.search(r'example_netif_sta ip: ([\d.]+)',text)
    gates={'boot_banner':'ESP-ROM:esp32c6' in text,'board_mac':'40:4c:ca:56:bb:b0' in text,'elf_prefix':bool(prefix and expected.startswith(prefix[1])),'transport_firmware':f'Starting ESP32-C6 DHT11 over {transport}' in text,'wifi_ps_none':'requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)' in text,'assigned_ip':bool(ip),'transport_connected':('QUIC connection established' in text if transport=='QUIC' else 'TCP_NODELAY=1' in text),'mqtt_connected':f'MQTT connected over {transport}' in text,'subscription':'Subscription acknowledged' in text,'tls':f'{transport} negotiated TLS=TLSv1.3 cipher=TLS_AES_128_GCM_SHA256' in text and 'suite=0x1301 ALPN=mqtt certificate_verification=NONE (mode=0)' in text}
    fatal=bool(prefix and not expected.startswith(prefix[1])) or bool(re.search(r'ESP_ERROR_CHECK failed|abort\(\)|Guru Meditation',text))
    return dict(checked_utc=utc(),gates=gates,pass_all=all(gates.values()),fatal=fatal,assigned_ip=ip[1] if ip else None,reported_elf_prefix=prefix[1] if prefix else None)

def finalize(start,startup,interruption):
    with lock:raw_serial.flush();index.flush()
    for thread in tail_threads:thread.join(timeout=2)
    lines=(folder/'serial.raw.log').read_text(encoding='utf-8',errors='replace').splitlines()
    receipts=[json.loads(s) for s in (folder/'serial_receipts.jsonl').read_text().splitlines()]
    parsed=[];excluded=[];eligible=[];warnings=[];errors=[];resets=[];gaps=[];seen=set();rom=0;initial=True;last_uptime=None;last_seq=None
    for n,line in enumerate(lines):
        receipt=receipts[n] if n<len(receipts) else {}
        if 'ESP-ROM:esp32c6' in line:
            rom+=1;resets.append(dict(line=n+1,raw_line=line,host_receipt_utc=receipt.get('utc'),initial_designated_boot=rom==1))
            if rom>1:initial=False
        stamp=re.search(r'\b[IWE] \((\d+)\)',line)
        if stamp:
            uptime=int(stamp[1])
            if last_uptime is not None and last_uptime>60000 and uptime<last_uptime-1000:
                initial=False;resets.append(dict(line=n+1,raw_line=line,reason='ESP timestamp regression'))
            last_uptime=uptime
        if re.search(r'\b[WE] \(\d+\)',line):warnings.append(dict(line=n+1,raw_line=line))
        if re.search(r'(?i)(\bE \(\d+\)|disconnect|connection.*(?:error|fail|lost)|handshake.*(?:error|fail)|APP_RTT (?:ignored|storage full)|panic|abort\(|serial.*(?:closed|error)|waiting for.*port)',line):errors.append(dict(line=n+1,raw_line=line))
        m=re.search(r'\bI \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)',line)
        if not m:continue
        r=dict(source_line=n+1,host_receipt_utc=receipt.get('utc',''),host_monotonic=receipt.get('monotonic',''),esp_log_uptime_ms=int(m[1]),seq=int(m[2]),app_rtt_ms=m[3],run_id=run_id,transport=transport,condition=condition,boot_session=run_id+'/'+start['reset_release_utc'],raw_line=line)
        parsed.append(r)
        if last_seq is not None and r['seq']!=last_seq+1:gaps.append(dict(previous=last_seq,current=r['seq'],source_line=n+1))
        last_seq=r['seq']
        reason=''
        if not initial:reason='subsequent_boot_or_timestamp_regression'
        elif r['esp_log_uptime_ms']<60000:reason='warmup_below_60000_ms'
        elif r['esp_log_uptime_ms']>=2220000:reason='at_or_above_2220000_ms'
        elif r['seq'] in seen:reason='duplicate_sequence'
        if reason:excluded.append(dict(**r,exclusion_reason=reason))
        else:eligible.append(r)
        seen.add(r['seq'])
    selected=eligible[:415];values=[float(r['app_rtt_ms']) for r in selected]
    fields=['source_line','host_receipt_utc','host_monotonic','esp_log_uptime_ms','seq','app_rtt_ms','run_id','transport','condition','boot_session','raw_line']
    for name,data in [('all_rtts.csv',parsed),('eligible_rtts.csv',eligible),('selected_first_415.csv',selected),('eligible_extra.csv',eligible[415:])]:csv_save(name,data,fields)
    csv_save('excluded_rtts.csv',excluded,fields+['exclusion_reason'])
    sensor_source=Path(preflight['server_sensor_source'])
    with sensor_source.open(newline='',encoding='utf-8') as f:
        sensor_reader=csv.DictReader(f);sensor_fields=sensor_reader.fieldnames
        sensor_records=[r for r in sensor_reader if start['reset_release_utc']<=r.get('server_receive_utc','').replace('Z','+00:00')<start['deadline_utc']]
    csv_save('server_sensor_records.csv',sensor_records,sensor_fields)
    interrupted=bool(interruption or tail_errors or any(not r.get('initial_designated_boot',False) for r in resets))
    post_path=folder/'post_recording_settings_check.json'
    post=json.loads(post_path.read_text()) if post_path.exists() else {'status':'PENDING','reason':'Required post-recording GUI/settings evidence has not been supplied; no state fabricated'}
    post_verified=post.get('status')=='PASS'
    completion_candidate='FAILED_STARTUP' if not startup or not startup['pass_all'] else ('INTERRUPTED' if interrupted else ('FAILED_SETTINGS' if not post_verified else ('COMPLETE_SHORTFALL' if len(selected)<415 else 'COMPLETE')))
    # Automatic processing never approves scientific validity. This local pending
    # state is not a new frozen-register status and is not written to a register.
    status='PENDING_EVIDENCE_REVIEW' if completion_candidate in ('COMPLETE','COMPLETE_SHORTFALL') else completion_candidate
    stats=dict(status=status,run_id=run_id,transport=transport,condition=condition,recording_start_utc=start['reset_release_utc'],fixed_deadline_utc=start['deadline_utc'],finalization_utc=utc(),defined_window_seconds=2220,deadline_observed_lateness_ms=max(0,(time.monotonic()-start['deadline_monotonic'])*1000),all_rtt_count=len(parsed),eligible_count=len(eligible),selected_count=len(selected),shortfall=415-len(selected),mean_ms=statistics.mean(values) if values else None,median_ms=statistics.median(values) if values else None,minimum_ms=min(values) if values else None,maximum_ms=max(values) if values else None,first_selected_seq=selected[0]['seq'] if selected else None,last_selected_seq=selected[-1]['seq'] if selected else None,all_values_ms=[r['app_rtt_ms'] for r in selected],warning_error_lines=warnings,connection_error_lines=errors,sequence_gaps=gaps,resets=resets,interruptions=interruption,server_tail_errors=tail_errors,server_stderr=(folder/'server.stderr.raw.log').read_text(encoding='utf-8',errors='replace') if (folder/'server.stderr.raw.log').exists() else '',startup=startup,preflight=preflight)
    save('statistics.json',stats)
    ordered=sorted(values)
    def percentile(p):
        if not ordered:return None
        x=(len(ordered)-1)*p;i=int(x)
        return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(x-i)
    stats['percentile_method']='Linear empirical interpolation at (N-1)*p, type 7'
    stats['recording_window_status']='FINISHED_FIXED_WINDOW'
    stats['completion_candidate']=completion_candidate
    stats['evidence_review_status']='PENDING_MANUAL_REVIEW'
    stats['validity_status']='NOT_APPROVED'
    stats['operator_stability_confirmation']='NOT_REVIEWED'
    cutoff_path=folder/'recording_cutoff_observed.json'
    cutoff_report=json.loads(cutoff_path.read_text()) if cutoff_path.exists() else None
    stats['finalization_delay_after_deadline_ms']=max(0,(time.monotonic()-start['deadline_monotonic'])*1000)
    stats['deadline_observed_lateness_ms']=cutoff_report.get('lateness_ms') if cutoff_report else None
    stats['warmup_excluded_count']=sum(r['exclusion_reason']=='warmup_below_60000_ms' for r in excluded)
    stats['other_excluded_count']=len(excluded)-stats['warmup_excluded_count']
    stats['raw_serial_line_count']=len(lines)
    stats['post_recording_settings_check']=post
    stats['p90_ms']=percentile(.90);stats['p95_ms']=ordered[__import__('math').ceil(.95*len(ordered))-1] if ordered else None;stats['p99_ms']=percentile(.99)
    stats['p95_method']='nearest rank ceil(0.95*N); P90/P99 retain type 7'
    save('statistics.json',stats)
    stats['reporting_errors']=reports.errors
    save('metadata.json',dict(**stats,collector_pid=os.getpid(),monitor_pid=monitor.pid,source_plan_sha256=preflight['plan_sha256']))
    patch=dict(status=status,recording_end_utc=start['deadline_utc'],actual_duration_seconds=2220,eligible_count=len(eligible),selected_count=len(selected),shortfall=415-len(selected),connection_error_count=len(errors),sequence_gap_count=len(gaps),mean_app_rtt_ms=stats['mean_ms'],minimum_app_rtt_ms=stats['minimum_ms'],maximum_app_rtt_ms=stats['maximum_ms'],deviation_reason='; '.join(str(x) for x in interruption+tail_errors) or None)
    if status=='PENDING_EVIDENCE_REVIEW':
        patch.pop('status')  # Preserve frozen register enums; reviewer decides later.
        patch['deviation_reason']='Automatic recording finalized; required screenshots and operator stability confirmation await manual review. Validity NOT_APPROVED.'
    if not post_verified:patch['deviation_reason']=(patch['deviation_reason'] or '')+' Required post-recording settings evidence pending; fixed data window is not extended.'
    try:register(patch,True)
    except Exception:save('register_final_failure.json',dict(utc=utc(),error=traceback.format_exc()))
    text=f"# {run_id} {transport} {condition}\n\nStatus: **{status}**. Fixed recording from {start['reset_release_utc']} to {start['deadline_utc']} (2220 seconds).\n\nEligible {len(eligible)}; selected {len(selected)}; shortfall {415-len(selected)}. Mean {stats['mean_ms']} ms; min {stats['minimum_ms']}; max {stats['maximum_ms']}. All selected values and outliers retained.\n\n[Selected CSV](./selected_first_415.csv), [all RTTs](./all_rtts.csv), [eligibility exclusions](./excluded_rtts.csv), [statistics and errors/gaps/resets](./statistics.json), [serial raw log](./serial.raw.log), [server stdout](./server.stdout.raw.log), [server stderr](./server.stderr.raw.log), [reset anchor](./reset_event.json), [preflight/provenance](./preflight.json). Parent monitor stream and after-run logs remain live. No automatic retry/reset/extension was performed. Register update request emitted; application is a separate review step.\n"
    try:(folder/'SUMMARY.md').write_text(text,encoding='utf-8')
    except Exception as error:reports.error('summary_report',error)
    hashes=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file() and p.name not in ('monitor_stream.log','monitor_after_run.log','supervisor.stdout.log','supervisor.stderr.log','SHA256SUMS.json') and not p.name.endswith('.tmp')]
    save('SHA256SUMS.json',hashes)
    save('FINALIZED.json',dict(status=status,processing_status='FINALIZED',validity_status='NOT_APPROVED',evidence_review_status='PENDING_MANUAL_REVIEW',completion_candidate=completion_candidate,finished_utc=utc(),deadline_utc=start['deadline_utc'],selected_count=len(selected),shortfall=415-len(selected),summary=str(folder/'SUMMARY.md')))

def main():
    global monitor,startup_state,interruption_state
    assert preflight['status']=='PASS' and not (folder/'reset_event.json').exists()
    flash=json.loads((folder/'flash_result.json').read_text(encoding='utf-8-sig'));assert flash['exit_code']==0
    assert (folder/'flash.log').read_text(encoding='utf-16').count('Hash of data verified.')==3
    assert '40:4c:ca:56:bb:b0' in (folder/'identification.log').read_text(encoding='utf-16')
    for artifact in preflight['firmware_artifacts']:
        assert sha(Path(artifact['path']))==artifact['sha256'], 'Prepared artifact hash mismatch; no monitor/reset'
    for config in preflight.get('configuration',[]):
        assert sha(Path(config['path']))==config['sha256'], 'Configuration hash mismatch; no monitor/reset'
    before=evidence.capture('pre_run')
    if before['status']!='PASS':
        save('PREFLIGHT_BLOCKED.json',dict(reason='Missing/mismatched actual pre-reset settings evidence',evidence=before))
        raise RuntimeError('Settings preflight failed; no monitor/reset started')
    save('collector_prepared.json',dict(utc=utc(),pid=os.getpid(),recording_seconds=2220,plan_sha256=preflight['plan_sha256'],all_outputs_prepared_before_reset=True,collector_code_sha256=sha(Path(__file__)),monitor_wrapper_sha256=sha(Path(__file__).with_name('monitor_instrumented_v2.py')),reliability_code_sha256=sha(Path(__file__).with_name('reliability.py')),automatic_register_apply=False))
    for name in preflight['server_log_sources']:
        (folder/f'server.{name}.raw.log').touch(exist_ok=False)
        (folder/f'server.{name}.receipts.jsonl').touch(exist_ok=False)
    env=os.environ.copy();env.update(PYTHONUNBUFFERED='1',PYTHONUTF8='1',IDF_PATH='C:/esp/v6.1/esp-idf',RECORDER_RUN_DIR=str(folder))
    command=[sys.executable,'-u',str(Path(__file__).with_name('monitor_instrumented_v2.py')),'--port','COM6','--baud','115200','--target','esp32c6','--no-reset','--disable-auto-color','--timestamps','--timestamp-format','%Y-%m-%dT%H:%M:%S',next(x['path'] for x in preflight['firmware_artifacts'] if x['path'].endswith('quic_demo.elf'))]
    monitor=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    save('monitor_session.json',dict(started_utc=utc(),monitor_pid=monitor.pid,collector_pid=os.getpid(),command=command))
    threading.Thread(target=serial_reader,daemon=True).start()
    for name in preflight['server_log_sources']:
        t=threading.Thread(target=tail_server,args=(name,),daemon=True);tail_threads.append(t);t.start()
    time.sleep(3)
    if monitor.poll() is not None:raise RuntimeError('Monitor failed before designated reset; no retry')
    save('armed_before_reset.json',dict(utc=utc(),collector_pid=os.getpid(),monitor_pid=monitor.pid,server_tail_threads_prepared=True))
    monitor.stdin.write(b'reset\n');monitor.stdin.flush()
    timeout=time.monotonic()+20
    while event() is None:
        if monitor.poll() is not None or time.monotonic()>timeout:raise RuntimeError('Reset release not captured; no retry')
        time.sleep(.01)
    start=event();startup=None;registered=False;interruption=[]
    def finish(start,post):
        try:finalize(start,startup_state,interruption_state)
        finally:finalization_done.set()
    def save_post(post):save('post_recording_settings_check.json',post)
    cutoff,deadline_thread=arm_deadline(start,reports,evidence,finish,save_post)
    while time.monotonic()<start['deadline_monotonic']:
        if not startup or (not startup['pass_all'] and not startup['fatal']):
            check=startup_check()
            if check['fatal'] or check['pass_all']:
                startup=check;save('startup_checks.json',check)
            if check['fatal']:startup=check
        if startup and startup['pass_all'] and not registered:
            registered=True
            local=dt.datetime.fromisoformat(start['reset_release_utc']).astimezone(dt.timezone(dt.timedelta(hours=2)))
            deadline=dt.datetime.fromisoformat(start['deadline_utc']).astimezone(dt.timezone(dt.timedelta(hours=2)))
            running=dict(status='RUNNING',run_id=run_id,transport=transport,condition=condition,actual_start_utc=start['reset_release_utc'],deadline_utc=start['deadline_utc'],actual_start_helsinki=local.isoformat(),deadline_helsinki=deadline.isoformat(),collector_pid=os.getpid(),monitor_pid=monitor.pid,startup=startup,plan_sha256=preflight['plan_sha256'],serial_log=str(folder/'serial.raw.log'),server_stdout=str(folder/'server.stdout.raw.log'),server_stderr=str(folder/'server.stderr.raw.log'))
            save('RUNNING.json',running);save('metadata.json',running)
            try:register(dict(status='RUNNING',preflight_status='PASS',startup_status='PASS',settings_evidence_type='operator_reported_and_preflight_GUI_observed',boot_session_id=run_id+'/'+start['reset_release_utc'],reset_release_utc=start['reset_release_utc'],actual_assigned_ip=startup['assigned_ip'],metadata_path=str((folder/'metadata.json').relative_to(study)).replace('\\','/'),raw_serial_path=str((folder/'serial.raw.log').relative_to(study)).replace('\\','/')))
            except Exception:save('register_running_failure.json',dict(utc=utc(),error=traceback.format_exc()))
        if monitor_exit and not interruption:interruption.append(dict(reason='monitor_exited_before_deadline',evidence=monitor_exit))
        startup_state=startup;interruption_state=interruption
        control_exit()
        save('heartbeat.json',dict(utc=utc(),monotonic=time.monotonic(),remaining_seconds=max(0,start['deadline_monotonic']-time.monotonic()),status='RUNNING' if registered else 'STARTUP_PENDING',serial_bytes=(folder/'serial.raw.log').stat().st_size,monitor_alive=monitor.poll() is None,collector_pid=os.getpid()))
        time.sleep(min(1,max(0,start['deadline_monotonic']-time.monotonic())))
    deadline_thread.join()  # Deadline/settings/finalization worker is independent of heartbeat
    # Keep the same monitor and pipe reader alive after the immutable run window.
    while monitor.poll() is None:
        control_exit();time.sleep(1)

try:main()
except Exception:
    save('collector_failure.json',dict(utc=utc(),error=traceback.format_exc(),reset_event=event()))
    if monitor and monitor.poll() is None:
        while monitor.poll() is None:time.sleep(1)
