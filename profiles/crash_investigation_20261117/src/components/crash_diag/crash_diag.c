#include "crash_diag.h"
#include <stdio.h>
#include <string.h>
#include "esp_heap_caps.h"
#include "esp_rom_sys.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static uint32_t s_seq;
static const char *s_last_pass[8];

void crash_diag_banner(void)
{
    esp_rom_printf("DIAG BANNER DIAGNOSTIC_NOT_FOR_MEASUREMENT mode=%d cycles=%d run=%s checkpoints=%d\n",
                   CRASH_DIAG_MODE, CRASH_DIAG_CYCLES, CRASH_DIAG_RUN_ID, CRASH_DIAG_CHECKPOINTS);
}

void crash_diag_checkpoint(const char *name)
{
#if CRASH_DIAG_CHECKPOINTS
    uint32_t seq = ++s_seq;
    if (!heap_caps_check_integrity_all(false)) {
        esp_rom_printf("DIAG CHECKPOINT FAIL seq=%u name=%s last_pass=%s\n", (unsigned)seq, name,
                       s_last_pass[(seq - 1) & 7] ? s_last_pass[(seq - 1) & 7] : "none");
        esp_rom_printf("DIAG heap_caps_check_integrity_all(print_errors) follows\n");
        (void)heap_caps_check_integrity_all(true);
        esp_system_abort("DIAG heap integrity checkpoint failed");
    }
    s_last_pass[seq & 7] = name;
    esp_rom_printf("DIAG CP %u %s ok\n", (unsigned)seq, name);
#else
    (void)name;
#endif
}

void crash_diag_heap(const char *stage)
{
    esp_rom_printf("DIAG HEAP %s free=%u min_free=%u largest_block=%u\n", stage,
                   (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size(),
                   (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_DEFAULT));
}

void crash_diag_note(const char *tag, unsigned a, unsigned b, unsigned c)
{
    esp_rom_printf("DIAG NOTE %s %u %u %u\n", tag, a, b, c);
}

void crash_diag_stacks(const char *stage)
{
    static const char *const names[] = {"quic_dht11", "io_monitor", "ev_esp_loop", "main", "Tmr Svc", "sys_evt"};
    for (unsigned i = 0; i < sizeof(names) / sizeof(names[0]); ++i) {
        TaskHandle_t h = xTaskGetHandle(names[i]);
        if (h) {
            esp_rom_printf("DIAG STACK %s task=%s high_water_mark_bytes_free=%u\n", stage, names[i],
                           (unsigned)uxTaskGetStackHighWaterMark(h));
        }
    }
}
