# QUIC startup crash investigation (HBPSN-03, HBPSN-08) - NOTES

Started 2026-11-17. Branch: `crash-investigation` (created from `agents/backup-verification-and-creation`, no commit made).
Rules: frozen builds, 18-run data, run_register.csv and the frozen plan are not changed. No COM6 access, no flash, no reset, no build in Step A.

## Step log
1. `git checkout -b crash-investigation` (working tree carried over unchanged; no commit).
2. Read serial.raw.log of HBPSN-03 (attempt_20261105T202314Z) and HBPSN-08 (attempt_20261109T013410Z): panic text, registers, 1 KB stack dump.
3. Decoded stack words with `riscv32-esp-elf-addr2line` against `profiles/wifi_ps_none_20261103/build/quic_demo.elf` (sha256 prefix 9b23e164f8d6fd47, matches the "ELF file SHA256" in both panics) and ROM addresses against `esp32c6_rev0_rom.elf`.
4. Read earlier work: `results/diagnostics/HBPSN03_FIRST_CRASH_20261105T203406Z/ANALYSIS.md`, `results/diagnostics/TEST_ONLY_QUIC_HEAP_20261106T004758540Z/REPORT.md`, `profiles/test_only_heap_20261106/` (sdkconfig.diff, diagnostic_source.diff).
5. Read `ngtcp2.patch`, `wolfssl.patch`, `main/ngtcp2_sample.c` (locking, write path), `main/esp_ev_compat.c` (tasks, stack sizes), `sdkconfig` (heap poisoning, stack checks, core dump).
6. Counted panics in all `serial.raw.log` files of the study (script-free grep, read-only).

## Findings (Step A)
See the report given to the user in the session. Summary:
- Both crashes: Load access fault, MCAUSE 5, MEPC 0x40021c40 = ROM `tlsf_free+0x42`, RA 0x400225c4 = ROM `multi_heap_free_impl`, MTVAL = A5+4 (0x41847f0c / 0x41847f24).
- Stack chain: heap_caps_free -> free -> default_free -> ngtcp2_mem_free -> pktns_del (ngtcp2_conn.c:767) -> conn_discard_pktns (:2501) -> ngtcp2_conn_discard_initial_state (:2516) -> conn_write_handshake_pkts (:2766) -> conn_write_handshake (:9973) -> conn_client_write_handshake (:10197) -> ngtcp2_conn_write_vmsg (:11610) -> ngtcp2_conn_writev_stream (:11495) -> client_write_streams (main/ngtcp2_sample.c:563).
- The size word at (pktns - 4) reads as 0x01000000 (+flag bits) in both runs, so the free reads a "next block" 16 MiB away.
- Not reproduced in the one TEST_ONLY boot (no heap poisoning was enabled there).
- Formal first boots on the QUIC image 9b23e164f that got past startup: 9 (HBPSN-01, 03, 05, 08b, 10, 12, 13, 15, 17); 2 panicked (HBPSN-03, HBPSN-08b). HBPSN-08a produced no connection (39 lines) and is excluded.

## Status
Step A report delivered. Waiting for the user's OK before any build, flash or commit.

