"""rb3: confirm the suspected cause. Print the alignment of the ngtcp2_conn allocation and checkpoint right after the client available_versions write."""
from pathlib import Path
p = Path(__file__).parent / 'src'
def edit(rel, old, new):
    f = p / rel; t = f.read_text(encoding='utf-8'); assert t.count(old) == 1, (rel, old); f.write_text(t.replace(old, new), encoding='utf-8')
edit('components/crash_diag/include/crash_diag.h', 'void crash_diag_stacks(const char *stage);', 'void crash_diag_stacks(const char *stage);
void crash_diag_note(const char *tag, unsigned a, unsigned b, unsigned c);')
edit('components/crash_diag/crash_diag.c', 'void crash_diag_stacks(const char *stage)
{', 'void crash_diag_note(const char *tag, unsigned a, unsigned b, unsigned c)\n{\n    esp_rom_printf("DIAG NOTE %s %u %u %u\n", tag, a, b, c);\n}\n\nvoid crash_diag_stacks(const char *stage)\n{')
N = 'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c'
edit(N, '  buf = ngtcp2_mem_calloc(mem, 1, buflen);
  if (buf == NULL) {\n    return NGTCP2_ERR_NOMEM;\n  }\n',
        '  buf = ngtcp2_mem_calloc(mem, 1, buflen);
  if (buf == NULL) {\n    return NGTCP2_ERR_NOMEM;\n  }\n  crash_diag_note("conn_alloc addr_mod8 buflen sizeof_conn", (unsigned)((uintptr_t)buf & 7), (unsigned)buflen, (unsigned)sizeof(ngtcp2_conn));\n')
edit(N, '                                  &client_chosen_version, 1);
  }\n', '                                  &client_chosen_version, 1);\n    crash_diag_checkpoint("after_client_available_versions_init");\n  }\n')
print('refine2 applied')
