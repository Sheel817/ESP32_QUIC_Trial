# TEST_ONLY QUIC heap diagnostic ? built, not flashed

Build/link, application/bootloader partition checks and offline recovery validation **PASS**. Protected formal files **PASS: 10,271 unchanged**, no changed/missing entries. No board connection, flash, reset, Clumsy change, formal run or register update was performed. HBPSN-01 FAILED_SETTINGS, HBPSN-02 COMPLETE with retained flags, HBPSN-03 FAILED_STARTUP remain intact.

## Exact baseline and isolation

All1,428 files matched the preserved [baseline manifest](./baseline_source_manifest.json) before copying. It identifies the validated modified source corresponding to HBPSN-03, not merely Git HEAD. Original QUIC ELF SHA2569b23e164f8d6fd4702450b687c76ef3fa8ced802945dc23dd2f4d102c35c0f3d. [Private source tree](./src/) contains real copies of main/components/managed dependencies, with its own [build](./build/) and [sdkconfig](./sdkconfig). No source/dependency junctions point to the formal project. Existing SDK remains a read-only shared input.

[Exact source diff](./diagnostic_source.diff), [per-file hashes](./changed_source_files.json), [raw config diff](./sdkconfig.diff), [effective config differences](./effective_configuration_diff.json). `git apply --check` against the unchanged formal baseline passed; the patch was NOT applied there. All unmodified dependency source stays at recorded versions. The dependency manager is disabled for this private build so no versions can be resolved/upgraded. Private CMake names explicitly replace manager aliases and inject the same DHT/cJSON dependencies; the private DHT CMake dependency name changes only. Project version gets the TEST_ONLY suffix.

## Instrumentation only

1. [Before stream packet writing](./src/main/ngtcp2_sample.c): whole-heap integrity check immediately before ngtcp2_conn_writev_stream, inside the existing mutex scope.
2. [Packet-space discard entry](./src/components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c): integrity check in conn_discard_pktns before native crypto-context destruction and nested cleanup.
3. [Before final object free](./src/components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c): integrity check after pktns_free and immediately before ngtcp2_mem_free(pktns).

[Trace implementation](./src/components/test_only_heap_diag/test_only_heap_diag.c) and [schema](./src/components/test_only_heap_diag/include/test_only_heap_diag.h): preallocated256-entry RAM ring,36 bytes/entry,9,216 bytes plus24-byte control. It records phases, CPU cycles, task handle, relevant pointers, allocation sizes/counts and free/realloc events. ngtcp2 memory-wrapper events preserve real allocation/free calls and original ownership/order. Packet-space allocation events identify packet-space ID. These are NOT global SDK/wolfSSL allocation hooks. Earlier records can be overwritten; busy/incomplete entries and drops are reported rather than fabricated. Sequence/cycle wrap remains a limitation for very long captures; the proposed observation is one120-second boot.

Producer hooks use word atomics, a single try-once slot reservation, fixed stores and current-task/cycle readback. They never allocate/free, print, delay or take a semaphore. Static lock-free assertions compile; [final producer disassembly](./trace_producer_disassembly.txt) was inspected for allocator/log/delay/semaphore calls. Heap integrity checks are separate checkpoints and take SDK heap locks; they perturb timing. Explicit failure dumping may block on UART, after trace producers have been frozen. No speculative ownership, watcher, locking, protocol or scheduling fix was implemented.

## Recovery and configuration differences

A failed check freezes and prints TEST_ONLY TRACE_BEGIN/TRACE/TRACE_END, then aborts with a TEST_ONLY reason. Any panic also has UART ELF core-dump recovery with DRAM capture of the exported .data/.bss trace symbols. Core dump uses a reserved2,048-byte stack. The SDK requires ISR stack2,096 instead of1,536 bytes when core dumps are enabled (FreeRTOS Kconfig426); this is an explicit recovery-only change. All other effective differences are ESP_COREDUMP settings. Heap poisoning remains disabled, allocation tracing remains off, and application task stacks/priorities, publication/loop delays, payload/QoS, QUIC and WIFI_PS_NONE settings stay unchanged. Diagnostic checks/logging/recovery necessarily alter timing and memory footprint.

