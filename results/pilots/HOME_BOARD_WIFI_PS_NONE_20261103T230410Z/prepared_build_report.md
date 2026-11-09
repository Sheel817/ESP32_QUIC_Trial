# New experimental Wi-Fi power-saving-off profile

Built only; NOT FLASHED. No runtime/API readback verification has been performed on the board.

## Preservation

Tested source/configuration, populated dependency sources and original QUIC images/ELF/flash arguments were archived before editing in:

`C:\Users\newsh\Desktop\ESP32_QUIC_Checkpoints\pre_wifi_ps_none_20261103T162643Z`

The ZIP entries were verified against the per-file manifest; archive.sha256 records the archive checksum. All 6,198 inventoried original build files were rehashed after this build: no changed, missing or added files. This inventory excludes the linked node_modules dependency tree; the earlier full backup includes that tree. Original source/config hashes changed only for the two intended files. The original sdkconfig, dependencies.lock and populated dependency sources remained unchanged. Earlier results were preserved.

## Change

- main/CMakeLists.txt: adds DEMO_WIFI_PS_NONE, default OFF; compile definition 0/1; explicit esp_wifi dependency.
- main/quic_demo_main.c: includes esp_wifi.h; guarded block after example_connect and Wi-Fi connected log, before xTaskCreate. Sets WIFI_PS_NONE, checks API status, reads/checks mode, logs requested/returned names and numbers once. A mismatched returned mode fails before transport starts. Shared by QUIC and TCP_TLS.
- GPIO4/DHT11, payload, topic, client ID, QoS, five-second interval, APP_RTT reserve/timer placement, quiet logging, loop delay and processing cadence are unchanged. Removing the added include and guarded block reproduces the tested application source exactly.
- Separate profiles/wifi_ps_none_20261103/sdkconfig copy and build output. No effective CONFIG_ value differences from original sdkconfig.

## Build

Exact reproducible environment/command is in [build_profile.ps1](./build_profile.ps1). Run from the project root. The enable option is `-DDEMO_WIFI_PS_NONE=ON`; omit it for a fresh default-OFF build, or explicitly pass OFF when reusing a CMake cache. The experimental output cache retains ON.

```powershell
$env:PYTHONUTF8 = '1'
$env:ESP_IDF_VERSION = '6.1.0'
$env:IDF_PATH = 'C:\esp\v6.1\esp-idf'
$env:IDF_TOOLS_PATH = 'C:\Users\newsh\.espressif'
$env:IDF_PYTHON_ENV_PATH = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env'
$env:IDF_COMPONENT_CHECK_NEW_VERSION = '0'
$env:PATH = "$env:IDF_PYTHON_ENV_PATH\Scripts;C:\Espressif\tools\cmake\4.0.3\bin;C:\Espressif\tools\ninja\1.12.1;C:\Espressif\tools\riscv32-esp-elf\esp-15.2.0_20251204\riscv32-esp-elf\bin;" + $env:PATH
& "$env:IDF_PYTHON_ENV_PATH\Scripts\python.exe" "$env:IDF_PATH\tools\idf.py" -B C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/wifi_ps_none_20261103/build -DSDKCONFIG=C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/wifi_ps_none_20261103/sdkconfig -DDEMO_TRANSPORT=QUIC -DDEMO_WIFI_PS_NONE=ON -DCCACHE_ENABLE=False build
```

Build and bootloader/application partition checks PASS. Image size 1,637,280 bytes; application partition 1,740,800 bytes; free 103,520 bytes (about 5.95%, build reports 6%). Image: [quic_demo.bin](./build/quic_demo.bin).

SHA-256: `6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198`

