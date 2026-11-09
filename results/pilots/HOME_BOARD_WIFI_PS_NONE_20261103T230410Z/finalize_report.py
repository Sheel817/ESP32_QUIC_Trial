import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

folder=Path(__file__).resolve().parent
root=folder.parents[2]
reference=root/'results/pilots/HOME_BOARD_PS_DEFAULT_20261103T225407Z'
profile=root/'profiles/wifi_ps_none_20261103'
stats=json.loads((folder/'HOME_BOARD_WIFI_PS_NONE_statistics.json').read_text())
monitor=json.loads((folder/'monitor_session.json').read_text())
checks=json.loads((folder/'startup_checks.json').read_text())
with (folder/'HOME_BOARD_WIFI_PS_NONE_APP_RTT_20261103T230410Z.csv').open() as f:
    rows=list(csv.DictReader(f))
assert len(rows)==10 and min(int(x['esp_log_uptime_ms']) for x in rows)>=60000
with (folder/'HOME_BOARD_WIFI_PS_NONE_ping_20261103T230410Z.csv').open() as f:
    pings=list(csv.DictReader(f))
assert len(pings)==30
with (reference/'HOME_BOARD_PS_DEFAULT_APP_RTT_20261103T225407Z.csv').open() as f:
    base_app=list(csv.DictReader(f))
assert len(base_app)==10
source_refs=[]
for path in [profile/'README.md',profile/'build_final.log',profile/'build/CMakeCache.txt',profile/'build/compile_commands.json',profile/'build/config/sdkconfig.json',profile/'build/flash_args',profile/'build/flasher_args.json',root/'main/quic_demo_main.c',root/'main/CMakeLists.txt',reference/'HOME_BOARD_PS_DEFAULT_statistics.json',reference/'HOME_BOARD_PS_DEFAULT_APP_RTT_20261103T225407Z.csv',reference/'HOME_BOARD_PS_DEFAULT_ping_20261103T225407Z.csv']:
    source_refs.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(folder/'source_references.json').write_text(json.dumps(source_refs,indent=2))
(folder/'experimental_application_source_snapshot.txt').write_bytes((root/'main/quic_demo_main.c').read_bytes())
table='\n'.join(f"| {r['seq']} | {r['esp_log_uptime_ms']} | {r['app_rtt_ms']} |" for r in rows)
if stats['ping_less_than_1_ms']:
    low,high=stats['ping_all_reply_mean_bounds_ms']
    ping_mean=f"Mean of all reported replies is bounded by **{low:.4f} <= mean < {high:.4f} ms**, allowing each `<1 ms` reply to lie in [0,1). No exact value was assigned to those replies."
    ping_compare=f"[{low:.4f}, {high:.4f}) ms"
else:
    ping_mean=f"Arithmetic mean of reported integer RTTs: **{stats['ping_reported_integer_mean_ms']:.4f} ms**, change {stats['ping_mean_change_ms']:.4f} ms ({stats['ping_mean_reduction_percent']:.2f}% lower) versus the fresh HOME_BOARD reference."
    ping_compare=f"{stats['ping_reported_integer_mean_ms']:.4f} ms"
