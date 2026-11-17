"""Create the DIAGNOSTIC-ONLY crash investigation profile source tree. No device access.
Copies the frozen QUIC source set (hash-verified against profiles/tcp_tls_wifi_ps_none_20261104/source_before.json),
then applies diagnostic edits. Frozen profiles and the root tree are only read."""
from pathlib import Path
import datetime as dt, hashlib, json, shutil, re

root = Path(__file__).resolve().parents[2]
p = Path(__file__).resolve().parent
src = p / 'src'
assert not src.exists(), 'src already exists; do not reuse'


def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()


manifest = json.loads((root / 'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json').read_text())
mism = [k for k, v in manifest.items() if sha(root / k) != v]
(p / 'baseline_check.json').write_text(json.dumps(dict(files=len(manifest), mismatches=mism), indent=2))
assert not mism, mism
for rel in manifest:
    t = src / rel
    t.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / rel, t)
shutil.copy2(root / 'profiles/wifi_ps_none_20261103/sdkconfig', p / 'sdkconfig.baseline')
shutil.copy2(root / 'profiles/wifi_ps_none_20261103/sdkconfig', p / 'sdkconfig')
baseline = {rel: sha(src / rel) for rel in manifest}


def replace(rel, old, new, count=1):
    f = src / rel
    t = f.read_text(encoding='utf-8')
    assert t.count(old) == count, (rel, old, t.count(old))
    f.write_text(t.replace(old, new), encoding='utf-8')


# ---- diagnostic component
comp = src / 'components/crash_diag'
(comp / 'include').mkdir(parents=True)
(comp / 'CMakeLists.txt').write_text('''set(DIAG_MODE "0" CACHE STRING "0=normal run with diagnostics, 1=reboot cycles, 2=soft reconnect cycles")
set(DIAG_CYCLES "30" CACHE STRING "cycles per test")
set(DIAG_RUN_ID "r0" CACHE STRING "id of this test run (NVS namespace suffix, max 8 chars)")
set(DIAG_CHECKPOINTS "1" CACHE STRING "1=heap integrity checkpoints enabled")
idf_component_register(SRCS "crash_diag.c" INCLUDE_DIRS "include" REQUIRES esp_system heap freertos esp_rom log)
target_compile_definitions(${COMPONENT_LIB} PUBLIC CRASH_DIAG_MODE=${DIAG_MODE} CRASH_DIAG_CYCLES=${DIAG_CYCLES}
    CRASH_DIAG_CHECKPOINTS=${DIAG_CHECKPOINTS} "CRASH_DIAG_RUN_ID=\\"${DIAG_RUN_ID}\\"")
''')
(comp / 'include/crash_diag.h').write_text('''#pragma once
/* DIAGNOSTIC ONLY - never used for timing or reliability measurements. */
#ifdef __cplusplus
extern "C" {
#endif
#ifndef CRASH_DIAG_MODE
#define CRASH_DIAG_MODE 0
#endif
#ifndef CRASH_DIAG_CHECKPOINTS
#define CRASH_DIAG_CHECKPOINTS 1
#endif
void crash_diag_banner(void);
void crash_diag_checkpoint(const char *name);
void crash_diag_heap(const char *stage);
void crash_diag_stacks(const char *stage);
#ifdef __cplusplus
}
#endif
''')
(comp / 'crash_diag.c').write_text(r'''#include "crash_diag.h"
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
''')

# ---- wiring
replace('CMakeLists.txt', 'include($ENV{IDF_PATH}/tools/cmake/project.cmake)', '''# DIAGNOSTIC profile: use existing private dependency copies without dependency resolution.
set(EXTRA_COMPONENT_DIRS "${CMAKE_SOURCE_DIR}/managed_components"
    "$ENV{IDF_PATH}/examples/common_components/protocol_examples_common")
set(PROJECT_VER "3c8c7a3-dirty-DIAGNOSTIC")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)''')
replace('main/CMakeLists.txt', '        protocol_examples_common', '        protocol_examples_common\n        crash_diag')
replace('components/ngtcp2/CMakeLists.txt', 'REQUIRES wolfssl)', 'REQUIRES wolfssl__wolfssl crash_diag)')

# ---- ngtcp2 library checkpoints
N = 'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c'
replace(N, '#include "ngtcp2_conn.h"', '#include "ngtcp2_conn.h"\n#include "crash_diag.h"')
replace(N, '  ngtcp2_pktns *pktns = *ppktns;\n  uint64_t bytes_in_flight;',
        '  ngtcp2_pktns *pktns = *ppktns;\n  uint64_t bytes_in_flight;\n\n  crash_diag_checkpoint("discard_pktns_entry");')