## Step 0 (no board): wolfSSL macro / struct-layout consistency check
Method: `compile_commands.json` of the frozen QUIC build (profiles/wifi_ps_none_20261103/build) was used read-only. For four translation units (wolfSSL library `wolfssl/src/quic.c`, `ngtcp2/crypto/wolfssl/wolfssl.c`, `ngtcp2/lib/ngtcp2_conn.c`, `main/ngtcp2_sample.c`) the exact compiler command was reused to compile `wolfssl_macro_check/probe.c` (outputs in the scratchpad, nothing in the build tree changed) and `nm -S` read sizeof() of key structs and which feature macros are defined. Files: `wolfssl_macro_check/probe.c`, `cc3.py`, `result_table.txt`.
Result:
- Both sides use `WOLFSSL_USER_SETTINGS` and the same `user_settings.h`. wolfssl/options.h is not needed.
- MISMATCH: `components/ngtcp2/CMakeLists.txt` adds PUBLIC defines (also reach `main`) that the wolfSSL library itself is NOT compiled with: HAVE_AESCCM, HAVE_AES_ECB, HAVE_CHACHA, HAVE_POLY1305, WOLFSSL_KEY_GEN, WOLFSSL_SNI, WOLFSSL_RAND, WOLFSSL_EVP_INCLUDED, WOLFSSL_HAVE_EVP_PKEY, WOLFSSL_EVP_AES, WOLFSSL_ADVANCED_EXTENSIONS.
- Real layout difference: sizeof(WOLFSSL_EVP_CIPHER_CTX) = 520 in the library, 524 in ngtcp2 and main units (extra `byte* key` when HAVE_CHACHA && HAVE_POLY1305). Aes 336, WC_RNG 16, EVP_MD_CTX 568, EVP_PKEY 88, HMAC_CTX 816, WOLFSSL_QUIC_METHOD 16 are equal.
- ngtcp2_crypto_wolfssl (wolfssl.c) only passes WOLFSSL_EVP_CIPHER_CTX pointers to wolfSSL APIs (allocated and freed by the library); it never allocates or dereferences the struct, so no overflow was found from this by reading the code. Not proven harmless, not proven the cause.
- Proposed fix (NOT applied): build both sides with one macro set, e.g. remove the extra feature `-D` lines from the ngtcp2 CMake and, where ngtcp2 needs a feature, enable it in user_settings.h so the library sees it too. Try in a separate diagnostic profile first.

## Step B - build (no board)  [2026-11-17]
- New profile folder: `profiles/crash_investigation_20261117/` (frozen profiles untouched). `make_profile.py` copies the frozen QUIC source set (1428 files, hash-verified against `profiles/tcp_tls_wifi_ps_none_20261104/source_before.json`, 0 mismatches), adds component `components/crash_diag` and applies the diagnostic edits; `build.py` builds. Changes listed in `changed_source_files.json`.
- Diagnostic config (sdkconfig): HEAP_POISONING_COMPREHENSIVE=y, COMPILER_STACK_CHECK_MODE_STRONG=y, FREERTOS_CHECK_STACKOVERFLOW_CANARY (already on), ESP_SYSTEM_USE_EH_FRAME=y (backtrace on panic). Factory partition 1700K -> 2560K (diagnostic image is larger). Core dump to UART was not enabled (too slow per crash for 30 cycles; EH_FRAME backtrace used instead).
- Code: `crash_diag_checkpoint()` (heap_caps_check_integrity_all at named points in ngtcp2 handshake/discard path and in client read/write), `crash_diag_heap()` (free / min free / largest block after Wi-Fi, after QUIC handshake, after MQTT), `crash_diag_stacks()` (stack high-water marks), cycle task with NVS counters (mode 1 reboot cycles, mode 2 soft reconnect cycles). Mode 2 calls ev_default_loop_init() once (the original re-runs it on every init, which memsets the live loop). Build banner: `DIAG BANNER DIAGNOSTIC_NOT_FOR_MEASUREMENT`.
- Build rb1 (mode 1, 30 cycles, checkpoints ON): exit 0, bin 1,947,888 B, sha256 f779904b8ba09abf7d6de1ce6d694c22cfe4214f6864f02b89ddcb260394c174.
- Build notes: idf.py refuses to run under Git Bash/MSys, builds were run from PowerShell; the component manager is off so components are referenced by directory name (wolfssl__wolfssl, esp-idf-lib__dht, espressif__cjson), as in the earlier TEST_ONLY profile.

