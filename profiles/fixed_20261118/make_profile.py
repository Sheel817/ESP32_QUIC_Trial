"""Create the FIXED measurement profile source tree (no device access).
Copies the frozen source set (hash-verified against profiles/tcp_tls_wifi_ps_none_20261104/source_before.json) and applies:
 (a) ngtcp2 conn_new: +7 bytes (malloc only 4-byte aligned on ESP-IDF); ngtcp2_balloc_get: reserve 0xf (same cause)
 (b) QUIC UDP socket closed in client_free() and on client_init() failure paths
 (c) build-system tweaks needed to build the private copy with the component manager disabled (same as earlier profiles)
 (d) optional TEST-ONLY cycle harness, compiled only when -DFIXED_TEST_MODE=1|2 is given (default 0 = absent).
Frozen profiles and the root tree are only read."""
from pathlib import Path
import datetime as dt, hashlib, json, shutil

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
shutil.copy2(root / 'profiles/wifi_ps_none_20261103/sdkconfig', p / 'sdkconfig')  # identical to the TCP_TLS profile sdkconfig
baseline = {rel: sha(src / rel) for rel in manifest}


def replace(rel, old, new, count=1):
    f = src / rel
    t = f.read_bytes().decode('utf-8')
    crlf = '\r\n' in t
    if crlf:
        t = t.replace('\r\n', '\n')
    assert t.count(old) == count, (rel, old, t.count(old))
    t = t.replace(old, new)
    f.write_bytes((t.replace('\n', '\r\n') if crlf else t).encode('utf-8'))


# ---- (a) ngtcp2 alignment fixes
N = 'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c'
replace(N, '  buf = ngtcp2_mem_calloc(mem, 1, buflen);',
        '  /* buflen_align() rounds lengths, buf_align() rounds addresses: when malloc returns only\n'
        '     4-byte aligned memory (ESP-IDF heap) sections start up to 7 bytes later than computed. */\n'
        '  buflen += 0x7U;\n  buf = ngtcp2_mem_calloc(mem, 1, buflen);')
B = 'components/ngtcp2/ngtcp2/lib/ngtcp2_balloc.c'
replace(B, 'sizeof(ngtcp2_memblock_hd) + 0x8u + balloc->blklen);', 'sizeof(ngtcp2_memblock_hd) + 0xfu + balloc->blklen);')

# ---- (b) QUIC socket leak
S = 'main/ngtcp2_sample.c'
replace(S, '#include <stdlib.h>\n', '#include <stdlib.h>\n#include <unistd.h>\n')
replace(S, '''  if (connect_sock((struct sockaddr *)&local_addr, &local_addrlen, c->fd,
                   (struct sockaddr *)&remote_addr, remote_addrlen) != 0) {
    return -1;
  }''', '''  if (connect_sock((struct sockaddr *)&local_addr, &local_addrlen, c->fd,
                   (struct sockaddr *)&remote_addr, remote_addrlen) != 0) {
    close(c->fd);
    c->fd = -1;
    return -1;
  }''')
replace(S, '''  if (client_ssl_init(c) != 0) {
    return -1;
  }

  if (client_quic_init(c, (struct sockaddr *)&remote_addr, remote_addrlen,
                       (struct sockaddr *)&local_addr, local_addrlen) != 0) {
    return -1;
  }''', '''  if (client_ssl_init(c) != 0) {
    close(c->fd);
    c->fd = -1;
    return -1;
  }

  if (client_quic_init(c, (struct sockaddr *)&remote_addr, remote_addrlen,
                       (struct sockaddr *)&local_addr, local_addrlen) != 0) {
    close(c->fd);
    c->fd = -1;
    return -1;
  }''')
replace(S, '  SSL_free(c->ssl);\n  SSL_CTX_free(c->ssl_ctx);\n}', '''  SSL_free(c->ssl);
  SSL_CTX_free(c->ssl_ctx);
  /* The read watcher was stopped by the caller; release the UDP socket (lwIP has a small fixed socket table). */
  if (c->fd >= 0) {
    close(c->fd);
    c->fd = -1;
  }
}''')

# ---- (c) build-system tweaks (component manager disabled for the private copy)
replace('CMakeLists.txt', 'include($ENV{IDF_PATH}/tools/cmake/project.cmake)', '''# Private copy: use existing dependency copies without dependency resolution (same approach as earlier profiles).
set(EXTRA_COMPONENT_DIRS "${CMAKE_SOURCE_DIR}/managed_components"
    "$ENV{IDF_PATH}/examples/common_components/protocol_examples_common")
set(PROJECT_VER "3c8c7a3-dirty-FIXED_20261118")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)''')
replace('main/CMakeLists.txt', '        wolfssl \n', '        wolfssl__wolfssl \n')
replace('main/CMakeLists.txt', '        protocol_examples_common', '        protocol_examples_common\n        esp-idf-lib__dht\n        espressif__cjson')
replace('components/ngtcp2/CMakeLists.txt', 'REQUIRES wolfssl)', 'REQUIRES wolfssl__wolfssl)')
replace('managed_components/esp-idf-lib__dht/CMakeLists.txt', ' esp_idf_lib_helpers', ' esp-idf-lib__esp_idf_lib_helpers', count=3)