replace(N, '  pktns_del(pktns, conn->mem);\n  *ppktns = NULL;',
        '  crash_diag_checkpoint("discard_before_pktns_del");\n  pktns_del(pktns, conn->mem);\n  *ppktns = NULL;\n  crash_diag_checkpoint("discard_after_pktns_del");')
replace(N, '  pktns_free(pktns, mem);\n\n  ngtcp2_mem_free(mem, pktns);',
        '  crash_diag_checkpoint("pktns_del_before_pktns_free");\n  pktns_free(pktns, mem);\n  crash_diag_checkpoint("pktns_del_before_final_free");\n  ngtcp2_mem_free(mem, pktns);')
replace(N, '                             NGTCP2_PKT_HANDSHAKE, wflags, write_datalen, ts);\n  if (nwrite < 0) {',
        '                             NGTCP2_PKT_HANDSHAKE, wflags, write_datalen, ts);\n  crash_diag_checkpoint("after_handshake_pkt_built");\n  if (nwrite < 0) {')
W = 'components/ngtcp2/ngtcp2/crypto/wolfssl/wolfssl.c'
replace(W, '    rv = wolfSSL_provide_quic_data(ssl, level, data, datalen);',
        '    crash_diag_checkpoint("before_provide_quic_data");\n    rv = wolfSSL_provide_quic_data(ssl, level, data, datalen);\n    crash_diag_checkpoint("after_provide_quic_data");')
replace(W, '    rv = wolfSSL_quic_do_handshake(ssl);',
        '    crash_diag_checkpoint("before_quic_do_handshake");\n    rv = wolfSSL_quic_do_handshake(ssl);\n    crash_diag_checkpoint("after_quic_do_handshake");')
t = (src / W).read_text(encoding='utf-8')
i = t.index('#include')
(src / W).write_text(t[:i] + '#include "crash_diag.h"\n' + t[i:], encoding='utf-8')

# ---- application
S = 'main/ngtcp2_sample.c'
replace(S, '#include "tls_negotiation.h"', '#include "tls_negotiation.h"\n#include "crash_diag.h"')
replace(S, '  c->stream.stream_id = -1;\n', '  crash_diag_checkpoint("after_client_quic_init");\n  c->stream.stream_id = -1;\n')
replace(S, '    nwrite = ngtcp2_conn_writev_stream(', '    crash_diag_checkpoint("before_writev_stream");\n    nwrite = ngtcp2_conn_writev_stream(')
replace(S, '    if (nwrite == 0) {\n      return 0;\n    }', '    crash_diag_checkpoint("after_writev_stream");\n    if (nwrite == 0) {\n      return 0;\n    }')
replace(S, '    result = client_read(&g_client);\n', '    result = client_read(&g_client);\n    crash_diag_checkpoint("after_client_read");\n')
replace(S, '    g_quic_handshake_completed = true;\n    return 0;', '    g_quic_handshake_completed = true;\n    crash_diag_heap("after_quic_handshake");\n    return 0;')
# soft-reconnect mode: ev_default_loop_init() memsets the live loop and creates a new event task on every call; call it once.
replace(S, '    ev_default_loop_init();\n', '#if CRASH_DIAG_MODE == 2\n    { static bool diag_loop_ready; if (!diag_loop_ready) { ev_default_loop_init(); diag_loop_ready = true; } }\n#else\n    ev_default_loop_init();\n#endif\n')

M = 'main/quic_demo_main.c'
replace(M, '#include "esp_wifi.h"', '#include "esp_wifi.h"\n#include "crash_diag.h"\n#include "nvs.h"\n#include "esp_rom_sys.h"')
replace(M, '    ESP_LOGI(TAG, "Wi-Fi connected");\n', '    ESP_LOGI(TAG, "Wi-Fi connected");\n    crash_diag_heap("after_wifi_connected");\n')
replace(M, '    ESP_LOGI(TAG, "MQTT connected over %s", DEMO_TRANSPORT_NAME);\n',
        '    ESP_LOGI(TAG, "MQTT connected over %s", DEMO_TRANSPORT_NAME);\n    crash_diag_heap("after_mqtt_connected");\n    crash_diag_stacks("after_mqtt_connected");\n')
