"""Orchestrator to launch HBPSN-08 collection cleanly."""
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

def main():
    root = Path(r"C:\Users\newsh\Desktop\ESP32_QUIC_Trial")
    study = root / "results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED"
    
    # Generate timestamp
    now_utc = dt.datetime.now(dt.timezone.utc)
    attempt_id = f"attempt_{now_utc.strftime('%Y%m%dT%H%M%SZ')}"
    
    run_dir = root / f"runs/HBPSN-08/{attempt_id}"
    mirror_dir = study / f"runs/HBPSN-08/{attempt_id}"
    
    run_dir.mkdir(parents=True, exist_ok=True)
    mirror_dir.mkdir(parents=True, exist_ok=True)
    
    # Locate clumsy_pre_manual_2.png
    candidates = [
        root / "main/runs/HBPSN-07/clumsy_pre_manual_2.png",
        Path(r"C:\Users\newsh\Pictures\Screenshots\clumsy_pre_manual_2.png"),
        root / "runs/HBPSN-08/clumsy_pre_manual_2.png"
    ]
    src_img = None
    for c in candidates:
        if c.exists():
            src_img = c
            break
    assert src_img is not None, "Could not locate clumsy_pre_manual_2 image"
    
    img_bytes = src_img.read_bytes()
    img_sha256 = hashlib.sha256(img_bytes).hexdigest()
    mtime_utc = dt.datetime.fromtimestamp(src_img.stat().st_mtime, dt.timezone.utc)
    helsinki_tz = dt.timezone(dt.timedelta(hours=2))
    mtime_helsinki = mtime_utc.astimezone(helsinki_tz)
    
    # Copy to both directories as clumsy_pre_manual.png
    for d in [run_dir, mirror_dir]:
        dest = d / "clumsy_pre_manual.png"
        dest.write_bytes(img_bytes)
        # Initialize SHA256SUMS.json
        manifest = [
            {
                "path": "clumsy_pre_manual.png",
                "bytes": len(img_bytes),
                "sha256": img_sha256
            }
        ]
        (d / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
    print(f"ATTEMPT_ID: {attempt_id}")
    print(f"PREFLIGHT_IMAGE_PATH: {src_img}")
    print(f"PREFLIGHT_SHA256: {img_sha256}")
    print(f"PREFLIGHT_LAST_WRITE_UTC: {mtime_utc.isoformat()}")
    print(f"PREFLIGHT_LAST_WRITE_HELSINKI: {mtime_helsinki.isoformat()}")
    
    # Launch collector process
    python_exe = r"C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe"
    collector_script = root / "tools/run_recorder/hbpsn08_collector.py"
    
    stdout_file = (run_dir / "collector.stdout.log").open("wb")
    stderr_file = (run_dir / "collector.stderr.log").open("wb")
    
    cmd = [
        python_exe,
        "-u",
        str(collector_script),
        "--run-dir", str(run_dir),
        "--mirror-dir", str(mirror_dir),
        "--port", "COM6",
        "--baud", "115200",
        "--duration", "2220.0"
    ]
    
    proc = subprocess.Popen(
        cmd,
        cwd=str(root),
        stdout=stdout_file,
        stderr=stderr_file
    )
    
    print(f"COLLECTOR_PID: {proc.pid}")
    
    # Wait for collector to initialize, reset, and log initial output
    time.sleep(8)
    
    # Check if process is still running
    poll = proc.poll()
    if poll is not None:
        stdout_file.close()
        stderr_file.close()
        out = (run_dir / "collector.stdout.log").read_text(encoding="utf-8", errors="replace")
        err = (run_dir / "collector.stderr.log").read_text(encoding="utf-8", errors="replace")
        print(f"Collector exited prematurely with code {poll}!\nSTDOUT:\n{out}\nSTDERR:\n{err}", file=sys.stderr)
        sys.exit(1)
        
    # Read reset_event.json
    reset_event_file = run_dir / "reset_event.json"
    if reset_event_file.exists():
        re_data = json.loads(reset_event_file.read_text(encoding="utf-8"))
        print(f"WINDOW_START_UTC: {re_data['reset_release_utc']}")
        print(f"WINDOW_START_HELSINKI: {re_data['reset_release_helsinki']}")
        print(f"FIXED_FINISH_DEADLINE_UTC: {re_data['deadline_utc']}")
        print(f"FIXED_FINISH_DEADLINE_HELSINKI: {re_data['deadline_helsinki']}")
        
    # Read first lines of serial_raw.log
    serial_file = run_dir / "serial_raw.log"
    if serial_file.exists():
        s_data = serial_file.read_text(encoding="utf-8", errors="replace")
        print("--- INITIAL SERIAL OUTPUT ---")
        lines = [line.strip() for line in s_data.splitlines() if line.strip()]
        for l in lines[:30]:
            print(l)
        print(f"--- TOTAL INITIAL LINES: {len(lines)} ---")

if __name__ == "__main__":
    main()