# ---- (d) optional test-only cycle harness (absent unless FIXED_TEST_MODE is set at configure time)
replace('main/CMakeLists.txt', 'message(STATUS "Measurement transport: ${DEMO_TRANSPORT}")', '''message(STATUS "Measurement transport: ${DEMO_TRANSPORT}")
set(FIXED_TEST_MODE "0" CACHE STRING "TEST ONLY: 0=measurement image (default), 1=reboot cycles, 2=soft reconnect cycles")
set(FIXED_TEST_CYCLES "30" CACHE STRING "TEST ONLY: cycles")
set(FIXED_TEST_RUN_ID "f0" CACHE STRING "TEST ONLY: NVS namespace suffix")''')
replace('main/CMakeLists.txt', '    DEMO_WIFI_PS_NONE=$<BOOL:${DEMO_WIFI_PS_NONE}>)', '''    DEMO_WIFI_PS_NONE=$<BOOL:${DEMO_WIFI_PS_NONE}>
    FIXED_TEST_MODE=${FIXED_TEST_MODE} FIXED_TEST_CYCLES=${FIXED_TEST_CYCLES} "FIXED_TEST_RUN_ID=\\"${FIXED_TEST_RUN_ID}\\"")''')
replace(S, '    ev_default_loop_init();\n', '''#if FIXED_TEST_MODE == 2
    { static bool test_loop_ready; if (!test_loop_ready) { ev_default_loop_init(); test_loop_ready = true; } }
#else
    ev_default_loop_init();
#endif
''')
M = 'main/quic_demo_main.c'
replace(M, '#include "esp_wifi.h"', '#include "esp_wifi.h"\n#include "nvs.h"\n#include "esp_rom_sys.h"')
cycle = r'''#if FIXED_TEST_MODE
/* TEST ONLY cycle task (not present in measurement images): QUIC connect, wait for handshake, then reboot (mode 1)
 * or close and reconnect (mode 2). Counters live in NVS so crashes (reboot) are counted: started - passed - failed. */
static void test_cycle_task(void *argument)
{
    (void)argument;
    nvs_handle_t h;
    char ns[16];
    snprintf(ns, sizeof(ns), "tf%s", FIXED_TEST_RUN_ID);
    uint32_t started = 0, passed = 0, failed = 0, init_failed = 0;
    ESP_ERROR_CHECK(nvs_open(ns, NVS_READWRITE, &h));
    (void)nvs_get_u32(h, "started", &started);
    (void)nvs_get_u32(h, "passed", &passed);
    (void)nvs_get_u32(h, "failed", &failed);
    (void)nvs_get_u32(h, "initfail", &init_failed);
    esp_rom_printf("TEST RESUME run=%s mode=%d started=%u passed=%u failed=%u init_failed=%u crashed_so_far=%d\n", FIXED_TEST_RUN_ID,
                   FIXED_TEST_MODE, (unsigned)started, (unsigned)passed, (unsigned)failed, (unsigned)init_failed,
                   (int)started - (int)passed - (int)failed);
    char port_text[16];
    snprintf(port_text, sizeof(port_text), "%u", (unsigned)server_info.port);
    quic_client_config_t quic_config = {.hostname = server_info.pHostName, .port = port_text, .alpn = server_info.pAlpn};
    while (started < FIXED_TEST_CYCLES) {
        started++;
        ESP_ERROR_CHECK(nvs_set_u32(h, "started", started));
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("TEST CYCLE %u START mode=%d free_heap=%u\n", (unsigned)started, FIXED_TEST_MODE, (unsigned)esp_get_free_heap_size());
        bool init_ok = quic_client_init_with_config(&quic_config) == 0;
        bool ok = init_ok && wait_for_quic_ready();
        if (ok) {
            vTaskDelay(pdMS_TO_TICKS(1000));
            passed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "passed", passed));
        } else {
            failed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "failed", failed));
            if (!init_ok) {
                init_failed++;
                ESP_ERROR_CHECK(nvs_set_u32(h, "initfail", init_failed));
            }
        }
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("TEST CYCLE %u %s\n", (unsigned)started, ok ? "PASS" : (init_ok ? "FAIL_HANDSHAKE_TIMEOUT" : "FAIL_CLIENT_INIT"));
        if (FIXED_TEST_MODE == 1) {
            esp_rom_printf("TEST REBOOTING\n");
            vTaskDelay(pdMS_TO_TICKS(200));
            esp_restart();
        }
        quic_client_cleanup();
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
    esp_rom_printf("TEST COMPLETE run=%s mode=%d cycles=%d started=%u passed=%u failed=%u init_failed=%u crashed=%d free_heap=%u\n",
                   FIXED_TEST_RUN_ID, FIXED_TEST_MODE, FIXED_TEST_CYCLES, (unsigned)started, (unsigned)passed, (unsigned)failed,
                   (unsigned)init_failed, (int)started - (int)passed - (int)failed, (unsigned)esp_get_free_heap_size());
    nvs_close(h);
    vTaskDelete(NULL);
}
#endif

void app_main(void)'''
replace(M, 'void app_main(void)', cycle)
replace(M, '        quic_sensor_task,\n        "quic_dht11",', '#if FIXED_TEST_MODE\n        test_cycle_task,\n#else\n        quic_sensor_task,\n#endif\n        "quic_dht11",')

changed = [rel for rel in manifest if sha(src / rel) != baseline[rel]]
(p / 'changed_source_files.json').write_text(json.dumps(dict(
    modified_vs_frozen=changed, partition='unchanged (factory 1700K)',
    sdkconfig='identical to frozen sdkconfig (no heap poisoning, no stack check)', QUIET_MEASUREMENT=1), indent=2))
(p / 'identity.json').write_text(json.dumps(dict(
    label='FIXED_PROFILE', created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    baseline_files=len(manifest), baseline_mismatches=0, board_action='NONE'), indent=2))
print('profile ready; modified files:', changed)