replace(M, 'void app_main(void)\n{\n', 'void app_main(void)\n{\n    crash_diag_banner();\n')
cycle = r'''#if CRASH_DIAG_MODE
/* DIAGNOSTIC cycle task: QUIC connect, wait for handshake, then reboot (mode 1) or close and reconnect (mode 2).
 * Counters live in NVS so crashes (which reboot the board) are counted: started - passed - failed = crashed. */
static void diag_cycle_task(void *argument)
{
    (void)argument;
    nvs_handle_t h;
    char ns[16];
    snprintf(ns, sizeof(ns), "dg%s", CRASH_DIAG_RUN_ID);
    uint32_t started = 0, passed = 0, failed = 0;
    ESP_ERROR_CHECK(nvs_open(ns, NVS_READWRITE, &h));
    (void)nvs_get_u32(h, "started", &started);
    (void)nvs_get_u32(h, "passed", &passed);
    (void)nvs_get_u32(h, "failed", &failed);
    esp_rom_printf("DIAG RESUME run=%s mode=%d started=%u passed=%u failed=%u crashed_so_far=%d\n", CRASH_DIAG_RUN_ID,
                   CRASH_DIAG_MODE, (unsigned)started, (unsigned)passed, (unsigned)failed,
                   (int)started - (int)passed - (int)failed);
    char port_text[16];
    snprintf(port_text, sizeof(port_text), "%u", (unsigned)server_info.port);
    quic_client_config_t quic_config = {.hostname = server_info.pHostName, .port = port_text, .alpn = server_info.pAlpn};
    while (started < CRASH_DIAG_CYCLES) {
        started++;
        ESP_ERROR_CHECK(nvs_set_u32(h, "started", started));
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("DIAG CYCLE %u START mode=%d\n", (unsigned)started, CRASH_DIAG_MODE);
        crash_diag_heap("cycle_start");
        bool ok = quic_client_init_with_config(&quic_config) == 0 && wait_for_quic_ready();
        if (ok) {
            crash_diag_heap("cycle_after_handshake");
            crash_diag_stacks("cycle_after_handshake");
            vTaskDelay(pdMS_TO_TICKS(1000));
            passed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "passed", passed));
        } else {
            failed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "failed", failed));
        }
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("DIAG CYCLE %u %s\n", (unsigned)started, ok ? "PASS" : "FAIL_TIMEOUT_OR_INIT");
        if (CRASH_DIAG_MODE == 1) {
            esp_rom_printf("DIAG REBOOTING\n");
            vTaskDelay(pdMS_TO_TICKS(200));
            esp_restart();
        }
        quic_client_cleanup();
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
    esp_rom_printf("DIAG COMPLETE run=%s mode=%d cycles=%d started=%u passed=%u failed_timeout=%u crashed=%d\n",
                   CRASH_DIAG_RUN_ID, CRASH_DIAG_MODE, CRASH_DIAG_CYCLES, (unsigned)started, (unsigned)passed,
                   (unsigned)failed, (int)started - (int)passed - (int)failed);
    nvs_close(h);
    vTaskDelete(NULL);
}
#endif

void app_main(void)'''
replace(M, 'void app_main(void)', cycle)
replace(M, '        quic_sensor_task,\n        "quic_dht11",', '#if CRASH_DIAG_MODE\n        diag_cycle_task,\n#else\n        quic_sensor_task,\n#endif\n        "quic_dht11",')

# ---- dht component: dependency name as used when the component manager is disabled (same fix as the TEST_ONLY profile)
d = 'managed_components/esp-idf-lib__dht/CMakeLists.txt'
replace(d, ' esp_idf_lib_helpers', ' esp-idf-lib__esp_idf_lib_helpers', count=3)

# ---- sdkconfig (diagnostics only)
cfg = p / 'sdkconfig'
t = cfg.read_text()
settings = {
    'CONFIG_HEAP_POISONING_DISABLED': None, 'CONFIG_HEAP_POISONING_COMPREHENSIVE': 'y',
    'CONFIG_COMPILER_STACK_CHECK_MODE_NONE': None, 'CONFIG_COMPILER_STACK_CHECK_MODE_STRONG': 'y',
    'CONFIG_ESP_SYSTEM_USE_EH_FRAME': 'y',
}
for k, v in settings.items():
    t = re.sub(r'^' + k + r'=.*\n|^# ' + k + r' is not set\n', '', t, flags=re.M)
    t += (f'{k}={v}\n' if v is not None else f'# {k} is not set\n')
cfg.write_text(t, encoding='utf-8')
(src / 'partitions.csv').write_text('# DIAGNOSTIC profile: larger factory partition (frozen builds keep 1700K)\nnvs,      data, nvs,     ,        0x6000,\nphy_init, data, phy,     ,        0x1000,\nfactory,  app,  factory, ,        2560K,\n')
changed = [rel for rel in manifest if sha(src / rel) != baseline[rel]]
(p / 'changed_source_files.json').write_text(json.dumps(dict(
    modified_vs_frozen=changed,
    added=['components/crash_diag/CMakeLists.txt', 'components/crash_diag/crash_diag.c', 'components/crash_diag/include/crash_diag.h'],
    sdkconfig_changes=settings, partition_change='factory 1700K -> 2560K'), indent=2))
(p / 'identity.json').write_text(json.dumps(dict(
    label='DIAGNOSTIC_NOT_FOR_MEASUREMENT', created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    baseline_files=len(manifest), baseline_mismatches=0, board_action='NONE'), indent=2))
print('profile ready', p, 'modified files:', changed)
