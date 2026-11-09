# TEST_ONLY offline recovery, compatible with GDB without Python.
# Run only in a NEW empty TEST_ONLY capture directory; dump files must not exist.
# No target remote, load, monitor, flash or reset commands.
set pagination off
if g_test_only_heap_control.magic != 0x544f4844 || g_test_only_heap_control.version != 1 || g_test_only_heap_control.capacity != 256
    echo TEST_ONLY trace identity/schema mismatch\n
    quit 1
end
dump binary memory TEST_ONLY_trace_control.bin &g_test_only_heap_control ((char *)&g_test_only_heap_control + sizeof(g_test_only_heap_control))
dump binary memory TEST_ONLY_trace_ring.bin &g_test_only_heap_trace[0] &g_test_only_heap_trace[256]
printf "TEST_ONLY TRACE_RAW_SAVED next=%u dropped=%u frozen=%u\n", g_test_only_heap_control.next_sequence, g_test_only_heap_control.dropped, g_test_only_heap_control.frozen
