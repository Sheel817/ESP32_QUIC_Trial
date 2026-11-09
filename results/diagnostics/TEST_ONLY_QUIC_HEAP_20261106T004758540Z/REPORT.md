# TEST_ONLY single diagnostic boot — NOT_REPRODUCED

The fault did not reproduce in this one instrumented 180-second boot. This does not establish a fix. No source edit, rebuild, Clumsy change, formal-run/register update, manual retry or firmware restoration was performed.

## Preflight and image identity

[Preflight](./preflight.json) confirmed HBPSN-03 FINALIZED / FAILED_STARTUP, no active formal collection, HOME_BOARD on COM6 (MAC40:4c:ca:56:bb:b0, ESP32-C6 rev0.0,8MB), hotspot ON with host192.168.137.1, and the existing project QUIC server PID23100 on UDP14567. Only the verified obsolete post-finalization COM6 monitor was closed gracefully through its existing control channel. Its historical raw recordings were preserved.

The actual [Clumsy image](./TEST_ONLY_Clumsy_PRE_FLASH.jpg) was captured2026-11-06T00:47:58.540Z–00:47:59.499Z. SHA-256 `f7caed5b0614e995a1c67cd66441e78afa4799822e60ee64a9a6d62b3a989972`. Visible settings passed: exact `udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)`; capture running; only Drop enabled, Chance1.0%, Outbound checked, Inbound unchecked. Lag, Throttle, Duplicate, Out of order, Tamper, Set TCP RST and Bandwidth disabled. No settings were changed by this procedure. Host activity: Chrome Remote Desktop operator-reported; not a formal timing experiment.

Preserved diagnostic [BIN](../../../profiles/test_only_heap_20261106/build/quic_demo.bin),1,652,336bytes, SHA-256 `6dd666d50640e1a79775d79bb83f43acdc3420582822e67026cb6cb8653301cb`.

Matching [ELF](../../../profiles/test_only_heap_20261106/build/quic_demo.elf),17,418,112bytes, SHA-256 `a8056d24f2e746d5f345b16e545e907f3339e6e87ea146895b57b1aaa7d32b70`.

Bootloader, partition, BIN, ELF and flash-argument hashes matched the preserved build report. [Flash log](./flash.log) contains three successful written-data hash verifications; [flash result](./flash_result.json) records exit0. Matching image offsets/settings were used. The reset policy was explicitly overridden to before=no-reset/after=no-reset after identification entered ROM, avoiding an unrecorded application boot. Exact commands are in [identification metadata](./identification.json) and [flash metadata](./flash_started.json). Identification reset entered only the ROM loader; the single application reset release follows below.

## Controlled startup and fixed window

Raw capture was active while EN was held low, before its single release. The [serial-open record](./serial_open.json) documents driver buffer clearing at open while EN was held low, with no post-open flush. Reset release host anchor: **2026-11-06T00:52:21.973632Z**, Helsinki **02:52:21.973632**. Fixed deadline: **00:55:21.973632Z**, Helsinki **02:55:21.973632**,6November2026.

[Raw UART](./TEST_ONLY_uart.raw.log) starts with the first ESP-ROM startup, POWERON reset reason, TEST_ONLY banner and ELF digest prefix `a8056d24f`. Assigned IP192.168.137.112. Explicit requested/returned WIFI_PS_NONE(0) at ESP4582ms. QUIC connected at7382ms, MQTT over QUIC at8422ms. TLS1.3, TLS_AES_128_GCM_SHA256, suite0x1301, ALPN mqtt; certificate_verification=NONE(mode0), retained as reported.

One application boot observed, zero automatic reboots. No panic, corruption, heap-check failure or core-dump markers.34 APP_RTT echoes, sequences1–34, ESP13562–178872ms, no sequence gaps. All retained in [RTT observations](./TEST_ONLY_rtt_observations.json). Wi-Fi warning lines are retained verbatim in [analysis](./TEST_ONLY_ANALYSIS.json); no serial E-level errors were observed. Server stderr snapshot is empty. Server stdout contains DHT11 publications, including the34 associated sequences.

[Deadline decision](./deadline_decision.json): no active core dump, so no120-second recovery extension. [Completion](./CAPTURE_COMPLETE.json) was processed at00:55:22.023046Z,180.0495seconds after the host reset anchor. The polling delay is49.5ms; [byte receipts](./TEST_ONLY_uart_receipts.jsonl) preserve exact host receipt boundaries, and subsequent UART is isolated in [after-capture output](./TEST_ONLY_after_capture.raw.log). No later RTT belongs to the diagnostic observation. Raw file10,993bytes, SHA-256 `98a0e269b7aca09ba4ea2dce84944bc289584e02b1781fdbb00215068c560b52`.

## Recovery and limitations

No panic/core dump was generated, so no panic decoding or core-based RAM recovery was possible or necessary. No live RAM readback was attempted. Passing checkpoints are stored in the RAM ring and are not printed during normal operation; therefore the last passing checkpoint and individual trace events cannot be established from this UART record. No first failing checkpoint was observed. The diagnostic instrumentation perturbs timing; this brief boot does not validate allocator ownership or synchronization and does not establish the defect fixed.

The [server stdout snapshot](./TEST_ONLY_server_stdout.snapshot.log) and [stderr snapshot](./TEST_ONLY_server_stderr.snapshot.log) retain actual start offsets and analysis-time end offsets in the analysis metadata. They include some post-deadline activity and are supplementary evidence, not an extension of the observation. Serial receipt times and reset API return are host anchors, not physical-edge measurements.

## Preservation and remaining board state

[Protection verification](./protection_after.json) confirms all1,701 snapshotted formal source/evidence/plan/register files unchanged. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags and HBPSN-03 FAILED_STARTUP were preserved. Diagnostic inputs also matched after flash. Original logs and historical crash evidence were not modified.

**The TEST_ONLY diagnostic QUIC WIFI_PS_NONE firmware remains on HOME_BOARD.** No automatic restoration occurred. The persistent raw logger PID32104 remains open on COM6 with later bytes directed separately; the project server remains running. Clumsy was left unchanged.

Supporting scripts: [single-boot host procedure](./run_host_capture.py), [offline analysis](./analyze_capture.py). [SHA-256 manifest](./SHA256SUMS.json) covers stable deliverables; explicitly live outputs are excluded.
