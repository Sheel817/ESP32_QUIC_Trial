# TCP_TLS WIFI_PS_NONE matching build

Built only. Not flashed or reset; runtime behavior is not yet verified.

Build/link, bootloader/application partition checks and offline image checksum/digest verification **PASS**. Application partition 1,740,800 bytes; free 241,936 bytes. Same modified source revision as validated QUIC: Git HEAD 3c8c7a30b7b32ae3feaa07788b74eec637be37fc, project version 3c8c7a3-dirty; source content hashes are authoritative because the tree is modified.

| Artifact under build/ | Bytes | SHA-256 |
|---|---:|---|
| quic_demo.bin | 1498864 | `ff97eb5d20c9c47375539395f9cf23c1d0780381562cf511094d4b525ab17de8` |
| quic_demo.elf | 16790856 | `1f661a4f7214dd0bd499cdf03783ca40633542fb95a6d164e1233c0b6f6363e6` |
| bootloader/bootloader.bin | 22096 | `726bb68a523511c6e08904ab50d6d19455cc940a16b58f989ac3446bd2c627e1` |
| partition_table/partition-table.bin | 3072 | `8bc8d437a36b46e0880f7cbebe470527e27e4d454b536fff6633ac5f30539f16` |
| flash_args | 150 | `391bb7c5a21107d400c309f147e35cfbed5ba5988d3679234aa59168f6510ec0` |
| flasher_args.json | 933 | `7519f9b5e2cf279a7521b4d90cb637cc857483c37a630da8685edd86fc723964` |

[Image](./build/quic_demo.bin), [ELF](./build/quic_demo.elf), [build log](./build.log), [full validation/preservation report](./validation.json), [source identity](./source_identity.json), [image descriptor](./image_info.txt).

## Exact command and environment

Run the following lines from the project root. The host's Restricted PowerShell script policy did not execute the first script-file invocation; no build ran in that attempt. The successful build executed these same environment assignments and idf.py command inline without changing that policy. The retained build_profile.ps1 records the command for reproducibility.

```powershell
$env:PYTHONUTF8 = '1'
$env:ESP_IDF_VERSION = '6.1.0'
$env:IDF_PATH = 'C:/esp/v6.1/esp-idf'
$env:IDF_TOOLS_PATH = 'C:/Users/newsh/.espressif'
$env:IDF_PYTHON_ENV_PATH = 'C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env'
$env:IDF_COMPONENT_CHECK_NEW_VERSION = '0'
$env:PATH = "$env:IDF_PYTHON_ENV_PATH/Scripts;C:/Espressif/tools/cmake/4.0.3/bin;C:/Espressif/tools/ninja/1.12.1;C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin;" + $env:PATH
& "$env:IDF_PYTHON_ENV_PATH/Scripts/python.exe" "$env:IDF_PATH/tools/idf.py" -B C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/tcp_tls_wifi_ps_none_20261104/build -DSDKCONFIG=C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/tcp_tls_wifi_ps_none_20261104/sdkconfig -DDEMO_TRANSPORT=TCP_TLS -DDEMO_WIFI_PS_NONE=ON -DCCACHE_ENABLE=False build
```

## Differences from validated QUIC PS_NONE

- DEMO_TRANSPORT=TCP_TLS instead of QUIC; DEMO_TRANSPORT_TCP_TLS=1 instead of 0. DEMO_WIFI_PS_NONE stays ON / 1.
- Separate profile sdkconfig and output paths. Effective CONFIG_ entries and generated sdkconfig JSON are identical. ESP-IDF v6.1 and GCC/G++ 15.2.0 executable paths match. Dependency lock and preserved source/configuration inputs are unchanged.
- The existing transport branch selects TCP+TLS at port 14568 instead of QUIC UDP 14567. Existing TLS 1.3 / AES-128-GCM / ALPN mqtt requirements and TCP_NODELAY checks apply. No firmware logic was edited. DHT11 GPIO4, payload, topic/client ID, QoS 0, five-second sampling, APP_RTT timing, loop cadence and quiet logging remain shared and unchanged.
- Build timestamps and transport-specific link contents cause different BIN/ELF sizes/hashes. No dependency upgrade was performed.

All 6198 inventoried original-build files and 1796 QUIC-profile files remain hash-identical, with no added/missing files in those inventories. Linked node_modules directories were excluded. All 1428 recorded source/config inputs remain unchanged.

Warnings are preserved in validation.json and build.log. They include the established missing ESP_ROM_ELF_DIR GDB-symbol setup warning, SDK Kconfig/component notices, generic ESP-TLS/wolfSSL notice and ngtcp2 maybe-uninitialized warning where emitted. The inline invocation used forward-slash IDF_PYTHON_ENV_PATH spelling, producing a venv-path string comparison warning; the invoked interpreter is the same installed idf6.1_py3.14_env. No packages/environment were upgraded to address warnings. Firmware linking and partition validation succeeded.

The newlib syscall-stub warnings printed in CMAKE_C_COMPILER_PRODUCED_OUTPUT / CMAKE_CXX_COMPILER_PRODUCED_OUTPUT are compiler ABI-probe output, also present in the QUIC build log. They are not new application-link failures.

Compile-command comparison covers all 1,139 translation units. After normalizing the transport macro and build/object output destinations, compiler commands match exactly. The longer TCP profile path causes CMake to hash 11 mbedTLS object destination paths; this changes output filenames, not source or flags. See compile_settings_comparison.json.
