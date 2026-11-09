#include "test_only_heap_diag.h"
#include "esp_cpu.h"
#include "esp_heap_caps.h"
#include "esp_rom_sys.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

_Static_assert(sizeof(uintptr_t) == 4, "TEST_ONLY trace schema requires 32-bit target");
_Static_assert(__atomic_always_lock_free(4, 0), "TEST_ONLY requires lock-free word atomics");
_Static_assert(sizeof(test_only_heap_trace_entry) == 36, "TEST_ONLY trace schema v1");

/* Exported ordinary .data/.bss symbols: private UART core dump captures DRAM. */
volatile test_only_heap_trace_control g_test_only_heap_control = {
    .magic = TEST_ONLY_TRACE_MAGIC, .version = 1, .capacity = TEST_ONLY_TRACE_CAPACITY
};
volatile test_only_heap_trace_entry g_test_only_heap_trace[TEST_ONLY_TRACE_CAPACITY];

__attribute__((noinline))
void test_only_heap_trace(uint32_t phase, const void *pointer,
                          const void *related, uint32_t detail)
{
    if (__atomic_load_n(&g_test_only_heap_control.frozen, __ATOMIC_RELAXED)) return;
    uint32_t seq = __atomic_add_fetch(&g_test_only_heap_control.next_sequence, 1, __ATOMIC_RELAXED);
    volatile test_only_heap_trace_entry *slot = &g_test_only_heap_trace[(seq - 1) % TEST_ONLY_TRACE_CAPACITY];
    /* Never spin/wait if another producer was preempted on this slot. */
    if (__atomic_exchange_n(&slot->writing, 1, __ATOMIC_ACQUIRE)) {
        __atomic_fetch_add(&g_test_only_heap_control.dropped, 1, __ATOMIC_RELAXED);
        return;
    }
    __atomic_store_n(&slot->commit, 0, __ATOMIC_RELAXED);
    slot->sequence = seq;
    slot->cycles = esp_cpu_get_cycle_count();
    slot->phase = phase;
    slot->task = (uint32_t)(uintptr_t)xTaskGetCurrentTaskHandle();
    slot->pointer = (uint32_t)(uintptr_t)pointer;
    slot->related = (uint32_t)(uintptr_t)related;
    slot->detail = detail;
    __atomic_store_n(&slot->commit, seq, __ATOMIC_RELEASE);
    __atomic_store_n(&slot->writing, 0, __ATOMIC_RELEASE);
}

/* Explicit failure recovery, NOT a producer hook. UART output may block here. */
static void test_only_heap_dump_failure(uint32_t failed_phase)
{
    __atomic_store_n(&g_test_only_heap_control.frozen, 1, __ATOMIC_RELEASE);
    esp_rom_printf("TEST_ONLY TRACE_BEGIN v=1 capacity=%u next=%u dropped=%u failed_phase=%u\n",
                   TEST_ONLY_TRACE_CAPACITY, g_test_only_heap_control.next_sequence,
                   g_test_only_heap_control.dropped, failed_phase);
    for (uint32_t i = 0; i < TEST_ONLY_TRACE_CAPACITY; ++i) {
        volatile test_only_heap_trace_entry *e = &g_test_only_heap_trace[i];
        uint32_t commit = __atomic_load_n(&e->commit, __ATOMIC_ACQUIRE);
        if (__atomic_load_n(&e->writing, __ATOMIC_ACQUIRE) || !commit || commit != e->sequence) continue;
        esp_rom_printf("TEST_ONLY TRACE slot=%u seq=%u cycles=%u phase=%u task=%08x ptr=%08x related=%08x detail=%u\n",
                       i, e->sequence, e->cycles, e->phase, e->task,
                       e->pointer, e->related, e->detail);
    }
    esp_rom_printf("TEST_ONLY TRACE_END\n");
}

void test_only_heap_check(uint32_t phase, const void *pointer, const void *related)
{
    test_only_heap_trace(phase, pointer, related, 0);
    /* Not an allocation/free hook: full SDK heap check, outside allocator calls. */
    if (!heap_caps_check_integrity_all(false)) {
        test_only_heap_trace(TEST_ONLY_CHECK_FAIL, pointer, related, phase);
        test_only_heap_dump_failure(phase);
        esp_system_abort("TEST_ONLY heap integrity checkpoint failed; trace frozen");
    }
    test_only_heap_trace(TEST_ONLY_CHECK_PASS, pointer, related, phase);
}

void test_only_heap_banner(void)
{
    test_only_heap_trace(TEST_ONLY_BOOT, (const void *)g_test_only_heap_trace,
                         (const void *)&g_test_only_heap_control, sizeof(g_test_only_heap_trace));
    esp_rom_printf("TEST_ONLY QUIC HEAP DIAGNOSTIC v1; not formal firmware; trace=%p control=%p bytes=%u\n",
                   g_test_only_heap_trace, &g_test_only_heap_control,
                   (unsigned)sizeof(g_test_only_heap_trace));
}
