# HBPSN-04 TCP_TLS CONTROL — preflight blocked, NOT_RUN

No flash, reset, formal timer, recording or monitor handover was started. Both registers retain HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with flags, HBPSN-03 FAILED_STARTUP and HBPSN-04 NOT_RUN. The QUIC crash remains unresolved.

## Server repair attempt

Verified PID 26228 was the project tcp_tls_server.py in the existing .quic-venv, without a confirmed listener. Preserved the original logs and separate [stdout](./previous_server.stdout.snapshot.log) / [stderr](./previous_server.stderr.snapshot.log) snapshots with [hashes](./previous_server_snapshot_hashes.json). Stopped only verified PID 26228. No unrelated process/listener was stopped.

Launched the unchanged project server once using the existing .quic-venv. [Launch metadata](./server_launch.json): launcher PID 18676, actual Python PID 36536. Fresh [stdout](./tcp_tls_server.stdout.log) printed `READY | TCP+TLS port 14568 | ALPN=mqtt`; [stderr](./tcp_tls_server.stderr.log) was empty. Nevertheless repeated Windows queries did not confirm LISTENING. Raw CIM displayed State 0, its JSON serialization showed null, and netstat contained no 14568 listener. READY alone does not satisfy the required check. Cause is unknown. No second relaunch or connection probe was attempted. The new server remains running for inspection.

[System evidence](./system_after_relaunch.json), actual UTC 2026-11-06T01:37:35.6642815Z, records hotspot ON, 2.4 GHz, SSID SHEEL 3460 and host 192.168.137.1. COM6 CP210x enumeration matches the previous HOME_BOARD device. No serial connection was opened.

## Actual Clumsy evidence

[Screenshot](./HBPSN-04_Clumsy_PRE_FLASH.jpg) captured 2026-11-06T01:35:40.465Z–01:35:40.851Z. SHA-256 `a82c62bf8f5c9843852826e2b12e8e4d03db3627d922d7ebdcdc9373ef270396`.

Exact filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture running, all eight main effects disabled: Lag, Drop, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth. Inactive Lag100ms/Drop1% values and direction boxes retain their saved values; enable boxes are off. No settings changed. [Actual observation](./clumsy_pre_flash.json).

## Firmware and preservation

The formal TCP_TLS profile's BIN, ELF, bootloader, partition table, flash_args and flasher_args.json match preserved validation hashes; firmware images match the frozen manifest. TEST_ONLY image excluded. [Full audit](./PREFLIGHT_BLOCKED.json) contains current hashes and both-register verification.

The TEST_ONLY firmware remains on HOME_BOARD and its identified logger remains open, because preflight stopped before board access. All 26 stable diagnostic deliverables still match their saved hashes. Both formal registers retain their previous hashes. Original server logs were preserved; new server logs are separate.

## Remaining gates

A future start needs a confirmed TCP14568 LISTENING socket owned by the verified project process, repeat final preflight checks and fresh actual pre-reset settings evidence, controlled logger handover, formal flash verification and then the frozen controlled startup. No replacement or reordered run was created. Positive validity requires actual post-recording image and operator stability review.
