# HBPSN-07 TCP_TLS DROP1_OUT (Replicate 2) - Audit Review

Original recording completed for the fixed 2,220-second window:
- **Start**: 2026-11-07 05:09:19.159995 Helsinki (03:09:19.159995 UTC)
- **Deadline**: 2026-11-07 05:46:19.159995 Helsinki (03:46:19.159995 UTC)
- **Monotonic duration**: exactly 2,220 seconds (775268.4760111 to 777488.4760111)

## 1. Startup Log Verification
- **Board identity**: HOME_BOARD (MAC `40:4c:ca:56:bb:b0`, COM6)
- **Assigned IP**: `192.168.137.112`
- **Firmware ELF Prefix**: `1f661a4f7` (matches preserved TCP_TLS WIFI_PS_NONE build `1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6`)
- **Wi-Fi Power Save Readback**: `requested=WIFI_PS_NONE(0), returned=WIFI_PS_NONE(0)`
- **Socket Options**: `TCP_NODELAY=1; connect/I/O timeout=5000 ms`
- **TLS Parameters**: `TLS=TLSv1.3`, cipher=`TLS_AES_128_GCM_SHA256`, suite=`0x1301`, ALPN=`mqtt`, cert_mode=`NONE (0)`
- **MQTT**: `MQTT connected over TCP_TLS`

## 2. Sample Selection and Summary Metrics
- **Raw RTT count**: 441
- **Warmup excluded (< 60,000 ms ESP uptime)**: 10 records (seq 1 to 10)
- **Eligible count (>= 60,000 ms ESP uptime)**: 431 records
- **Selected first-415**: 415 records (seq 11 to 425; ESP uptime 62,357 ms to 2,136,477 ms)
- **Extra eligible records**: 16 records (seq 426 to 441)
- **Shortfall**: 0

| Metric | Computed Value | Frozen Plan Rule |
|---|---|---|
| Count | 415 | First 415 eligible records in source arrival order |
| Mean | 77.053949 ms | Arithmetic mean of 415 records |
| Sample SD | 65.569142 ms | Sample standard deviation (N-1) |
| Population SD | 65.490095 ms | Population standard deviation (N) |
| Minimum | 26.986 ms | Minimum APP_RTT observed |
| Median | 67.436 ms | Median APP_RTT |
| Nearest-rank P95 | 107.940 ms | Rank ceil(0.95 * 415) = rank 395 |
| Maximum | 627.760 ms | Maximum APP_RTT observed |

## 3. Diagnostics and Preserved Ledger
- **Resets**: Exactly 1 initial designated reset (at line 2); zero subsequent reboots.
- **Serial Connection Errors**: 0
- **Sequence Gaps**: 0
- **Wi-Fi Warnings**: 3 warnings retained verbatim (WPA2 password length, 2G phymode trace, ba-add).
- **Server Errors**: 1 new unattributed server error `TCP+TLS ERROR: ` at 2026-11-07 05:10:14.826668 Helsinki (03:10:14.826668 UTC), source bytes 211-228. Retained under the original non-reboot error rule.

## 4. Clumsy Settings and Validity Status
- **Pre-reset Clumsy image**: [clumsy_actual_pre_reset.jpg](../clumsy_actual_pre_reset.jpg), captured 2026-11-07 05:09:00.897-05:09:01.272 Helsinki, SHA-256 `f677ee483e9a0d1116e29c7cfa7d9bd07ca646ca6078c625cf905a2150b1d72a`. Shows filter `tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568)`, capture Running, Drop 1.0% outbound only, all other effects off.
- **Post-deadline screenshot**: Automatic capture timed out at finalization; agent subshell attempt returned `ERROR_INVALID_HANDLE` (6) due to headless/detached desktop DC.
- **Validity**: **NOT_APPROVED (PENDING OPERATOR CONFIRMATION & POST-SCREENSHOT)**.
- **Registers**: Both registers retain HBPSN-07 row status `RUNNING`; no completed runs or registers modified.
