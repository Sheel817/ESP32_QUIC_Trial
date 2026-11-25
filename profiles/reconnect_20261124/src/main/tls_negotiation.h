#ifndef TLS_NEGOTIATION_H
#define TLS_NEGOTIATION_H
#include <stdbool.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/ssl.h>
bool tls_report_negotiation(const char *transport, WOLFSSL *ssl);
#endif