[Proposed single-boot procedure](./PROPOSED_CAPTURE.md), [native GDB RAM extraction](./recover_trace.gdb), [offline decoder](./decode_trace.py). Always pass a saved core file explicitly: do not let a recovery tool read board flash. Run extraction in a new empty TEST_ONLY directory; decode refuses to overwrite its JSON. The installed GDB lacks embedded Python, so recovery deliberately uses native GDB dumps plus a standalone Python decoder. Its earlier Python-script failure is retained under host_validation.

[Offline synthetic validation](./host_validation.json) used the actual final ELF and real installed RISC-V GDB with synthetic ELF core-memory segments. It recovered two committed records in sequence order and skipped an in-progress record. The synthetic core intentionally has no CPU register notes, explaining GDB's missing-register warnings. This validates RAM extraction/decoding, NOT real board panic/core generation, UART completeness or fault reproduction. Hardware recovery remains untested; report incomplete recovery if a future core dump is damaged/missing.

## Build and artifacts

ESP-IDF v6.1, same GCC15.2.0 / esp-15.2.0_20251204, CMake4.0.3, Ninja1.12.1 and existing idf6.1_py3.14_env. [Tool versions/hashes](./tool_versions.json). Compiler path matches the preserved formal build. [Exact command and environment](./EXACT_BUILD_COMMAND.txt); working directory is this profile's src:

```text
C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe C:/esp/v6.1/esp-idf/tools/idf.py -B C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/test_only_heap_20261106/build -DSDKCONFIG=C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/test_only_heap_20261106/sdkconfig -DDEMO_TRANSPORT=QUIC -DDEMO_WIFI_PS_NONE=ON -DCCACHE_ENABLE=False build
```

Required environment includes ESP_IDF_VERSION=6.1.0, IDF_PATH=C:/esp/v6.1/esp-idf, IDF_PYTHON_ENV_PATH=C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env, IDF_COMPONENT_MANAGER=0 and the recorded compiler/CMake/Ninja PATH. [Machine-readable build report](./BUILD_REPORT.json) retains all attempt commands, logs and exits.

The initial configure stopped because manager-provided short component aliases were unavailable; private CMake wiring corrected that without dependency upgrades. The complete build passed, then an incremental rebuild/relink brought in the final cleanup-entry placement. [Final build log](./build_20261106T003539Z.log). [Warnings](./build_warnings.json) preserve SDK component/Kconfig notices and the inherited ngtcp2_acktr.c maybe-uninitialized warning; no speculative fix was applied.

Application **1,652,336 bytes**, partition **1,740,800**, free **88,464**. Bootloader0x5650 bytes with0x29b0 free; same partition layout and8MB flash arguments. No core-dump flash partition is used. Compiled source paths were verified private for all project/dependency sources. QUIC and WIFI_PS_NONE compile definitions verified. Runtime/API checks await separately authorized hardware work.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| [quic_demo.bin](./build/quic_demo.bin) | 1,652,336 | `6dd666d50640e1a79775d79bb83f43acdc3420582822e67026cb6cb8653301cb` |
| [quic_demo.elf](./build/quic_demo.elf) | 17,418,112 | `a8056d24f2e746d5f345b16e545e907f3339e6e87ea146895b57b1aaa7d32b70` |
| [bootloader/bootloader.bin](./build/bootloader/bootloader.bin) | 22,096 | `201aab89981d1f3a52dea8da1d05bf81f7e6244d2e9ab7eaa73cb46fa618501e` |
| [partition_table/partition-table.bin](./build/partition_table/partition-table.bin) | 3,072 | `8bc8d437a36b46e0880f7cbebe470527e27e4d454b536fff6633ac5f30539f16` |
| [flash_args](./build/flash_args) | 150 | `391bb7c5a21107d400c309f147e35cfbed5ba5988d3679234aa59168f6510ec0` |
| [flasher_args.json](./build/flasher_args.json) | 933 | `7519f9b5e2cf279a7521b4d90cb637cc857483c37a630da8685edd86fc723964` |

## Preservation

[Protected inventory before](./protected_before.json) and [after-build verification](./protection_verification.json) cover formal source/dependencies/configurations, original and both preserved profile builds, immutable formal results, plan and both registers. 10,271 checks passed. Caches, node_modules/junction trees and continuously growing monitor/after-run/supervisor logs are excluded explicitly; no such running process was stopped or modified. Existing formal artifacts/results are preserved. [Deliverable hashes](./SHA256SUMS.json).
