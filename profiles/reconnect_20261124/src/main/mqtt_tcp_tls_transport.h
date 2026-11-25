#ifndef MQTT_TCP_TLS_TRANSPORT_H
#define MQTT_TCP_TLS_TRANSPORT_H
#include "mqtt_quic_transport.h"
int tcp_tls_client_connect(const ServerInfo_t *server, uint32_t timeout_ms);
bool tcp_tls_client_is_connected(void);
int tcp_tls_client_process(void);
void tcp_tls_client_cleanup(void);
int tcp_tls_client_diag(char *out, size_t size);  // RECONNECT PROFILE diagnostics
BaseType_t mqtt_tcp_tls_transport_init(NetworkContext_t *context,
    const ServerInfo_t *server, const MQTTQUICConfig_t *config);
#endif