## Correction from the user (2026-11-17)
- HBPSN-03 crashed under DROP1_OUT (1% outbound loss); HBPSN-08 crashed under LAG100_OUT (+100 ms outbound delay). The three CONTROL QUIC boots (HBPSN-01, 12, 15) did not crash. (Earlier text in this folder that treats both crashes as one condition is superseded by this.)
- Plan agreed: Phase 1 Clumsy OFF, image rb1 (reboot cycles, unfixed code, 30 cycles); Phase 2 (only if 0 crashes) Clumsy Lag 100 ms outbound on the UDP 14567 filter, 30 more reboot cycles; then 30 soft cycles; then a second image with the wolfSSL macro mismatch fixed, tested the same way. No commit. Monitor closed gracefully at the end.
- The user turned the hotspot on manually.

## Phase 1 result: image rb1, Clumsy OFF, 30 reboot cycles, unfixed code (2026-11-17 ~17:49-17:53Z)
Files: `phase1_rb1.log` (host-timestamped UART), `server_stdout.log`, `profiles/crash_investigation_20261117/flash_rb1.log` (flash: hash verified).
- 30 cycles started, 13 passed, 0 timeouts, **17 heap-integrity failures** (CORRUPT HEAP), all at the very first checkpoint `after_client_quic_init` (seq=1, no earlier checkpoint passed), with the same message: `CORRUPT HEAP: Bad tail at 0x4084xxxx. Expected 0xbaad5678 got 0x01000000` (tail addresses 0x408482f0..0x408492f8, mostly 0x40848280/0x40848308). Same value 0x01000000 as the size word seen at the original crashes (HBPSN-03/08).
- Meaning: a heap block's tail guard word was overwritten by 0x01000000 (a 4-byte overflow just past the end of a block) before or inside `client_quic_init` (socket, SSL_CTX/SSL setup, ngtcp2_conn_client_new). It happens in most boots; in the formal builds (no poisoning) this is silent until a later free reads the damaged neighbour header (the observed tlsf_free fault).
- Also 7 of the 13 passing cycles printed a task watchdog (`task_wdt`) backtrace: diagnostic overhead from the many integrity checks plus UART printing; not part of the original failures.
- Backtrace of the poison abort (checkpoint abort): 0x40809082 0x4080903e 0x42097576 0x4201383e 0x42013b88 0x42012454 0x42133b6e (decoding in the Phase 1 section below).
- Next: finer checkpoints inside client_init/client_ssl_init/client_quic_init (refine1.py) -> image rb2.

## Cause located (2026-11-17)
**ngtcp2 `conn_new()` (components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c ~1166-1199, 1415-1421) under-allocates by 4 bytes when `malloc` returns an address that is 4 mod 8.**
- `buflen_align()` rounds *offsets* to 8 (assumes an 8-byte aligned base). `buf_align()` rounds the *absolute address* to 8. For a client, `buflen = sizeof(ngtcp2_conn) (7640) + 4 = 7644`. If the calloc'd block starts at addr%8==4, `buf_align(buf + 7640)` moves up by 4 and `available_versions_init()` writes 4 bytes (version 1, big-endian = bytes 00 00 00 01, read as little-endian word 0x01000000) past the end of the 7644-byte block.
- ESP-IDF heap only guarantees 4-byte alignment, so this depends on where the block lands in the heap (it varies from boot to boot).
- Evidence: rb3 (30 reboot cycles, Clumsy off, poisoning + checkpoints + alignment print): 9/9 failures had the conn address %8==4 and the first failing checkpoint was `after_client_available_versions_init` (last pass `before_ngtcp2_conn_client_new`); 21/21 passes had %8==0. Poison message in every failure: `CORRUPT HEAP: Bad tail at 0x4084xxxx. Expected 0xbaad5678 got 0x01000000`.
- Without poisoning (formal builds) the 4 stray bytes land in the header (size word) of the next heap block. The next block is normally the Initial packet-number space (`pktns`, allocated right after the conn buffer in `conn_new`), so when it is freed at `ngtcp2_conn_discard_initial_state` TLSF reads a size of 0x01000000 (16 MiB) -> Load access fault in `tlsf_free` (MEPC 0x40021c40), exactly HBPSN-03/08 (A5-(A1-4)=0x01000000).
- Not the cause: the wolfSSL macro mismatch (see Step 0). rb5 (macro mismatch fixed, sizeof(WOLFSSL_EVP_CIPHER_CTX)=524 in all units): still 2/30 crashes, both at addr%8==4, same checkpoint.

