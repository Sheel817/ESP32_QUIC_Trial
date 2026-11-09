"""Persistent HBPSN-08 QUIC LAG100_OUT collector and fixed-window timer."""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import traceback
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path
import serial
import esp_pylib.serial_reset as sr

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def helsinki_now():
    return dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=2))).isoformat()

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_json(paths, data):
    raw = json.dumps(data, indent=2)
    for p in paths:
        target = Path(p)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(raw, encoding='utf-8')

def update_registers(study_dir, root_dir, row_idx, patch):
    reg_csv = Path(study_dir) / 'run_register.csv'
    raw_csv = reg_csv.read_bytes()
    lines = raw_csv.splitlines(keepends=True)
    reader = csv.DictReader(io.StringIO(raw_csv.decode('utf-8-sig')))
    headers = reader.fieldnames
    rows = list(reader)

    # Safety assertions: verify earlier rows untouched
    for i in range(row_idx):
        assert rows[i]['run_id'] == f'HBPSN-0{i+1}'
    assert rows[row_idx]['run_id'] == 'HBPSN-08'

    target = dict(rows[row_idx])
    target.update(patch)
    s = io.StringIO(newline='')
    w = csv.DictWriter(s, fieldnames=headers, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    w.writerow(target)

    # Row 8 is index 7 in rows, which is line 8 in 0-based lines (line 1 is header)
    csv_line_idx = row_idx + 1
    updated_lines = list(lines)
    updated_lines[csv_line_idx] = s.getvalue().encode('utf-8')
    assert all(updated_lines[i] == lines[i] for i in range(len(lines)) if i != csv_line_idx)
    reg_csv.write_bytes(b''.join(updated_lines))

    # Update XLSX
    xlsx_path = Path(root_dir) / 'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx'
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    q = lambda x: '{' + ns + '}' + x
    def col(n):
        s = ''
        while n:
            n, a = divmod(n - 1, 26)
            s = chr(65 + a) + s
        return s

    xml_row_num = str(row_idx + 2) # Row 8 is row r="9" (1-based, row 1 is header)
    with zipfile.ZipFile(xlsx_path) as z:
        xml = z.read('xl/worksheets/sheet1.xml')
        pattern = (rb'<(?:\w+:)?row\b[^>]*\br="' + xml_row_num.encode() + rb'"[^>]*>.*?</(?:\w+:)?row>')
        m = re.search(pattern, xml, re.S)
        assert m, f'Row {xml_row_num} not found in XLSX sheet1.xml'
        row_elem = E.fromstring(b'<root xmlns="' + ns.encode() + b'" xmlns:x="' + ns.encode() + b'">' + m.group() + b'</root>')[0]
        for k, value in patch.items():
            if k not in headers:
                continue
            ref = col(headers.index(k) + 1) + xml_row_num
            c = next((c for c in row_elem if c.get('r') == ref), None)
            if c is None:
                c = E.SubElement(row_elem, q('c'), {'r': ref})
            for child in list(c):
                c.remove(child)
            c.set('t', 'inlineStr')
            E.SubElement(E.SubElement(c, q('is')), q('t')).text = str(value)
        updated_xml = xml[:m.start()] + E.tostring(row_elem, encoding='utf-8') + xml[m.end():]
        tmp_xlsx = xlsx_path.with_name(xlsx_path.name + '.HBPSN08_UPDATE.tmp')
        with zipfile.ZipFile(tmp_xlsx, 'w') as targetzip:
            for info in z.infolist():
                targetzip.writestr(info, updated_xml if info.filename == 'xl/worksheets/sheet1.xml' else z.read(info.filename))
    os.replace(tmp_xlsx, xlsx_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--mirror-dir', required=True)
    parser.add_argument('--port', default='COM6')
    parser.add_argument('--baud', type=int, default=115200)
    parser.add_argument('--duration', type=float, default=2220.0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    mirror_dir = Path(args.mirror_dir).resolve()
    dirs = [run_dir, mirror_dir]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    study_dir = Path(r'C:\Users\newsh\Desktop\ESP32_QUIC_Trial\results\experiments\HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED')
    root_dir = Path(r'C:\Users\newsh\Desktop\ESP32_QUIC_Trial')

    # Server log sources
    server_sources = {
        'stdout': str(root_dir / 'logs/quic_server_start_20261103T163259.stdout.log'),
        'stderr': str(root_dir / 'logs/quic_server_start_20261103T163259.stderr.log'),
        'sensor_csv': str(root_dir / 'logs/sensor_20261103T143300_220342Z_c7ett8c2.csv')
    }

    server_boundaries = {}
    for name, path_str in server_sources.items():
        p = Path(path_str)
        size = p.stat().st_size if p.exists() else 0
        server_boundaries[name] = {'source': path_str, 'byte_offset': size}

    # Open serial port
    print(f"[{helsinki_now()}] Opening {args.port} at {args.baud} baud...", flush=True)
    ser = serial.Serial(args.port, args.baud, timeout=0.05)
    ser.dtr = False
    ser.reset_input_buffer()

    # Perform SDK RTS hard reset
    print(f"[{helsinki_now()}] Triggering controlled ESP32-C6 reset via RTS pulse...", flush=True)
    sr.hard_reset(ser, hold_delay=0.1, post_release_delay=0.0)

    # Capture release time immediately
    reset_monotonic = time.monotonic()
    reset_utc = utc_now()
    reset_helsinki = helsinki_now()
    deadline_monotonic = reset_monotonic + args.duration
    deadline_utc = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=args.duration)).isoformat()
    deadline_helsinki = (dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=2))) + dt.timedelta(seconds=args.duration)).isoformat()

    reset_event = {
        'reset_release_utc': reset_utc,
        'reset_release_monotonic': reset_monotonic,
        'deadline_utc': deadline_utc,
        'deadline_monotonic': deadline_monotonic,
        'reset_release_helsinki': reset_helsinki,
        'deadline_helsinki': deadline_helsinki,
        'target_duration_seconds': args.duration,
        'method': 'SDK hard reset (RTS toggle via esp_pylib); host clocks sampled immediately after release',
        'server_boundaries': server_boundaries
    }
    save_json([d / 'reset_event.json' for d in dirs], reset_event)

    # Open serial log files for writing
    serial_raw_files = []
    serial_compat_files = []
    receipts_files = []
    for d in dirs:
        serial_raw_files.append((d / 'serial_raw.log').open('ab', buffering=0))
        serial_compat_files.append((d / 'serial.raw.log').open('ab', buffering=0))
        receipts_files.append((d / 'serial_receipts.jsonl').open('a', encoding='utf-8', buffering=1))

    # Initial register commit for Row 8 (HBPSN-08) -> RUNNING
    attempt_id = run_dir.name
    reg_patch = {
        'status': 'RUNNING',
        'transport': 'QUIC',
        'condition': 'LAG100_OUT',
        'preflight_status': 'PASS',
        'startup_status': 'STARTUP_PENDING',
        'settings_evidence_type': 'clumsy_pre_manual.png; operator-configured LAG100_OUT',
        'boot_session_id': f'HBPSN-08/{reset_utc}',
        'reset_release_utc': reset_utc,
        'recording_end_utc': deadline_utc,
        'metadata_path': f'runs/HBPSN-08/{attempt_id}/metadata.json',
        'raw_serial_path': f'runs/HBPSN-08/{attempt_id}/serial_raw.log',
        'deviation_reason': f'Start_UTC: {reset_utc}; Start_Helsinki: {reset_helsinki}; QUIC LAG100_OUT; validity pending post-recording screenshot and operator review.'
    }
    update_registers(study_dir, root_dir, 7, reg_patch)
    print(f"[{helsinki_now()}] Register committed: Row 8 RUNNING (Start: {reset_helsinki} / {reset_utc}).", flush=True)

    running_json = {
        'status': 'RUNNING',
        'run_id': 'HBPSN-08',
        'transport': 'QUIC',
        'condition': 'LAG100_OUT',
        'actual_start_utc': reset_utc,
        'actual_start_helsinki': reset_helsinki,
        'deadline_utc': deadline_utc,
        'deadline_helsinki': deadline_helsinki,
        'collector_pid': os.getpid(),
        'defined_window_seconds': args.duration
    }
    save_json([d / 'RUNNING.json' for d in dirs], running_json)

    # Tail server logs in background threads
    stop_tail = threading.Event()
    def tail_server(name, path_str, boundary_offset):
        try:
            p = Path(path_str)
            target_files = [(d / f'server.{name}.raw.log').open('ab', buffering=0) for d in dirs]
            with p.open('rb') as src:
                src.seek(boundary_offset)
                while not stop_tail.is_set() and time.monotonic() < deadline_monotonic:
                    line = src.readline()
                    if line:
                        for tf in target_files:
                            tf.write(line)
                    else:
                        time.sleep(0.05)
            for tf in target_files:
                tf.close()
        except Exception as e:
            print(f"Error tailing {name}: {e}", file=sys.stderr, flush=True)

    for name, boundary in server_boundaries.items():
        threading.Thread(target=tail_server, args=(name, boundary['source'], boundary['byte_offset']), daemon=True).start()

    # Serial reader loop
    line_buffer = bytearray()
    raw_lines = []
    receipts = []
    startup_verified = False
    startup_details = {}

    last_heartbeat = 0
    sample_count = 0

    print(f"[{helsinki_now()}] Starting 37-minute collection loop (Deadline: {deadline_helsinki} / {deadline_utc})...", flush=True)

    while time.monotonic() < deadline_monotonic:
        chunk = ser.read(1024)
        now_mono = time.monotonic()
        now_utc = utc_now()
        if chunk:
            for f in serial_raw_files:
                f.write(chunk)
            for f in serial_compat_files:
                f.write(chunk)

            line_buffer.extend(chunk)
            while b'\n' in line_buffer:
                idx = line_buffer.index(b'\n')
                raw_line = bytes(line_buffer[:idx+1])
                del line_buffer[:idx+1]

                decoded = raw_line.decode('utf-8', errors='replace')
                raw_lines.append(decoded)
                receipt = {'utc': now_utc, 'monotonic': now_mono, 'line_no': len(raw_lines)}
                receipts.append(receipt)
                for rf in receipts_files:
                    rf.write(json.dumps(receipt) + '\n')

                if 'APP_RTT' in decoded:
                    sample_count += 1

                # Check startup conditions if not yet verified
                if not startup_verified:
                    all_text = ''.join(raw_lines)
                    has_boot = 'ESP-ROM:esp32c6' in all_text
                    has_mac = '40:4c:ca:56:bb:b0' in all_text
                    has_transport = 'Starting ESP32-C6 DHT11 over QUIC' in all_text
                    has_ps = 'requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)' in all_text
                    ip_match = re.search(r'example_netif_sta ip: ([\d.]+)', all_text)
                    has_quic = 'QUIC connection established' in all_text
                    has_mqtt = 'MQTT connected over QUIC' in all_text
                    has_sub = 'Subscription acknowledged' in all_text
                    has_tls = 'QUIC negotiated TLS=TLSv1.3' in all_text or 'TLSv1.3' in all_text

                    if has_boot and has_transport and has_ps and ip_match and has_quic and has_mqtt and has_sub:
                        startup_verified = True
                        assigned_ip = ip_match.group(1)
                        startup_details = {
                            'pass_all': True,
                            'assigned_ip': assigned_ip,
                            'verified_utc': utc_now(),
                            'verified_helsinki': helsinki_now(),
                            'gates': {
                                'boot_banner': has_boot,
                                'mac': has_mac,
                                'transport_firmware': has_transport,
                                'wifi_ps_none': has_ps,
                                'assigned_ip': bool(ip_match),
                                'quic_connected': has_quic,
                                'mqtt_connected': has_mqtt,
                                'subscription': has_sub,
                                'tls': has_tls
                            }
                        }
                        save_json([d / 'startup_checks.json' for d in dirs], startup_details)
                        # Update Row 8 startup_status to PASS in registers
                        update_registers(study_dir, root_dir, 7, {'startup_status': 'PASS', 'actual_assigned_ip': assigned_ip})
                        print(f"[{helsinki_now()}] Startup gates VERIFIED PASS! Assigned IP: {assigned_ip}", flush=True)

        if now_mono - last_heartbeat >= 2.0:
            last_heartbeat = now_mono
            hb = {
                'utc': now_utc,
                'monotonic': now_mono,
                'remaining_seconds': max(0.0, deadline_monotonic - now_mono),
                'status': 'RUNNING',
                'startup_verified': startup_verified,
                'raw_line_count': len(raw_lines),
                'app_rtt_count': sample_count,
                'collector_pid': os.getpid()
            }
            save_json([d / 'heartbeat.json' for d in dirs], hb)

    # 37-minute deadline reached!
    cutoff_mono = time.monotonic()
    cutoff_utc = utc_now()
    stop_tail.set()
    print(f"[{helsinki_now()}] 37-minute collection window reached. Finalizing...", flush=True)

    for f in serial_raw_files + serial_compat_files + receipts_files:
        try:
            f.flush()
            f.close()
        except Exception:
            pass

    cutoff_event = {
        'fixed_deadline_utc': deadline_utc,
        'observed_cutoff_utc': cutoff_utc,
        'observed_cutoff_monotonic': cutoff_mono,
        'lateness_ms': max(0.0, (cutoff_mono - deadline_monotonic) * 1000.0)
    }
    save_json([d / 'recording_cutoff_observed.json' for d in dirs], cutoff_event)

    # Parse RTTs
    parsed = []
    excluded = []
    eligible = []
    seen_seq = set()
    initial_boot = True
    rom_count = 0
    last_uptime = None

    for idx, line in enumerate(raw_lines):
        if 'ESP-ROM:esp32c6' in line:
            rom_count += 1
            if rom_count > 1:
                initial_boot = False

        uptime_match = re.search(r'\b[IWE] \((\d+)\)', line)
        if uptime_match:
            uptime = int(uptime_match.group(1))
            if last_uptime is not None and last_uptime > 60000 and uptime < last_uptime - 1000:
                initial_boot = False
            last_uptime = uptime

        m = re.search(r'\bI \((\d+)\) quic_demo_main: APP_RTT seq=(\d+) app_rtt_ms=([\d.]+)', line)
        if not m:
            continue

        r = {
            'source_line': idx + 1,
            'esp_log_uptime_ms': int(m.group(1)),
            'seq': int(m.group(2)),
            'app_rtt_ms': m.group(3),
            'run_id': 'HBPSN-08',
            'transport': 'QUIC',
            'condition': 'LAG100_OUT',
            'boot_session': f'HBPSN-08/{reset_utc}',
            'raw_line': line.strip()
        }
        parsed.append(r)

        reason = ''
        if not initial_boot:
            reason = 'subsequent_boot_or_timestamp_regression'
        elif r['esp_log_uptime_ms'] < 60000:
            reason = 'warmup_below_60000_ms'
        elif r['esp_log_uptime_ms'] >= 2220000:
            reason = 'at_or_above_2220000_ms'
        elif r['seq'] in seen_seq:
            reason = 'duplicate_sequence'

        if reason:
            excluded.append(dict(**r, exclusion_reason=reason))
        else:
            eligible.append(r)
        seen_seq.add(r['seq'])

    selected = eligible[:415]
    values = [float(r['app_rtt_ms']) for r in selected]
    fields = ['source_line', 'esp_log_uptime_ms', 'seq', 'app_rtt_ms', 'run_id', 'transport', 'condition', 'boot_session', 'raw_line']

    for d in dirs:
        with (d / 'all_rtts.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(parsed)
        with (d / 'eligible_rtts.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(eligible)
        with (d / 'selected_first_415.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(selected)
        with (d / 'eligible_extra.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(eligible[415:])
        with (d / 'excluded_rtts.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields + ['exclusion_reason']); w.writeheader(); w.writerows(excluded)

    # Statistics
    ordered = sorted(values)
    mean_val = statistics.mean(values) if values else None
    sd_val = statistics.stdev(values) if len(values) > 1 else None
    med_val = statistics.median(values) if values else None
    min_val = min(values) if values else None
    max_val = max(values) if values else None
    p95_val = ordered[math.ceil(0.95 * len(ordered)) - 1] if ordered else None

    stats = {
        'status': 'FINISHED_PENDING_MANUAL_REVIEW',
        'run_id': 'HBPSN-08',
        'transport': 'QUIC',
        'condition': 'LAG100_OUT',
        'recording_start_utc': reset_utc,
        'fixed_deadline_utc': deadline_utc,
        'finalization_utc': utc_now(),
        'defined_window_seconds': args.duration,
        'all_rtt_count': len(parsed),
        'eligible_count': len(eligible),
        'selected_count': len(selected),
        'shortfall': 415 - len(selected),
        'mean_ms': round(mean_val, 3) if mean_val else None,
        'sd_ms': round(sd_val, 3) if sd_val else None,
        'median_ms': round(med_val, 3) if med_val else None,
        'p95_ms': round(p95_val, 3) if p95_val else None,
        'minimum_ms': round(min_val, 3) if min_val else None,
        'maximum_ms': round(max_val, 3) if max_val else None
    }
    save_json([d / 'statistics.json' for d in dirs], stats)
    save_json([d / 'metadata.json' for d in dirs], dict(**stats, collector_pid=os.getpid()))

    # SHA256SUMS.json
    for d in dirs:
        manifest = []
        for p in d.iterdir():
            if p.is_file() and p.name not in ('SHA256SUMS.json', 'monitor_stream.log', 'monitor_after_run.log'):
                manifest.append({'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha256_file(p)})
        (d / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    finalized = {
        'status': 'FINISHED_PENDING_MANUAL_REVIEW',
        'processing_status': 'FINALIZED',
        'deadline_utc': deadline_utc,
        'selected_count': len(selected),
        'shortfall': 415 - len(selected)
    }
    save_json([d / 'FINALIZED.json' for d in dirs], finalized)
    print(f"[{helsinki_now()}] HBPSN-08 Finalized. Selected {len(selected)} samples. Mean: {stats['mean_ms']} ms.", flush=True)

    # Keep serial open in idle mode
    while ser.is_open:
        time.sleep(1)

if __name__ == '__main__':
    main()
