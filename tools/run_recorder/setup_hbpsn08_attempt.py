"""Prepare fresh attempt directory for HBPSN-08."""
import datetime as dt
import hashlib
import json
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
    
    src_img = root / "main/runs/HBPSN-07/clumsy_pre_manual_2.png"
    if not src_img.exists():
        src_img = Path(r"C:\Users\newsh\Pictures\Screenshots\clumsy_pre_manual_2.png")
    assert src_img.exists(), f"Preflight image not found: {src_img}"
    
    img_bytes = src_img.read_bytes()
    img_sha256 = hashlib.sha256(img_bytes).hexdigest()
    mtime_utc = dt.datetime.fromtimestamp(src_img.stat().st_mtime, dt.timezone.utc)
    helsinki_tz = dt.timezone(dt.timedelta(hours=2))
    mtime_helsinki = mtime_utc.astimezone(helsinki_tz)
    
    for d in [run_dir, mirror_dir]:
        dest = d / "clumsy_pre_manual.png"
        dest.write_bytes(img_bytes)
        manifest = [
            {
                "path": "clumsy_pre_manual.png",
                "bytes": len(img_bytes),
                "sha256": img_sha256
            }
        ]
        (d / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
    print(f"ATTEMPT_ID: {attempt_id}")
    print(f"RUN_DIR: {run_dir}")
    print(f"MIRROR_DIR: {mirror_dir}")
    print(f"PREFLIGHT_IMAGE_PATH: {src_img}")
    print(f"PREFLIGHT_SHA256: {img_sha256}")
    print(f"PREFLIGHT_LAST_WRITE_UTC: {mtime_utc.isoformat()}")
    print(f"PREFLIGHT_LAST_WRITE_HELSINKI: {mtime_helsinki.isoformat()}")

if __name__ == "__main__":
    main()
