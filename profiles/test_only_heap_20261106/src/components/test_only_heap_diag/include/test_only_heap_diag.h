#pragma once
#include <stddef.h>
#include <stdint.h>

/* TEST_ONLY: numeric schema is also consumed offline; never changes ownership. */
enum test_only_heap_phase {
    TEST_ONLY_BOOT = 1,
    TEST_ONLY_BEFORE_WRITE = 2,
    TEST_ONLY_CLEANUP_ENTRY = 3,
    TEST_ONLY_BEFORE_FINAL_FREE = 4,
    TEST_ONLY_CHECK_PASS = 5,
    TEST_ONLY_CHECK_FAIL = 6,
    TEST_ONLY_ALLOC = 7,
    TEST_ONLY_FREE_BEGIN = 8,
    TEST_ONLY_FREE_END = 9,
    TEST_ONLY_CALLOC = 10,
    TEST_ONLY_REALLOC_BEGIN = 11,
    TEST_ONLY_REALLOC_END = 12,
    TEST_ONLY_PKTNS_ALLOC = 13
};
#define TEST_ONLY_TRACE_CAPACITY 256u
#define TEST_ONLY_TRACE_MAGIC 0x544f4844u
typedef struct {
    uint32_t writing, commit, sequence, cycles, phase, task;
    uint32_t pointer, related, detail;
} test_only_heap_trace_entry;
typedef struct {
    uint32_t magic, version, capacity, next_sequence, dropped, frozen;
} test_only_heap_trace_control;
extern volatile test_only_heap_trace_control g_test_only_heap_control;
extern volatile test_only_heap_trace_entry g_test_only_heap_trace[TEST_ONLY_TRACE_CAPACITY];

/* Producer only: fixed memory, lock-free try-once slot reservation, no I/O. */
void test_only_heap_trace(uint32_t phase, const void *pointer,
                          const void *related, uint32_t detail);
/* Checkpoints are separate from trace producers: SDK integrity checks take heap locks. */
void test_only_heap_check(uint32_t phase, const void *pointer, const void *related);
void test_only_heap_banner(void);
