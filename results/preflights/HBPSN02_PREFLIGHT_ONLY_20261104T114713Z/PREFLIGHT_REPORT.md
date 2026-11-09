# HBPSN-02 preflight only

Prepared UTC: 2026-11-04T11:48:52.777373+00:00. Run HBPSN-02, HOME_BOARD, WIFI_PS_NONE, TCP_TLS, LAG100_OUT, order 2 / block 1 / replicate 1. Register stays **NOT_RUN**; no formal attempt or recording has started.

**Readiness: preserved image PASS; existing server PASS; Clumsy settings NOT READY for HBPSN-02. Execution remains on hold.** No flash/reset/build, Clumsy settings change, serial monitor closure, server restart or formal recording occurred. The existing board/monitor is not claimed to be loaded with the TCP_TLS profile by this preflight.

## Exact frozen settings

The [unchanged frozen plan](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md), lines 23 and 28, specifies:

> TCP_TLS filter: `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`.

| Condition ID | Capture | Lag | Drop | Direction | Other effects |
|---|---|---|---|---|---|
| LAG100_OUT | Running | Configured 100 ms | Off | Outbound only, inbound unchecked | All off |

Operational checkbox mapping: **Lag checked**, Delay **100 ms**, **Inbound unchecked**, **Outbound checked**. The plan's exact phrase “All off” means every other main effect is disabled: **Drop unchecked, Throttle unchecked, Duplicate unchecked, Out of order unchecked, Tamper unchecked, Set TCP RST unchecked, Bandwidth unchecked**. Capture remains running. Disabled effects' displayed numeric values are not an instruction to enable them or modify them now.

The actual [preflight-only screenshot](./clumsy_preflight_only.png), acquired 2026-11-04T11:44:48.674Z–2026-11-04T11:44:49.137Z, shows **QUIC UDP 14567 filter**, capture running, **Lag unchecked**, displayed 100 ms/outbound-only, and all other main effects unchecked. Therefore filter and Lag-enable state differ from HBPSN-02. This mismatch is reported rather than changed. Screenshot SHA-256 `931061d4a531a80389e426c2c3e0ac644986b325f9b1f157cbe16aceb7465ebd`. It is not the future measured-reset screenshot and cannot serve as HBPSN-01 original post-run evidence.

## Preserved TCP_TLS profile verification

Profile: [tcp_tls_wifi_ps_none_20261104](../../../profiles/tcp_tls_wifi_ps_none_20261104/README.md). All four firmware artifacts match the frozen manifest, and both flash-argument files match the build report. CMakeCache records DEMO_TRANSPORT=TCP_TLS and DEMO_WIFI_PS_NONE=ON. Effective sdkconfig JSON matches preserved QUIC PS_NONE. No build/dependency change was made. Full [verification](./image_verification.json).

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| quic_demo.bin | 1498864 | `ff97eb5d20c9c47375539395f9cf23c1d0780381562cf511094d4b525ab17de8` |
| quic_demo.elf | 16790856 | `1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6` |
| bootloader.bin | 22096 | `726bb68a523511c6e08904ab50d6d19455cc940a16b58f989ac3446bd2c627e1` |
| partition-table.bin | 3072 | `8bc8d437a36b46e0880f7cbebe470527e27e4d454b536fff6633ac5f30539f16` |

Matching flash arguments remain --flash-mode dio --flash-freq 80m --flash-size 8MB; bootloader at 0x0, partition table at 0x8000, application at 0x10000. They were inspected, not executed. Original build report link/partition/integrity checks PASS; current hashes prove these are the same preserved outputs, not a rebuild. Startup WIFI_PS_NONE API readback, assigned IP, TCP_TLS/MQTT, TLS_AES_128_GCM_SHA256/ALPN mqtt and TCP_NODELAY=1 remain future measured-startup checks.

## Existing server readiness

Existing TCP endpoint 0.0.0.0:14568 belongs to PID 26228, child of .quic-venv launcher PID 36520. Command is this project's .quic-venv/Scripts/python.exe -u tcp_tls_server.py. No process was restarted or stopped. Server/imported QUIC module/certificate/dependency-lock hashes match the preserved source manifest. Certificate/key context loads locally, with TLS 1.3 only and AES-128-GCM available.

Passive Windows endpoint state queries were inconsistent, so a single **local TLS-only preflight probe** at 2026-11-04T11:47:18.151137+00:00–2026-11-04T11:47:18.203995+00:00 verified current TLS 1.3, ALPN mqtt and matching certificate at 127.0.0.1:14568. It sent no MQTT publication and did not involve the board. This Python client negotiated TLS_AES_256_GCM_SHA384; that client-specific probe is not the formal ESP TLS/cipher check. The measured ESP startup must still report the frozen AES-128-GCM cipher. Full [server evidence](./server_readiness.json).

## Fresh server boundaries and old errors

After the local preflight connection closed, EOF boundaries were captured at **11:47:18.454418–11:47:18.511997 UTC**:

| Source | Next byte offset | Prefix lines |
|---|---:|---:|
| Server stdout | 61377 | 721 |
| Server stderr | 51 | 3 |
| Server sensor CSV | 32663 | 355 |

Exact source paths, timestamps and prefix hashes are in [boundary metadata](./server_log_boundaries.json). Existing bytes [0, offset) are preserved in the three prefix snapshots. Stdout's local TLS-only probe lies in the excluded historical/preflight prefix: bytes [61280, 61377). Stderr's three bare TCP+TLS ERROR lines are all before byte 51 and remain explicitly **historical/unattributed**, not HBPSN-02 errors. Their contents lack timestamp/peer/connection IDs, so no retrospective boot attribution is invented. [Historical error ledger](./historical_tcp_error_ledger.json).

These are fresh **preflight boundaries**, not a future recording start. At a later separately authorized measured reset, recheck process/log identity and take new source EOF offsets atomically with the run's reset-release anchor, then receipt-timestamp only newly appended bytes into new per-run logs for the fixed interval. Exclude everything before those later offsets, including any intervening traffic. Do not reuse these older offsets as the actual run boundary. If a future bare error appears after the later boundary, record its receipt and flag session attribution limits instead of assigning an unidentifiable peer. This requires no server logic change now.

## Evidence and validity hold

A fresh actual **pre-reset screenshot will be saved and reviewed before any later authorized measured reset**, with actual acquisition UTC, image SHA-256, run ID and the actual TCP filter/effect states. The recorder's pre-run evidence gate blocks if that evidence is missing or mismatched. Today's preflight screenshot is not substituted. No screenshot is backdated.

After a future fixed recording ends, capture the actual GUI **before any settings changes** and save actual UTC/hash. Obtain the operator's explicit confirmation of unchanged filter/capture/effect settings throughout recording and until that screenshot. Review both screenshots, their ordering and operator statement together with startup/errors/deviations. Automatic deadline processing/finalization remains enabled, but local validity stays **NOT_APPROVED / PENDING_EVIDENCE_REVIEW** until that review. A machine screenshot PASS is insufficient. A separate active read-only screenshot observer is required; unattended 37-minute observer lifetime is not yet demonstrated. [Manual checklist](../../reviews/HBPSN01_20261104T112740Z/MANUAL_EVIDENCE_CHECKLIST.md).

HBPSN-01 remains FAILED_SETTINGS, with its original measured attempt and review note untouched. The plan, both registers, frozen order and 73 protected files passed hash preservation checks. HBPSN-02 remains the second scheduled session and NOT_RUN; no replacement was assigned.
