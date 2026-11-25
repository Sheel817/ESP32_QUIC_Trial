#ifndef HTTP3_CLIENT_H
#define HTTP3_CLIENT_H
#include <stddef.h>
#include <stdint.h>

#ifndef HTTP3_SERVER_HOST
#define HTTP3_SERVER_HOST "192.168.137.1"
#endif
#ifndef HTTP3_SERVER_PORT
#define HTTP3_SERVER_PORT "4433"
#endif

typedef struct {
    const char *host, *port, *authority, *path;
    uint32_t timeout_ms;
} http3_client_config_t;

typedef struct {
    int status_code;
    size_t header_count;
    uint64_t body_bytes;
    double handshake_ms, first_header_ms, total_ms;
    uint32_t free_heap_min;
} http3_result_t;

int http3_client_get(const http3_client_config_t *cfg, http3_result_t *out);
void http3_client_task(void *arg);
#endif
