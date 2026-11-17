"""Add finer heap-integrity checkpoints inside client_init / client_ssl_init / client_quic_init (diagnostic image rb2)."""
from pathlib import Path
f = Path(__file__).parent / 'src/main/ngtcp2_sample.c'
t = f.read_text(encoding='utf-8')
def rep(old, new):
    global t
    assert t.count(old) == 1, old
    t = t.replace(old, new)
rep('  memset(c, 0, sizeof(*c));\n\n  ngtcp2_ccerr_default(&c->last_error);', '  crash_diag_checkpoint("client_init_start");\n  memset(c, 0, sizeof(*c));\n\n  ngtcp2_ccerr_default(&c->last_error);')
rep('  if (c->fd == -1) {\n    return -1;\n  }\n', '  crash_diag_checkpoint("after_create_sock");\n  if (c->fd == -1) {\n    return -1;\n  }\n')
rep('  memcpy(&c->local_addr, &local_addr, sizeof(c->local_addr));', '  crash_diag_checkpoint("after_connect_sock");\n  memcpy(&c->local_addr, &local_addr, sizeof(c->local_addr));')
rep('  c->ssl_ctx = SSL_CTX_new(TLS_client_method());\n', '  c->ssl_ctx = SSL_CTX_new(TLS_client_method());\n  crash_diag_checkpoint("after_SSL_CTX_new");\n')
rep('  wolfSSL_CTX_UseSNI(c->ssl_ctx, WOLFSSL_SNI_HOST_NAME', '  crash_diag_checkpoint("after_configure_client_context");\n  wolfSSL_CTX_UseSNI(c->ssl_ctx, WOLFSSL_SNI_HOST_NAME')
rep('  c->ssl = SSL_new(c->ssl_ctx);\n', '  crash_diag_checkpoint("after_UseSNI_set_verify");\n  c->ssl = SSL_new(c->ssl_ctx);\n  crash_diag_checkpoint("after_SSL_new");\n')
rep('  SSL_set_connect_state(c->ssl);\n', '  SSL_set_connect_state(c->ssl);\n  crash_diag_checkpoint("after_set_connect_state");\n')
rep('  if (!numeric_host(g_config.hostname)) {\n    SSL_set_tlsext_host_name', '  crash_diag_checkpoint("after_set_alpn");\n  if (!numeric_host(g_config.hostname)) {\n    SSL_set_tlsext_host_name')
rep('  if (client_ssl_init(c) != 0) {\n    return -1;\n  }\n', '  if (client_ssl_init(c) != 0) {\n    return -1;\n  }\n  crash_diag_checkpoint("after_client_ssl_init");\n')
rep('  rv =\n    ngtcp2_conn_client_new(&c->conn,', '  crash_diag_checkpoint("before_ngtcp2_conn_client_new");\n  rv =\n    ngtcp2_conn_client_new(&c->conn,')
rep('  ngtcp2_conn_set_tls_native_handle(c->conn, c->ssl);\n\n  return 0;', '  crash_diag_checkpoint("after_ngtcp2_conn_client_new");\n  ngtcp2_conn_set_tls_native_handle(c->conn, c->ssl);\n\n  return 0;')
f.write_text(t, encoding='utf-8')
print('refine1 applied')
