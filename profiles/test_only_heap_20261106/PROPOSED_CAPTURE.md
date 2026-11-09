# TEST_ONLY single-boot capture — proposal only, not executed

This image is for diagnosis, not a replacement for HBPSN-03 or any registered run.
Do not apply formal RTT comparisons to its timings. A later explicit authorization
is required to flash/reset. Keep all original failed-run evidence and statuses.

1. Before a future authorized attempt, verify this profile's BIN/ELF/bootloader/
   partition SHA-256 hashes against BUILD_REPORT.json. Record the source diff,
   configuration, SDK/compiler and this image identity. Start a new TEST_ONLY
   directory. Record board MAC, COM6 enumeration, hotspot/server and host activity.
   Save actual Clumsy evidence and document its existing state; do not toggle any
   effect to make connection succeed. No formal register entry is created.
2. Only when separately authorized, close the exact existing monitor gracefully,
   flash this build's own matching flash arguments once, and prepare persistent
   raw serial capture at115200 with this ELF and the RISC-V toolchain. Configure
   host monitor core-dump decoding OFF so all original base64 UART bytes are
   retained. Capture setup resets separately. Neither this document nor its
   offline recovery commands authorize board access now.
3. Designate ONE controlled startup with logging already active. Confirm the
   TEST_ONLY banner and matching ELF prefix, QUIC/WIFI_PS_NONE settings, and record
   actual startup. Use one fixed120-second diagnostic observation from that reset;
   never extend it or retry a failure. Preserve complete UART output even if a
   core dump continues past120s: such tail bytes are recovery evidence, not an
   extended observation or a second boot measurement. Identify every automatic
   reboot; do not treat its measurements as the original boot. No pings/tests or
   alternate conditions. If no fault occurs, report NOT_REPRODUCED for that one
   boot; it does not establish a fix.
4. On a failed heap checkpoint, expect TEST_ONLY TRACE_BEGIN/TRACE/TRACE_END and
   a TEST_ONLY abort reason. Producer hooks never print, allocate or wait. This
   explicit failure dump is separate and may block on UART. Heap checkpoints use
   SDK heap locks and add overhead; application delays/priorities/intervals are
   unchanged. A panic inside an integrity check may prevent the textual dump.
5. On any panic, retain the complete standard SDK UART core-dump BEGIN/END block.
   The private sdkconfig enables ELF UART core dumps with whole DRAM capture and
   a2048-byte reserved core-dump stack, including trace .data/.bss. Extract ONLY
   the base64 payload between the markers into TEST_ONLY_core.b64. Preserve the
   original complete serial file, UTC/byte boundaries, and hashes. Do not alter
   standard core-dump framing to add labels; the capture directory/banner and
   decoded report are labelled TEST_ONLY. No core data is written to flash.
6. Recover OFFLINE with the exact diagnostic ELF. Always pass --core explicitly;
   omitting it may make the SDK tool read board flash, which is forbidden here.
   Run in a NEW empty TEST_ONLY capture directory containing the extracted
   TEST_ONLY_core.b64. Keep that raw payload unchanged. Use the existing RISC-V
   debugger explicitly (it has no embedded Python; the recovery script does not
   require it):

   ```powershell
   $testProfile = 'C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/test_only_heap_20261106'
   & 'C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/esp-coredump.exe' --chip esp32c6 --chip-rev 0 info_corefile --gdb 'C:/Espressif/tools/riscv32-esp-elf-gdb/17.1_20260402/riscv32-esp-elf-gdb/bin/riscv32-esp-elf-gdb.exe' --rom-elf 'C:/Users/newsh/.espressif/tools/esp-rom-elfs/20241011/esp32c6_rev0_rom.elf' --core TEST_ONLY_core.b64 --core-format b64 --extra-gdbinit-file "$testProfile/recover_trace.gdb" "$testProfile/build/quic_demo.elf"
   & 'C:/Users/newsh/.espressif/python_env/idf6.1_py3.14_env/Scripts/python.exe' -B "$testProfile/decode_trace.py" .
   ```

   This saves TEST_ONLY_trace_control.bin and TEST_ONLY_trace_ring.bin from the
   exported symbols, then writes TEST_ONLY_trace_recovered.json. The decoder
   refuses to overwrite an existing JSON. GDB binary dumps require a fresh empty
   directory to avoid overwriting earlier raw extractions. Archive the offline
   tool output and all input hashes. No serial port, target
   remote, load, flash or reset command belongs in this offline invocation.

Trace schema: control magic0x544f4844/version1/capacity256; each36-byte entry has
writing, commit, sequence, CPU cycles, numeric phase, task-handle identity, pointer,
related pointer/value and detail. The9,216-byte ring plus24-byte control is bounded.
Only writing==0 and commit==sequence!=0 entries are committed. Sort by sequence;
keep gaps/dropped/overwritten evidence. CPU cycles wrap and are not UTC. Task
handles identify tasks within the boot, not stable names across boots. Allocator
events cover ngtcp2's non-MEMDEBUG memory wrappers, not all SDK/wolfSSL mallocs.
ALLOC detail=size; CALLOC related=count/detail=element size; REALLOC BEGIN/END
record requested size and old/new pointer; FREE BEGIN/END bracket the real free.
PKTNS_ALLOC detail=packet-space ID. CHECK_PASS/FAIL detail=checkpoint phase.

If neither a textual trace nor a complete decodable core dump survives, report
RECOVERY_INCOMPLETE. UART disconnection, damaged allocator state, stack exhaustion
or a reset can prevent recovery. Do not invent entries or retry automatically.
No hardware recovery has been validated as part of this build-only task.
