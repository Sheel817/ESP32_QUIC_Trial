# HOME_BOARD — original/default-power-saving firmware, Clumsy stopped

Home ESP32-C6, base MAC 40:4c:ca:56:bb:b0, COM6, DHT11 DATA=GPIO4 / VCC=3V3 / GND=GND (operator wiring). No build, flash, firmware source change, or Clumsy start was performed.

## Startup and firmware identity

Persistent ESP-IDF monitor is using the ORIGINAL [ELF](../../../build/quic_demo.elf), not the experimental profile. Its command, process IDs and reset timestamp are in [monitor_session.json](./monitor_session.json). Monitor PID 14776; wrapper PID 36356. The wrapper keeps stdin open; an `exit` line in `monitor_control.txt` in this directory requests graceful shutdown if later desired. It was not requested in this run.

Logging was active before the controlled RTS reset at 2026-11-03T22:54:30.076456Z (2026-11-04 00:54:30 +02:00). An initial partial startup was also observed when opening COM6 despite `--no-reset`; it is retained in the raw log and excluded. Only the startup after the explicit `Command: 'reset'` marker supplies measurements. Its ROM reports `rst:0x1 (POWERON)` and normal SPI flash boot. No additional reset was requested.

The controlled startup reports `Starting ESP32-C6 DHT11 over QUIC`, a QUIC handshake, and MQTT connected over QUIC. Reported ELF digest is the truncated prefix `4d62aef77...`, matching the original ELF. The full local ELF SHA-256 is `4d62aef77a0d99d020416535822b3dc128a4404a54021cc4c69636e3b850845d`; original BIN SHA-256 is `9fa08b1992f666747739799905aeffd9b79317607041e3c29446fae48c929323`. Both match the preserved checkpoint [hash manifest copy](./preserved_original_build_hashes.json). The original BIN application descriptor also embeds that full ELF hash: [esptool image information](./HOME_BOARD_PS_DEFAULT_original_image_info.txt). The running firmware prints only a prefix, so a full on-device digest comparison is not claimed. Identity was checked before accepting reference data.

## Network and power-management evidence

Actual assigned IPv4 **192.168.137.212**, mask 255.255.255.0, gateway 192.168.137.1, confirmed by the controlled startup's DHCP/IPv4 event. Server target is 192.168.137.1:14567. This address was read from this board, not inherited from university measurements.

- Driver evidence at uptime 3323 ms: `wifi:pm start, type: 1, twt_start:0` and `wifi:pm start, type:1`.
- Beacon interval 102400 us, DTIM period 1; driver logs listen interval 3 / 307200 us.
- Installed ESP-IDF v6.1 header identifies the default as `WIFI_PS_MIN_MODEM`: [API excerpt](./esp_wifi_power_api_excerpt.txt). Enum order maps NONE=0 and MIN_MODEM=1: [enum excerpt](./esp_wifi_power_enum_excerpt.txt).
- Thus default MIN_MODEM is inferred from the preserved original firmware and SDK default, supported by the driver's explicit type-1 startup log. **No explicit `esp_wifi_get_ps()` API readback exists in this run.** The original source snapshot has no experimental setter/readback block. No experimental mode log was observed.
- Clumsy UI was observed with Start button, unchecked Lag, and status `Stopped. To begin again, edit criteria and click Start.` before startup and again around the end of ping collection. The process remains open but impairment is stopped: [observation](./HOME_BOARD_Clumsy_stopped_observation.json). No Clumsy settings were changed.

## Application RTT reference

The first 10 fresh APP_RTT records with ESP log uptime at least 60000 ms from the controlled startup were retained in arrival order, including every high/low value. Sequences 11–20 are consecutive. Host log timestamps are local Europe/Helsinki, UTC+02:00, second resolution; CSV adds corresponding UTC timestamps. The selection uses ESP uptime rather than host elapsed time.

| Sequence | ESP log uptime ms | APP_RTT ms |
|---:|---:|---:|
| 11 | 63413 | 85.493 |
| 12 | 68443 | 105.455 |
| 13 | 73373 | 25.358 |
| 14 | 78503 | 145.301 |
| 15 | 83433 | 65.392 |
| 16 | 88463 | 85.612 |
| 17 | 93493 | 105.234 |
| 18 | 98423 | 25.169 |
| 19 | 103453 | 45.144 |
| 20 | 108483 | 66.191 |

Mean **75.4349 ms**, minimum 25.169 ms, maximum 145.301 ms. Collection completed 2026-11-03T22:56:18.920711Z.

[Application CSV](./HOME_BOARD_PS_DEFAULT_APP_RTT_20261103T225407Z.csv), [fixed serial snapshot through collection](./HOME_BOARD_PS_DEFAULT_serial_through_collection.log), [continuously growing raw monitor log](./HOME_BOARD_PS_DEFAULT_serial.log).

APP_RTT measures application publish-to-matched-echo latency, including transport/network and application receive scheduling. Original source references: receive timestamp at line 228, send timestamp immediately before MQTT_Publish at line 525, and RTT computation/log at lines 191–193 in [preserved original source](./preserved_original_quic_demo_main.c.txt). It is not an ICMP or pure wire RTT.

## Sequential ping reference

After application collection completed, ran `ping.exe -n 30 -w 1000 192.168.137.212`. Started 2026-11-03T22:56:18.920770Z; finished 22:56:48.528837Z. The monitor and QUIC traffic continued during ping.

**30 sent, 30 replies, 0 timeouts, 0 other failures, 0% loss.** Reported RTT minimum 22 ms, maximum 519 ms, arithmetic mean of the 30 reported integer RTTs **268.8667 ms**. Windows' own approximate summary reports average 268 ms. These are integer-resolution reported values. No `<1 ms` replies occurred; the CSV retains reported text and would leave an exact numeric value blank for such replies.

[Raw ping output](./HOME_BOARD_PS_DEFAULT_ping_raw.txt), [per-request timestamped CSV](./HOME_BOARD_PS_DEFAULT_ping_20261103T225407Z.csv), [timestamped full ping output](./HOME_BOARD_PS_DEFAULT_ping_output_timestamped.csv), [statistics JSON](./HOME_BOARD_PS_DEFAULT_statistics.json).

## Sources and final state

[Source references and hashes](./source_references.json) identify the preservation archive, original build metadata, and SDK headers. The original main/CMake snapshots were extracted from the preservation archive into this results directory, without editing project source. [Original CMake snapshot](./preserved_original_CMakeLists.txt.txt) defines the QUIC/TCP_TLS selector; the original build cache selects QUIC and compile metadata contains DEMO_TRANSPORT_TCP_TLS=0. The currently edited experimental project source is not used as the original firmware reference.

Final checks found monitor PID 14776 and wrapper PID 36356 alive, fresh serial APP_RTT records continuing, and server PID 23100 still bound to 0.0.0.0:14567 UDP. Clumsy remained stopped. Original firmware remains on the HOME_BOARD.
