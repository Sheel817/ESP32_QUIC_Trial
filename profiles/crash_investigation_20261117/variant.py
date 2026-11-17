"""Apply/revert diagnostic variants to src. Usage: python -I variant.py macros|align|revert-macros|revert-align"""
import sys
from pathlib import Path
p = Path(__file__).parent / 'src'
def edit(rel, old, new):
    f = p / rel; t = f.read_text(encoding='utf-8'); assert t.count(old) == 1, (rel, old, t.count(old)); f.write_text(t.replace(old, new), encoding='utf-8')
M_OLD = 'add_compile_definitions(WOLFSSL_QUIC MICRO_SESSION_CACHE HAVE_ALPN OPENSSL_ALL)'
M_NEW = ('add_compile_definitions(WOLFSSL_QUIC MICRO_SESSION_CACHE HAVE_ALPN OPENSSL_ALL\n'
         '    HAVE_AESCCM HAVE_AES_ECB HAVE_CHACHA HAVE_POLY1305 WOLFSSL_KEY_GEN WOLFSSL_SNI WOLFSSL_RAND\n'
         '    WOLFSSL_HAVE_EVP_PKEY WOLFSSL_EVP_AES WOLFSSL_ADVANCED_EXTENSIONS WOLFSSL_ESPIDF) # DIAG variant: same wolfSSL macros for every unit')
A_OLD = '  buf = ngtcp2_mem_calloc(mem, 1, buflen);\n  if (buf == NULL) {\n    return NGTCP2_ERR_NOMEM;\n  }\n  crash_diag_note('
A_NEW = '  buf = ngtcp2_mem_calloc(mem, 1, buflen + 0x7); /* DIAG variant: slack for a base address that is only 4-byte aligned */\n  if (buf == NULL) {\n    return NGTCP2_ERR_NOMEM;\n  }\n  crash_diag_note('
N = 'components/ngtcp2/ngtcp2/lib/ngtcp2_conn.c'
{'macros': lambda: edit('CMakeLists.txt', M_OLD, M_NEW), 'revert-macros': lambda: edit('CMakeLists.txt', M_NEW, M_OLD),
 'align': lambda: edit(N, A_OLD, A_NEW), 'revert-align': lambda: edit(N, A_NEW, A_OLD)}[sys.argv[1]]()
print('ok', sys.argv[1])
