set(DIAG_MODE "0" CACHE STRING "0=normal run with diagnostics, 1=reboot cycles, 2=soft reconnect cycles")
set(DIAG_CYCLES "30" CACHE STRING "cycles per test")
set(DIAG_RUN_ID "r0" CACHE STRING "id of this test run (NVS namespace suffix, max 8 chars)")
set(DIAG_CHECKPOINTS "1" CACHE STRING "1=heap integrity checkpoints enabled")
idf_component_register(SRCS "crash_diag.c" INCLUDE_DIRS "include" REQUIRES esp_system heap freertos esp_rom log)
target_compile_definitions(${COMPONENT_LIB} PUBLIC CRASH_DIAG_MODE=${DIAG_MODE} CRASH_DIAG_CYCLES=${DIAG_CYCLES}
    CRASH_DIAG_CHECKPOINTS=${DIAG_CHECKPOINTS} "CRASH_DIAG_RUN_ID=\"${DIAG_RUN_ID}\"")