Compiler: existing GCC 15.2.0, ESP-IDF v6.1. No packages/dependencies were upgraded. Initial attempts with the older C:/Espressif Python environment failed preflight (missing constraints location, then monitor 1.9.0 below SDK requirement). The successful build uses the already installed idf6.1_py3.14_env, monitor 1.10.0 and esptool 5.6.0; this differs from the older tools environment and is recorded for reproducibility. The build logged a nonfatal GDB init warning because ESP_ROM_ELF_DIR was not defined, plus SDK Kconfig notices; firmware linking and size checks passed. Full output: [build_final.log](./build_final.log).

Compile commands verify DEMO_WIFI_PS_NONE=1 and DEMO_TRANSPORT_TCP_TLS=0 for the application. No flash, reset, board connection, server/monitor stop or Clumsy change was performed. Clumsy stopped state is operator-reported and was left untouched.

## Diff against preserved tested files

```diff
--- tested/main/CMakeLists.txt
+++ experimental/main/CMakeLists.txt
@@ -1,4 +1,5 @@
 set(DEMO_TRANSPORT "TCP_TLS" CACHE STRING "Measurement transport: QUIC or TCP_TLS")
+option(DEMO_WIFI_PS_NONE "Experimental profile: disable Wi-Fi power saving after connection" OFF)
 set_property(CACHE DEMO_TRANSPORT PROPERTY STRINGS QUIC TCP_TLS)
 if(NOT DEMO_TRANSPORT STREQUAL "QUIC" AND NOT DEMO_TRANSPORT STREQUAL "TCP_TLS")
     message(FATAL_ERROR "DEMO_TRANSPORT must be QUIC or TCP_TLS")
@@ -20,6 +21,7 @@
         wolfssl 
         coreMQTT
         esp_timer
+        esp_wifi
         protocol_examples_common
     INCLUDE_DIRS "")
 
@@ -29,3 +31,6 @@
     target_compile_definitions(${COMPONENT_LIB} PRIVATE DEMO_TRANSPORT_TCP_TLS=0)
 endif()
 message(STATUS "Measurement transport: ${DEMO_TRANSPORT}")
+target_compile_definitions(${COMPONENT_LIB} PRIVATE
+    DEMO_WIFI_PS_NONE=$<BOOL:${DEMO_WIFI_PS_NONE}>)
+message(STATUS "Experimental Wi-Fi power-saving-off profile: ${DEMO_WIFI_PS_NONE}")
--- tested/main/quic_demo_main.c
+++ experimental/main/quic_demo_main.c
@@ -17,6 +17,7 @@
 #include "esp_netif.h"
 #include "esp_system.h"
 #include "esp_timer.h"
+#include "esp_wifi.h"
 #include "nvs_flash.h"
 
 #include "protocol_examples_common.h"
@@ -579,6 +580,20 @@
 
     ESP_LOGI(TAG, "Wi-Fi connected");
 
+#if DEMO_WIFI_PS_NONE
+    /* Optional experimental profile, shared by QUIC and TCP_TLS. */
+    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
+    wifi_ps_type_t returned_ps_mode;
+    ESP_ERROR_CHECK(esp_wifi_get_ps(&returned_ps_mode));
+    const char *returned_ps_name =
+        returned_ps_mode == WIFI_PS_NONE ? "WIFI_PS_NONE" :
+        returned_ps_mode == WIFI_PS_MIN_MODEM ? "WIFI_PS_MIN_MODEM" :
+        returned_ps_mode == WIFI_PS_MAX_MODEM ? "WIFI_PS_MAX_MODEM" : "UNKNOWN";
+    ESP_LOGI(TAG, "EXPERIMENTAL Wi-Fi profile: requested=WIFI_PS_NONE(%d), returned=%s(%d)",
+             (int)WIFI_PS_NONE, returned_ps_name, (int)returned_ps_mode);
+    ESP_ERROR_CHECK(returned_ps_mode == WIFI_PS_NONE ? ESP_OK : ESP_ERR_INVALID_STATE);
+#endif
+
     BaseType_t task_status = xTaskCreate(
         quic_sensor_task,
         "quic_dht11",
```