## Test results (all with Clumsy OFF; hotspot on; QUIC server on UDP 14567; all images DIAGNOSTIC_NOT_FOR_MEASUREMENT)
| Run | Image (sha256 prefix) | Code | Mode | Cycles | Pass | Crash (heap corruption) | Other fail |
|---|---|---|---|---|---|---|---|
| Phase 1 | rb1 f779904b | unfixed | 30 reboot | 30 | 13 | 17 (first CP `after_client_quic_init`) | 0 |
| 1b | rb2 (finer CPs) | unfixed | 30 reboot | 30 | 5 | 25 (first CP `after_ngtcp2_conn_client_new`) | 0 (+1 boot with no cycle) |
| 1c | rb3 38d6ffbb | unfixed + alignment print | 30 reboot | 30 | 21 | 9 (`after_client_available_versions_init`; all addr%8==4) | 0 |
| Phase 3 | rb5 409e3901 | macro mismatch fixed | 30 reboot | 30 | 28 | 2 (same CP; addr%8==4) | 0 |
| Phase 4 | rb4 5791042e | alignment fix (+7 bytes) | 30 reboot | 30 | 30 | 0 (25 of 30 boots had addr%8==4) | 0 |
| Phase 5 | rs1 1da4db55 | unfixed | 30 soft reconnect | 30 | 16 | 7 (all addr%8==4) | 7 `client_init failed` (see below) |
| Phase 6 | rs2 0ff8ce71 | alignment fix | 30 soft reconnect | 30 | 10 | 0 (9 of 10 attempts had addr%8==4) | 20 `client_init failed` |
Phase 2 (Clumsy Lag 100 ms) was NOT needed: Phase 1 already reproduced the fault with Clumsy off.
- Soft-mode secondary finding (not the startup crash): `client_free()`/`quic_client_cleanup()` never closes the UDP socket (no `close(` in main/ngtcp2_sample.c) and `CONFIG_LWIP_MAX_SOCKETS=10`, so after about 10 reconnects `create_sock` fails (`client_init failed`). Production firmware does not reconnect, so formal runs are unaffected.
- Diagnostic artefact: task watchdog (`task_wdt`) backtraces appear in most diagnostic boots (many integrity checks + UART printing). They are not in the formal builds.
- Proposed fix (not applied to any frozen file): `PROPOSED_FIX_ngtcp2_conn_alignment.diff` (allocate `buflen + 0x7`). Alternative: make the allocator return 8-byte aligned memory for this call.
- Board state: it is left running the diagnostic image rs2 (idle after DIAG COMPLETE), NOT a formal build. The QUIC server I started (python quic_server.py, wrapper PID 5128) is still running; logs: results/diagnostics/quic_crash_20261117/server_stdout.log and logs/sensor_20261117T174754_788763Z_*.csv. Serial capture processes were closed by their own exit (port released) after each run.
- Nothing committed. Branch: crash-investigation.

## 2026-11-18 follow-up (user instructions: commit, upstream check, fixed profile)

### Step 1 - commit and push
- Scanned all files to be committed for the Wi-Fi SSID and password (values read from root sdkconfig, never printed).
  Hits were found in profile sdkconfig copies, build logs and the serial capture logs (SSID). They were masked
  in place (SSID_MASKED / WIFI_PASSWORD_MASKED); unmasked originals saved in backups/local_uncommitted/crash_investigation_unmasked/ (git-ignored).
- Re-scan of the staged files: 0 hits. Not committed: build_* directories (2.2 GB), copied source tree (only the 8 changed files + crash_diag component),
  src/sdkconfig (real credentials), README backups, the server csv.
