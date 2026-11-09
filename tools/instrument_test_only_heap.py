from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'profiles/test_only_heap_20261106';s=p/'src'
assert (p/'identity.json').exists()
def replace(rel,old,new):
    f=s/rel;t=f.read_text();assert t.count(old)==1,(rel,old);f.write_text(t.replace(old,new),encoding='utf-8')
replace('CMakeLists.txt','include($ENV{IDF_PATH}/tools/cmake/project.cmake)', '''# TEST_ONLY: use existing private dependency copies without dependency resolution.
set(EXTRA_COMPONENT_DIRS "${CMAKE_SOURCE_DIR}/managed_components"
    "$ENV{IDF_PATH}/examples/common_components/protocol_examples_common")
set(PROJECT_VER "3c8c7a3-dirty-TEST_ONLY")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)''')
replace('main/CMakeLists.txt','        protocol_examples_common','        protocol_examples_common\n        test_only_heap_diag')
replace('components/ngtcp2/CMakeLists.txt','REQUIRES wolfssl)','REQUIRES wolfssl test_only_heap_diag)')
replace('main/ngtcp2_sample.c','#include "tls_negotiation.h"','#include "tls_negotiation.h"\n#include "test_only_heap_diag.h"')
replace('main/ngtcp2_sample.c','    nwrite = ngtcp2_conn_writev_stream(','''    test_only_heap_check(TEST_ONLY_BEFORE_WRITE, c->conn, c);
    nwrite = ngtcp2_conn_writev_stream(''')
replace('main/quic_demo_main.c','#include "esp_wifi.h"','#include "esp_wifi.h"\n#include "test_only_heap_diag.h"')
replace('main/quic_demo_main.c','void app_main(void)\n{','void app_main(void)\n{\n    test_only_heap_banner();')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c','#include "ngtcp2_conn.h"','#include "ngtcp2_conn.h"\n#include "test_only_heap_diag.h"')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c','  pktns_init(*ppktns, pktns_id, rst, cc, initial_pkt_num, log, qlog,','  test_only_heap_trace(TEST_ONLY_PKTNS_ALLOC, *ppktns, mem, (uint32_t)pktns_id);\n  pktns_init(*ppktns, pktns_id, rst, cc, initial_pkt_num, log, qlog,')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c','  ngtcp2_pktns *pktns = *ppktns;\n  uint64_t bytes_in_flight;','  ngtcp2_pktns *pktns = *ppktns;\n  uint64_t bytes_in_flight;\n\n  test_only_heap_check(TEST_ONLY_CLEANUP_ENTRY, pktns, conn);')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c','  pktns_free(pktns, mem);\n\n  ngtcp2_mem_free(mem, pktns);','  pktns_free(pktns, mem);\n\n  test_only_heap_check(TEST_ONLY_BEFORE_FINAL_FREE, pktns, mem);\n  ngtcp2_mem_free(mem, pktns);')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c','#include "ngtcp2_mem.h"','#include "ngtcp2_mem.h"\n#include "test_only_heap_diag.h"')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c','  return mem->malloc(size, mem->user_data);','  void *ptr = mem->malloc(size, mem->user_data);\n  test_only_heap_trace(TEST_ONLY_ALLOC, ptr, mem, (uint32_t)size);\n  return ptr;')
# The non-MEMDEBUG wrapper only. Original allocator call and ownership unchanged.
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c','void ngtcp2_mem_free(const ngtcp2_mem *mem, void *ptr) {\n  mem->free(ptr, mem->user_data);\n}', '''void ngtcp2_mem_free(const ngtcp2_mem *mem, void *ptr) {
  test_only_heap_trace(TEST_ONLY_FREE_BEGIN, ptr, mem, 0);
  mem->free(ptr, mem->user_data);
  test_only_heap_trace(TEST_ONLY_FREE_END, ptr, mem, 0);
}''')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c','  return mem->calloc(nmemb, size, mem->user_data);','  void *ptr = mem->calloc(nmemb, size, mem->user_data);\n  test_only_heap_trace(TEST_ONLY_CALLOC, ptr, (const void *)(uintptr_t)nmemb, (uint32_t)size);\n  return ptr;')
replace('components/ngtcp2/ngtcp2/lib/ngtcp2_mem.c','  return mem->realloc(ptr, size, mem->user_data);','  test_only_heap_trace(TEST_ONLY_REALLOC_BEGIN, ptr, mem, (uint32_t)size);\n  void *result = mem->realloc(ptr, size, mem->user_data);\n  test_only_heap_trace(TEST_ONLY_REALLOC_END, result, ptr, (uint32_t)size);\n  return result;')
config=p/'sdkconfig';t=config.read_text()
settings={'CONFIG_ESP_COREDUMP_ENABLE_TO_NONE':None,'CONFIG_ESP_COREDUMP_ENABLE_TO_UART':'y','CONFIG_ESP_COREDUMP_CAPTURE_DRAM':'y','CONFIG_ESP_COREDUMP_STACK_SIZE':'2048','CONFIG_ESP_COREDUMP_DECODE_DISABLE':'y'}
for k,v in settings.items():
    import re
    t=re.sub(r'^'+k+r'=.*\n|^# '+k+r' is not set\n','',t,flags=re.M)
    t+=f'{k}={v}\n' if v is not None else f'# {k} is not set\n'
config.write_text(t,encoding='utf-8')
(p/'intended_config_changes.json').write_text(json.dumps(settings,indent=2))
print('TEST_ONLY instrumentation complete; no firmware execution')
