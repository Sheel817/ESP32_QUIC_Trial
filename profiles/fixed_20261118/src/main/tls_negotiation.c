#include "tls_negotiation.h"
#include "esp_log.h"
#include <string.h>

bool tls_report_negotiation(const char *transport, WOLFSSL *ssl)
{
    char *alpn = NULL;
    unsigned short alpn_length = 0;
    int alpn_result = wolfSSL_ALPN_GetProtocol(ssl, &alpn, &alpn_length);
    int suite = wolfSSL_get_current_cipher_suite(ssl);
    int verify = wolfSSL_get_verify_mode(ssl);
    const char *cipher = wolfSSL_get_cipher_name_iana_from_suite(
        (byte)((unsigned)suite >> 8), (byte)suite);
    ESP_LOGI("TLS", "%s negotiated TLS=%s cipher=%s wolfSSL_cipher=%s suite=0x%04x ALPN=%.*s certificate_verification=%s (mode=%d)",
             transport, wolfSSL_get_version(ssl), cipher, wolfSSL_get_cipher_name(ssl),
             (unsigned)suite, alpn ? (int)alpn_length : 0, alpn ? alpn : "",
             verify == WOLFSSL_VERIFY_NONE ? "NONE" : "ENABLED", verify);
    return wolfSSL_version(ssl) == 0x0304 && (suite & 0xffff) == 0x1301 &&
           alpn_result == WOLFSSL_SUCCESS && alpn_length == 4 &&
           alpn != NULL && memcmp(alpn, "mqtt", 4) == 0;
}