- Commit df2052026 on branch crash-investigation, pushed to remote thesis only.

### Step 2 - upstream ngtcp2
- Newest upstream release found: v1.26.0 (2 Nov 2026). Upstream PR #2400 "Fix heap overruns when malloc is only 4-byte aligned (like on ESP32)"
  (merged 1 Nov 2026 into main, milestone v1.26.0) adds `buflen += 0x7U` before the calloc in conn_new() (same fix as ours) and
  makes ngtcp2_balloc_get() reserve 0xf instead of 0x8 bytes. Source: web summary of upstream main + PR page (not re-verified by building upstream).
- Our vendored copy (older) has both bugs: conn_new without padding, and ngtcp2_balloc_get with 0x8u reserve but 0xfu alignment.
  Both are fixed in profiles/fixed_20261118.

### Step 3 - fixed profile profiles/fixed_20261118 (built, NOT committed, NOT used for measurements yet)
- Source = frozen QUIC/TCP_TLS source set (1428 files hash-verified, 0 mismatches) + changes in 8 files (changed_source_files.json):
  ngtcp2_conn.c +7 bytes in conn_new; ngtcp2_balloc.c reserve 0xf (same cause, fixed upstream too); ngtcp2_sample.c UDP socket closed in client_free()
  and on the 3 client_init failure paths; build-system tweaks (component manager off, same approach as earlier profiles); test harness compiled only with FIXED_TEST_MODE=1|2.
- TCP+TLS client: tcp_tls_client_cleanup() already closes the socket (close(client.fd)) - no change needed.
- sdkconfig identical to frozen one: no heap poisoning, no stack check, 1,700K partition. QUIET_MEASUREMENT=1.
- Images (exit 0): fq QUIC measurement 1,637,328 B sha256 d77192f6e48b...; ft TCP_TLS measurement 1,498,864 B b591e17c9c4d...;
  tb QUIC + reboot test harness 1,608,832 B b78511a0fe2f...; ts QUIC + soft test harness 1,609,472 B 70515a73017c...
- Note: ev_default_loop_init() is still re-run on every quic_client_init (leaks event loop task); the soft test harness calls it once. Not part of this fix; production never reconnects.

### Step 4 - verification (Clumsy OFF, normal network)
- tb, 30 reboot cycles: started 30, passed 30, failed 0, init_failed 0, crashed 0 (fixed_tb_reboot30.log).
- ts, 30 soft reconnects: started 30, passed 30, failed 0, init_failed 0, crashed 0; socket fd 54 in all 30 cycles; free heap 226 KB (cycle 10) -> 225 KB (cycle 30) (fixed_ts_soft30.log).
- Board now holds image ts (test harness, not a measurement image).

### Step 5
- QUIC server (PIDs 5128, 37500) stopped; UDP 14567 free. Serial ports closed by capture scripts. No timing measurements started.

## 2026-11-18/19 follow-up: connection-time test and 12 h runs (fixed profile)
- Connection-time test (50 attempts each, 0 failures): `results/experiments/CONNECTION_TIME_20261118/`. QUIC event-loop re-init leak fixed (init once) in the fixed profile (`patch_ct.py`).
- 12 h runs: `results/experiments/LONG_RUN_12H_20261118/` (`COMPARISON.md`, `tcp_tls/`, `quic/`). Neither run stayed healthy for 12 h: TCP+TLS stalled at 10.0 h (board-to-server direction stopped; board did not crash), QUIC at 11.53 h (server-to-board direction stopped: partial MQTT packet, then keepalive timeout; board kept publishing). 0 crashes/reboots in both. Causes not determined; see the STALL_ANALYSIS.md files.
- Source in the repo for the fixed profile: only the changed files and scripts are committed; the rest of `src/` is a verbatim copy of the frozen profile and is reproduced by `make_profile.py` plus `patch_ct.py`.
