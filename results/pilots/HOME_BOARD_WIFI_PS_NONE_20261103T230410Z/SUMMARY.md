# HOME_BOARD — experimental WIFI_PS_NONE, Clumsy stopped

Prepared profile flashed and measured on HOME_BOARD ESP32-C6 revision v0.0, COM6, base MAC 40:4c:ca:56:bb:b0. DHT11 DATA=GPIO4, VCC=3V3, GND=GND (operator wiring). Earlier results remain preserved. No rebuild, firmware source edit, application timing change, or Clumsy start was performed.

## Pre-flash review

[Audit](./preflash_audit.json) PASS: both builds use ESP-IDF v6.1 at the same SDK path, GCC/G++ 15.2.0 at the same compiler paths, and CMake 4.0.3. Effective sdkconfig and generated sdkconfig JSON are equal. QUIC is selected; experiment cache is DEMO_WIFI_PS_NONE=ON and application compile metadata has DEMO_WIFI_PS_NONE=1 / DEMO_TRANSPORT_TCP_TLS=0. Removing the intended include and guarded power-mode block from current application source reproduces the preserved original exactly; GPIO, payload and timing remain unchanged. Audited preserved dependency/source/config entries have no unexpected changes.

The successful prepared build uses the documented alternate installed Python environment idf6.1_py3.14_env, monitor 1.10.0 and esptool 5.6.0. Earlier attempts failed Python preflight/environment checks; these were not the final build. Host tooling changed as documented; SDK/compiler and effective firmware config did not. No packages were installed or updated in this test.

Warnings reviewed before flashing: missing ESP_ROM_ELF_DIR affects generation of GDB ROM-symbol initialization; component include/dependency validation notices; wolfSSL not selected for generic ESP-TLS (the QUIC integration uses wolfSSL separately); and ngtcp2_acktr.c:292 `ent` may be used uninitialized. The latter dependency source matches preservation. These warnings were reported before flashing; no material unintended build/settings difference was found. Linking/partition checks had passed. [Prepared report copy](./prepared_build_report.md), [intended source diff](./prepared_source_change.diff), [source paths and hashes](./source_references.json).

Prepared application SHA-256 matched before flash and again before data collection: `6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198`, 1,637,280 bytes. New ELF SHA-256: `9b23e164f8d6fd4702450b687c76ef3fa8ced802945dc23dd2f4d102c35c0f3d`. [Image information](./prepared_image_info.txt).

## Flash and controlled startup

Gracefully closed only the previous COM6 ESP-IDF monitor through its existing control file. Server PID 23100 was left running. Flashed exclusively from the prepared profile build directory using `esptool --chip esp32c6 --port COM6 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args`. Its arguments resolve to prepared bootloader at 0x0, prepared partition table at 0x8000, and prepared application at 0x10000. No whole-chip erase was performed; esptool erased the write ranges. Existing NVS was outside those ranges.

**All three artifact writes reported `Hash of data verified.` and esptool exited 0.** [Raw flash log (UTF-16)](./HOME_BOARD_WIFI_PS_NONE_flash.log), [flash result](./flash_result.json), [artifact hashes](./preflash_audit.json). Esptool logged an in-memory bootloader header/SHA update for flash parameters; the prepared input files remain unchanged.

Persistent ESP-IDF monitor uses the NEW prepared ELF. [Monitor command/process metadata](./monitor_session.json). Explicit controlled reset requested at **2026-11-03T23:06:05.634316+00:00**, with logging already active. Startup output received on initially opening the port is preserved separately before the `Command: 'reset'` marker and excluded from measurements. Flashing also caused downloader-entry and post-write hard resets. No later reset was requested.

The controlled startup prints ELF prefix `9b23e164f...`, matching the new ELF; only a prefix is printed, so full on-device digest comparison is not claimed. It confirms:

- `requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)` — explicit successful setter and API readback.
- `wifi:Set ps type: 0, coexist: 0`. Initial `pm start, type:1` precedes the application setter and is superseded by the confirmed type-0 readback before QUIC starts.
- QUIC connection established and MQTT connected over QUIC.
- Actual assigned IPv4 **192.168.137.212**, from this controlled startup, not assumed from a previous board.

