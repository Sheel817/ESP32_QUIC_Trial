"""Recorder host-side reliability. No serial, reset, network or GUI input APIs."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import uuid


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Reports:
    """Bounded atomic replacement, unique temporary names and independent journal."""
    def __init__(self, folder, replace=os.replace):
        self.folder = Path(folder)
        self.replace = replace
        self.lock = threading.Lock()
        self.errors = []

    def error(self, operation, error, **extra):
        row = dict(utc=utc(), monotonic=time.monotonic(), operation=operation,
                   error=repr(error), traceback=traceback.format_exc(), **extra)
        with self.lock:
            self.errors.append(row)
            try:
                with (self.folder/'reporting_errors.jsonl').open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row)+'\n')
            except Exception as journal_error:
                # A broken error reporter must never escape into the timer.
                try:
                    print(json.dumps(dict(**row, journal_error=repr(journal_error))), file=sys.stderr, flush=True)
                except Exception:
                    pass  # Last resort remains self.errors in memory.

    def save(self, name, value):
        target = self.folder/name
        temp = target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            data = json.dumps(value, indent=2).encode('utf-8')
            with temp.open('xb') as f:
                f.write(data)
                f.flush()
            for attempt in range(1, 4):
                try:
                    self.replace(temp, target)
                    return True
                except OSError as error:
                    self.error('atomic_replace', error, target=str(target), attempt=attempt,
                               exhausted=attempt==3)
                    if attempt < 3:
                        time.sleep(0.025*attempt)
            # Preserve the unwritten report; do not overwrite target in-place.
            fallback = target.with_name(target.name+'.failed_'+uuid.uuid4().hex+'.json')
            try:
                with fallback.open('xb') as f:
                    f.write(data)
            except Exception as error:
                self.error('fallback_report', error, target=str(fallback))
            return False
        except Exception as error:
            self.error('write_report', error, target=str(target))
            return False
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError as error:
                self.error('temporary_cleanup', error, target=str(temp))


class SettingsEvidence:
    """Explicit request/response broker. An absent observer is never a PASS.

    A read-only GUI observer supplies image + actual acquisition UTC/monotonic
    times and its observations. It must not label an older image as current.
    Snapshot timing brackets are stored separately from the recording deadline.
    """
    def __init__(self, reports, expected, timeout=30):
        self.reports = reports
        self.expected = expected
        self.timeout = timeout
        self.pending = reports.folder/'settings_requests'
        self.pending.mkdir(exist_ok=True)

    def capture(self, phase, anchor=None):
        request = dict(phase=phase, nonce=uuid.uuid4().hex, requested_utc=utc(),
                       requested_monotonic=time.monotonic(), expected=self.expected,
                       anchor=anchor, response_timeout_seconds=self.timeout)
        path = self.pending/(phase+'.request.json')
        path.write_text(json.dumps(request, indent=2), encoding='utf-8')
        response = self.pending/(phase+'.response.json')
        until = time.monotonic()+self.timeout
        result = dict(status='MISSING', phase=phase, request=request,
                      reason='No complete, timely screenshot/observation response')
        while time.monotonic() < until:
            try:
                if not response.exists():
                    time.sleep(min(.05, max(0, until-time.monotonic())))
                    continue
                value = json.loads(response.read_text(encoding='utf-8'))
                assert value['nonce'] == request['nonce'], 'Evidence request nonce mismatch'
                image = (self.reports.folder/value['screenshot']).resolve()
                assert image.is_relative_to(self.reports.folder.resolve()), 'Screenshot outside run directory'
                assert image.stat().st_size > 0, 'Empty screenshot'
                assert hashlib.sha256(image.read_bytes()).hexdigest() == value['sha256'], 'Image hash mismatch'
                first = dt.datetime.fromisoformat(value['capture_started_utc'])
                last = dt.datetime.fromisoformat(value['capture_completed_utc'])
                assert first.tzinfo and last.tzinfo, 'Screenshot UTC offset missing'
                assert dt.datetime.fromisoformat(request['requested_utc']) <= first <= last <= dt.datetime.now(dt.timezone.utc), 'Invalid actual capture interval'
                assert request['requested_monotonic'] <= value['capture_started_monotonic'] <= value['capture_completed_monotonic'] <= time.monotonic(), 'Invalid capture monotonic interval'
                assert value['source_type'] in ('GUI_observed', 'operator_reported'), 'Evidence source type missing'
                matches = value['observed'] == self.expected
                result = dict(status='PASS' if matches else 'MISMATCH', phase=phase,
                              request=request, evidence=value,
                              reason=None if matches else 'Observed settings differ from expected')
            except Exception as error:
                self.reports.error('settings_evidence_validation', error, phase=phase)
                result = dict(status='INVALID', phase=phase, request=request, reason=str(error))
            break
        if phase == 'end_of_run' and anchor and 'evidence' in result:
            result['capture_started_seconds_after_deadline'] = (dt.datetime.fromisoformat(result['evidence']['capture_started_utc'])-dt.datetime.fromisoformat(anchor['deadline_utc'])).total_seconds()
            result['capture_delay_clock'] = 'Actual capture UTC minus original deadline UTC; screenshot-runtime monotonic estimates are labelled in evidence'
        result['evaluated_utc'] = utc()
        self.reports.save(phase+'_settings_check.json', result)
        return result


def deadline_worker(start, reports, evidence, finalize, stopped, before_finalization=None):
    """Independent of heartbeat/register/reporting loops; never moves cutoff."""
    threading.Event().wait(max(0, start['deadline_monotonic']-time.monotonic()))
    # Set the cutoff first; no I/O, GUI wait or reporting retry precedes it.
    stopped.set()
    observed = dict(fixed_deadline_utc=start['deadline_utc'], observed_utc=utc(),
                    observed_monotonic=time.monotonic(),
                    lateness_ms=max(0, (time.monotonic()-start['deadline_monotonic'])*1000))
    try:
        reports.save('recording_cutoff_observed.json', observed)
    except Exception as error:
        reports.error('cutoff_reporting', error)
    post = dict(status='MISSING', reason='End-of-run capture failed before response')
    try:
        post = evidence.capture('end_of_run', start)
    except Exception as error:
        reports.error('end_settings_capture', error)
    # Finalization always executes even if settings capture/reporting fails.
    try:
        if before_finalization:
            before_finalization(post)
    except Exception as error:
        reports.error('post_settings_reporting', error)
    try:
        finalize(start, post)
    except Exception as error:
        reports.error('finalization', error)
        reports.save('FINALIZATION_FAILED.json', dict(utc=utc(), error=repr(error),
                     fixed_deadline_utc=start['deadline_utc'], recover_from_raw=True))


def arm_deadline(start, reports, evidence, finalize, before_finalization=None):
    stopped = threading.Event()
    worker = threading.Thread(target=deadline_worker,
        args=(start, reports, evidence, finalize, stopped, before_finalization),
        name='independent-fixed-deadline', daemon=False)
    worker.start()
    return stopped, worker