text=f'''# HOME_BOARD — experimental WIFI_PS_NONE, Clumsy stopped

Prepared profile flashed and measured on HOME_BOARD ESP32-C6 revision v0.0, COM6, base MAC 40:4c:ca:56:bb:b0. DHT11 DATA=GPIO4, VCC=3V3, GND=GND (operator wiring). Earlier results remain preserved. No rebuild, firmware source edit, application timing change, or Clumsy start was performed.

## Pre-flash review

[Audit](./preflash_audit.json) PASS: both builds use ESP-IDF v6.1 at the same SDK path, GCC/G++ 15.2.0 at the same compiler paths, and CMake 4.0.3. Effective sdkconfig and generated sdkconfig JSON are equal. QUIC is selected; experiment cache is DEMO_WIFI_PS_NONE=ON and application compile metadata has DEMO_WIFI_PS_NONE=1 / DEMO_TRANSPORT_TCP_TLS=0. Removing the intended include and guarded power-mode block from current application source reproduces the preserved original exactly; GPIO, payload and timing remain unchanged. Audited preserved dependency/source/config entries have no unexpected changes.

The successful prepared build uses the documented alternate installed Python environment idf6.1_py3.14_env, monitor 1.10.0 and esptool 5.6.0. Earlier attempts failed Python preflight/environment checks; these were not the final build. Host tooling changed as documented; SDK/compiler and effective firmware config did not. No packages were installed or updated in this test.

Warnings reviewed before flashing: missing ESP_ROM_ELF_DIR affects generation of GDB ROM-symbol initialization; component include/dependency validation notices; wolfSSL not selected for generic ESP-TLS (the QUIC integration uses wolfSSL separately); and ngtcp2_acktr.c:292 `ent` may be used uninitialized. The latter dependency source matches preservation. These warnings were reported before flashing; no material unintended build/settings difference was found. Linking/partition checks had passed. [Prepared report copy](./prepared_build_report.md), [intended source diff](./prepared_source_change.diff), [source paths and hashes](./source_references.json).

Prepared application SHA-256 matched before flash and again before data collection: `6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198`, 1,637,280 bytes. New ELF SHA-256: `{checks['elf_sha256']}`. [Image information](./prepared_image_info.txt).

## Flash and controlled startup

Gracefully closed only the previous COM6 ESP-IDF monitor through its existing control file. Server PID 23100 was left running. Flashed exclusively from the prepared profile build directory using `esptool --chip esp32c6 --port COM6 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args`. Its arguments resolve to prepared bootloader at 0x0, prepared partition table at 0x8000, and prepared application at 0x10000. No whole-chip erase was performed; esptool erased the write ranges. Existing NVS was outside those ranges.

**All three artifact writes reported `Hash of data verified.` and esptool exited 0.** [Raw flash log (UTF-16)](./HOME_BOARD_WIFI_PS_NONE_flash.log), [flash result](./flash_result.json), [artifact hashes](./preflash_audit.json). Esptool logged an in-memory bootloader header/SHA update for flash parameters; the prepared input files remain unchanged.

Persistent ESP-IDF monitor uses the NEW prepared ELF. [Monitor command/process metadata](./monitor_session.json). Explicit controlled reset requested at **{monitor['controlled_reset_requested_utc']}**, with logging already active. Startup output received on initially opening the port is preserved separately before the `Command: 'reset'` marker and excluded from measurements. Flashing also caused downloader-entry and post-write hard resets. No later reset was requested.

The controlled startup prints ELF prefix `{checks['reported_digest_prefix']}...`, matching the new ELF; only a prefix is printed, so full on-device digest comparison is not claimed. It confirms:

- `requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)` — explicit successful setter and API readback.
- `wifi:Set ps type: 0, coexist: 0`. Initial `pm start, type:1` precedes the application setter and is superseded by the confirmed type-0 readback before QUIC starts.
- QUIC connection established and MQTT connected over QUIC.
- Actual assigned IPv4 **{stats['assigned_ip']}**, from this controlled startup, not assumed from a previous board.

[Startup checks](./startup_checks.json), [live serial log](./HOME_BOARD_WIFI_PS_NONE_serial.log). Startup gates were verified before accepting the collection; the immutable snapshot preserves its exact input.

## APP_RTT after 60000 ms boot uptime

Selected the first 10 fresh APP_RTT records in arrival order with ESP log uptime >=60000 ms from the controlled startup. No outliers removed. Host timestamps are Europe/Helsinki UTC+02:00 at second resolution; corresponding UTC is recorded in CSV.

| Sequence | ESP log uptime ms | APP_RTT ms |
|---:|---:|---:|
{table}

Mean **{stats['app_mean_ms']:.4f} ms**, min {stats['app_min_ms']:.3f}, max {stats['app_max_ms']:.3f}. Change versus fresh HOME_BOARD reference: **{stats['app_mean_change_ms']:.4f} ms** ({stats['app_mean_reduction_percent']:.2f}% lower). Collection finished **{stats['collection_complete_utc']}**.

[APP_RTT CSV](./HOME_BOARD_WIFI_PS_NONE_APP_RTT_20261103T230410Z.csv), [fixed raw serial snapshot through collection](./HOME_BOARD_WIFI_PS_NONE_serial_through_collection.log). APP_RTT is application publish-to-matched-echo latency; it includes transport/network and receive scheduling. Source timestamp/log references are lines 229, 526 and 194 of [experimental application snapshot](./experimental_application_source_snapshot.txt); setter/readback is at lines 585–594. It is distinct from ICMP RTT.

## Subsequent 30 pings

Command: `{' '.join(stats['ping_command'])}`. Started **{stats['ping_start_utc']}**, after APP_RTT collection; finished **{stats['ping_end_utc']}**. Monitor and QUIC traffic continued.

**{stats['ping_replies']} replies, {stats['ping_timeouts']} timeouts, {stats['ping_other_failures']} other failures** out of 30 requests. `<1 ms` observations: **{stats['ping_less_than_1_ms']}**; each retained literally in the CSV with numeric exact RTT blank. Reported integer RTT min {stats['ping_reported_integer_min_ms']}, max {stats['ping_reported_integer_max_ms']} ms. {ping_mean} All ping values/timeouts are retained.

Windows prints an approximate integer summary, preserved verbatim:

```text
{stats['ping_windows_summary']}
```

[Raw ping output](./HOME_BOARD_WIFI_PS_NONE_ping_raw.txt), [timestamped per-request CSV](./HOME_BOARD_WIFI_PS_NONE_ping_20261103T230410Z.csv), [full output with UTC timestamps](./HOME_BOARD_WIFI_PS_NONE_ping_output_timestamped.csv), [statistics](./HOME_BOARD_WIFI_PS_NONE_statistics.json).

## Comparison only with fresh HOME_BOARD reference

| Metric | Original/default HOME_BOARD | WIFI_PS_NONE HOME_BOARD |
|---|---:|---:|
| APP_RTT mean, 10 records | 75.4349 ms | {stats['app_mean_ms']:.4f} ms |
| Ping mean, 30 requests | 268.8667 ms | {ping_compare} |

[Fresh reference summary](../HOME_BOARD_PS_DEFAULT_20261103T225407Z/SUMMARY.md), [comparison CSV](./HOME_BOARD_default_vs_WIFI_PS_NONE_comparison.csv). No university-board measurements enter this comparison. The original reference has driver type-1 evidence plus inferred SDK default, without API readback; this experiment has explicit WIFI_PS_NONE API readback. This is one sequential pilot per setting; the observations alone do not establish a general causal effect or long-run distribution.

Clumsy was observed Stopped with the Start button and unchecked Lag before flashing; it was not started or reconfigured. Final process/socket/UI observations are saved alongside this summary. Server and persistent monitor are left running on the experimental firmware.
'''
(folder/'SUMMARY.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(app_count=len(rows),ping_count=len(pings),summary=str(folder/'SUMMARY.md')),indent=2))