[Startup checks](./startup_checks.json), [live serial log](./HOME_BOARD_WIFI_PS_NONE_serial.log). Startup gates were verified before accepting the collection; the immutable snapshot preserves its exact input.

## APP_RTT after 60000 ms boot uptime

Selected the first 10 fresh APP_RTT records in arrival order with ESP log uptime >=60000 ms from the controlled startup. No outliers removed. Host timestamps are Europe/Helsinki UTC+02:00 at second resolution; corresponding UTC is recorded in CSV.

| Sequence | ESP log uptime ms | APP_RTT ms |
|---:|---:|---:|
| 11 | 63663 | 85.430 |
| 12 | 68693 | 105.411 |
| 13 | 73623 | 25.479 |
| 14 | 78653 | 45.457 |
| 15 | 83683 | 65.457 |
| 16 | 88713 | 85.396 |
| 17 | 93743 | 104.645 |
| 18 | 98673 | 25.423 |
| 19 | 103703 | 45.496 |
| 20 | 108733 | 65.479 |

Mean **65.3673 ms**, min 25.423, max 105.411. Change versus fresh HOME_BOARD reference: **-10.0676 ms** (13.35% lower). Collection finished **2026-11-03T23:07:54.407221+00:00**.

[APP_RTT CSV](./HOME_BOARD_WIFI_PS_NONE_APP_RTT_20261103T230410Z.csv), [fixed raw serial snapshot through collection](./HOME_BOARD_WIFI_PS_NONE_serial_through_collection.log). APP_RTT is application publish-to-matched-echo latency; it includes transport/network and receive scheduling. Source timestamp/log references are lines 229, 526 and 194 of [experimental application snapshot](./experimental_application_source_snapshot.txt); setter/readback is at lines 585–594. It is distinct from ICMP RTT.

## Subsequent 30 pings

Command: `ping.exe -n 30 -w 1000 192.168.137.212`. Started **2026-11-03T23:07:54.407284+00:00**, after APP_RTT collection; finished **2026-11-03T23:08:23.721212+00:00**. Monitor and QUIC traffic continued.

**30 replies, 0 timeouts, 0 other failures** out of 30 requests. `<1 ms` observations: **0**; each retained literally in the CSV with numeric exact RTT blank. Reported integer RTT min 1.0, max 47.0 ms. Arithmetic mean of reported integer RTTs: **7.6333 ms**, change -261.2333 ms (97.16% lower) versus the fresh HOME_BOARD reference. All ping values/timeouts are retained.

Windows prints an approximate integer summary, preserved verbatim:

```text
Reply from 192.168.137.212: bytes=32 time=4ms TTL=64

Ping statistics for 192.168.137.212:
    Packets: Sent = 30, Received = 30, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 1ms, Maximum = 47ms, Average = 7ms
```

[Raw ping output](./HOME_BOARD_WIFI_PS_NONE_ping_raw.txt), [timestamped per-request CSV](./HOME_BOARD_WIFI_PS_NONE_ping_20261103T230410Z.csv), [full output with UTC timestamps](./HOME_BOARD_WIFI_PS_NONE_ping_output_timestamped.csv), [statistics](./HOME_BOARD_WIFI_PS_NONE_statistics.json).

## Comparison only with fresh HOME_BOARD reference

| Metric | Original/default HOME_BOARD | WIFI_PS_NONE HOME_BOARD |
|---|---:|---:|
| APP_RTT mean, 10 records | 75.4349 ms | 65.3673 ms |
| Ping mean, 30 requests | 268.8667 ms | 7.6333 ms |

[Fresh reference summary](../HOME_BOARD_PS_DEFAULT_20261103T225407Z/SUMMARY.md), [comparison CSV](./HOME_BOARD_default_vs_WIFI_PS_NONE_comparison.csv). No university-board measurements enter this comparison. The original reference has driver type-1 evidence plus inferred SDK default, without API readback; this experiment has explicit WIFI_PS_NONE API readback. This is one sequential pilot per setting; the observations alone do not establish a general causal effect or long-run distribution.

Clumsy was observed Stopped with the Start button and unchecked Lag before flashing; it was not started or reconfigured. Final process/socket/UI observations are saved alongside this summary. Server and persistent monitor are left running on the experimental firmware.
