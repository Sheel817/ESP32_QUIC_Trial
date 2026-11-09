"""Small adversarial tests: no device, GUI input, formal outputs or register writes."""
import ast,ctypes,csv,datetime as dt,hashlib,json,os,re,statistics,tempfile,threading,time,unittest
from pathlib import Path
from reliability import Reports,SettingsEvidence,arm_deadline,utc

class ReliabilityTests(unittest.TestCase):
    def test_permission_error_retry_exhaustion_and_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            count=0
            def replace(a,b):
                nonlocal count
                count+=1
                if count<=3:raise PermissionError(13,'injected Access denied')
                os.replace(a,b)
            r=Reports(d,replace)
            self.assertFalse(r.save('heartbeat.json',dict(test=True)))
            self.assertEqual(count,3)
            self.assertEqual(len(list(Path(d).glob('heartbeat.json.failed_*.json'))),1)
            self.assertTrue(r.save('heartbeat.json',dict(recovered=True)))
            self.assertTrue(r.errors[-1]['exhausted'])

    def test_missing_settings_stays_missing(self):
        with tempfile.TemporaryDirectory() as d:
            r=Reports(d);e=SettingsEvidence(r,dict(capture='RUNNING'),timeout=.01)
            self.assertEqual(e.capture('end_of_run')['status'],'MISSING')

    def test_capture_failure_does_not_skip_finalization(self):
        with tempfile.TemporaryDirectory() as d:
            class Broken:
                def capture(self,*args):raise PermissionError('injected screenshot failure')
            called=[];r=Reports(d)
            anchor=dict(deadline_monotonic=time.monotonic()+.03,deadline_utc=utc())
            stopped,worker=arm_deadline(anchor,r,Broken(),lambda start,post:called.append(post))
            worker.join(1)
            self.assertTrue(stopped.is_set());self.assertEqual(called[0]['status'],'MISSING')
            self.assertEqual(r.errors[0]['operation'],'end_settings_capture')

    def test_deadline_independent_of_blocked_reporter(self):
        with tempfile.TemporaryDirectory() as d:
            class NoEvidence:
                def capture(self,*args):return dict(status='MISSING')
            called=threading.Event();r=Reports(d)
            start=dict(deadline_monotonic=time.monotonic()+.04,deadline_utc=utc())
            stopped,worker=arm_deadline(start,r,NoEvidence(),lambda *x:called.set())
            # Models a hung main/reporting worker; timer owns its own thread.
            self.assertTrue(called.wait(.4));worker.join()
            self.assertTrue(stopped.is_set())

    def test_actual_collector_finalizer_offline(self):
        """Execute only finalizer definitions, never the serial/reset main entrypoint."""
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);r=Reports(folder)
            sensor=folder/'sensor.csv';sensor.write_text('server_receive_utc,seq,sensor_error\n2026-11-04T00:01:01Z,2,0\n')
            lines=['ESP-ROM:esp32c6-20220919','I (50000) quic_demo_main: APP_RTT seq=1 app_rtt_ms=90.000','I (60000) quic_demo_main: APP_RTT seq=2 app_rtt_ms=12.000','I (65000) quic_demo_main: APP_RTT seq=3 app_rtt_ms=18.000']
            (folder/'serial.raw.log').write_text('\n'.join(lines)+'\n')
            (folder/'serial_receipts.jsonl').write_text(''.join(json.dumps(dict(utc='2026-11-04T00:01:01+00:00',monotonic=61))+'\n' for _ in lines))
            r.save('post_recording_settings_check.json',dict(status='PASS',test_only=True))
            tree=ast.parse(Path(__file__).with_name('collector_v2.py').read_text())
            functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('finalize','csv_save','sha','register')]
            env=dict(csv=csv,dt=dt,hashlib=hashlib,json=json,os=os,re=re,statistics=statistics,sys=__import__('sys'),threading=threading,time=time,traceback=__import__('traceback'),folder=folder,lock=threading.RLock(),tail_threads=[],tail_errors=[],preflight=dict(server_sensor_source=str(sensor),plan_sha256='TEST_ONLY'),run_id='TEST_ONLY_OFFLINE_FINALIZER',transport='QUIC',condition='CONTROL',monitor=type('Monitor',(),dict(pid=0))(),reports=r,save=r.save,utc=utc)
            exec(compile(ast.Module(body=functions,type_ignores=[]),'collector_v2_functions_only','exec'),env)
            anchor=dict(reset_release_utc='2026-11-04T00:00:00+00:00',deadline_utc='2026-11-04T00:37:00+00:00',deadline_monotonic=time.monotonic())
            with (folder/'serial.raw.log').open('ab') as raw_serial, (folder/'serial_receipts.jsonl').open('a') as index:
                env.update(raw_serial=raw_serial,index=index,Path=Path)
                env['finalize'](anchor,dict(pass_all=True),[])
            stats=json.loads((folder/'statistics.json').read_text())
            self.assertEqual(stats['all_rtt_count'],3)
            self.assertEqual(stats['eligible_count'],2)
            self.assertEqual(stats['selected_count'],2)
            self.assertEqual(stats['mean_ms'],15)
            self.assertEqual(stats['p95_ms'],18)
            self.assertTrue((folder/'COMPLETE.json').exists())
            request=json.loads((folder/'register_final_request.json').read_text())
            self.assertFalse(request['automatic_register_apply'])

def windows_share_lock_probe(folder):
    """Read handle lacking FILE_SHARE_DELETE reproduces replace denial on scratch files."""
    path=Path(folder);dst=path/'lock_probe_target.json';src=path/'lock_probe_source.json'
    dst.write_text('original');src.write_text('replacement')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]
    k.CreateFileW.restype=ctypes.c_void_p;k.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=k.CreateFileW(str(dst.resolve()),0x80000000,0x1|0x2,None,3,0,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    result=dict(test_only=True,utc=utc(),read_handle_share_delete=False)
    try:
        try:os.replace(src,dst);result['unexpected_success']=True
        except PermissionError as e:result.update(error=repr(e),winerror=e.winerror,reproduced=True)
    finally:k.CloseHandle(handle)
    os.replace(src,dst);result['replacement_after_handle_close']=dst.read_text()=='replacement'
    (path/'windows_share_lock_probe.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':unittest.main(verbosity=2)
