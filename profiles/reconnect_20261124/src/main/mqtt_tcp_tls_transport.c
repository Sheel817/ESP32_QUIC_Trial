#include "mqtt_tcp_tls_transport.h"
#include "tls_negotiation.h"
#include "esp_log.h"
#include "freertos/task.h"
#include "lwip/sockets.h"
#include "lwip/tcp.h"
#include "lwip/api.h"
#include "lwip/tcpip.h"
#include "lwip/priv/sockets_priv.h"
#include "freertos/semphr.h"
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <string.h>

#define TLS_IDLE_TIMEOUT_US (60LL * 1000000)
static const char *TAG = "TCP_TLS";
/* Accessed only by the MQTT application task, never the QUIC event task. */
static struct {
    int fd;
    WOLFSSL_CTX *ctx;
    WOLFSSL *ssl;
    bool initialized;
    bool connected;
    uint32_t timeout_ms;
    int64_t last_io_us;
    uint8_t rx[2048];  // Stable wolfSSL_read retry buffer, independent of MQTT.
    size_t rx_length;
    size_t rx_position;
} client = { .fd = -1 };

/* Absolute deadlines are retained across EINTR, short I/O and TLS retries. */
static int wait_socket(int tls_error, int64_t deadline)
{
    while (esp_timer_get_time() < deadline) {
        int64_t left = deadline - esp_timer_get_time();
        if (left <= 0) break;
        struct timeval tv = { .tv_sec = left / 1000000,
                              .tv_usec = left % 1000000 };
        fd_set readfds, writefds;
        FD_ZERO(&readfds);
        FD_ZERO(&writefds);
        if (tls_error == WOLFSSL_ERROR_WANT_WRITE) FD_SET(client.fd, &writefds);
        else FD_SET(client.fd, &readfds);
        int result = select(client.fd + 1, &readfds, &writefds, NULL, &tv);
        if (result >= 0) return result;
        if (errno != EINTR) return -1;
    }
    return 0;
}

static int failed(const char *operation, int error)
{
    ESP_LOGE(TAG, "%s failed: error=%d errno=%d", operation, error, errno);
    client.connected = false;
    return -1;
}

bool tcp_tls_client_is_connected(void) { return client.connected; }

#if FIXED_CT_MODE
volatile int64_t g_ct_tcp_t0_us, g_ct_tcp_connect_done_us, g_ct_tls_done_us;
#endif

void tcp_tls_client_cleanup(void)
{
    if (client.ssl && client.connected) {
        int64_t deadline = esp_timer_get_time() + 250000;
        for (;;) {
            int result = wolfSSL_shutdown(client.ssl);
            if (result == WOLFSSL_SUCCESS) break;
            int error = wolfSSL_get_error(client.ssl, result);
            if (result == WOLFSSL_SHUTDOWN_NOT_DONE) error = WOLFSSL_ERROR_WANT_READ;
            if (error != WOLFSSL_ERROR_WANT_READ && error != WOLFSSL_ERROR_WANT_WRITE) break;
            if (wait_socket(error, deadline) <= 0) break;
        }
    }
    client.connected = false;
    if (client.ssl) wolfSSL_free(client.ssl);
    if (client.ctx) wolfSSL_CTX_free(client.ctx);
    if (client.fd >= 0) close(client.fd);
    if (client.initialized) wolfSSL_Cleanup();
    memset(&client, 0, sizeof(client));
    client.fd = -1;
}

int tcp_tls_client_connect(const ServerInfo_t *server, uint32_t timeout_ms)
{
    tcp_tls_client_cleanup();
    if (!server || !server->pHostName || !server->pAlpn || timeout_ms == 0 ||
        strcmp(server->pAlpn, "mqtt") != 0) return -1;
#if FIXED_CT_MODE
    g_ct_tcp_t0_us = esp_timer_get_time(); g_ct_tcp_connect_done_us = 0; g_ct_tls_done_us = 0;
#endif
    client.timeout_ms = timeout_ms;
    int64_t deadline = esp_timer_get_time() + (int64_t)timeout_ms * 1000;
    struct sockaddr_in address = { .sin_family = AF_INET,
                                  .sin_port = htons(server->port) };
    if (inet_pton(AF_INET, server->pHostName, &address.sin_addr) != 1) goto failure;
    client.fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (client.fd < 0) goto failure;
    int flags = fcntl(client.fd, F_GETFL, 0);
    if (flags < 0 || fcntl(client.fd, F_SETFL, flags | O_NONBLOCK) < 0) goto failure;
    int enabled = 1;
    socklen_t option_length = sizeof(enabled);
    if (setsockopt(client.fd, IPPROTO_TCP, TCP_NODELAY, &enabled, sizeof(enabled)) != 0 ||
        getsockopt(client.fd, IPPROTO_TCP, TCP_NODELAY, &enabled, &option_length) != 0 ||
        enabled != 1) goto failure;
    ESP_LOGI(TAG, "TCP_NODELAY=%d; connect/I/O timeout=%lu ms", enabled, (unsigned long)timeout_ms);
    if (connect(client.fd, (struct sockaddr *)&address, sizeof(address)) != 0) {
        if (errno != EINPROGRESS && errno != EWOULDBLOCK && errno != EALREADY) goto failure;
        if (wait_socket(WOLFSSL_ERROR_WANT_WRITE, deadline) <= 0) goto failure;
        int error = 0;
        socklen_t length = sizeof(error);
        if (getsockopt(client.fd, SOL_SOCKET, SO_ERROR, &error, &length) != 0 || error != 0) goto failure;
    }
#if FIXED_CT_MODE
    g_ct_tcp_connect_done_us = esp_timer_get_time();
#endif
    if (wolfSSL_Init() != WOLFSSL_SUCCESS) goto failure;
    client.initialized = true;
    client.ctx = wolfSSL_CTX_new(wolfTLSv1_3_client_method());
    if (!client.ctx) goto failure;
    // Match the existing QUIC experiment, which uses VERIFY_NONE as well.
    wolfSSL_CTX_set_verify(client.ctx, WOLFSSL_VERIFY_NONE, NULL);
    if (wolfSSL_CTX_set_cipher_list(client.ctx, "TLS13-AES128-GCM-SHA256") != WOLFSSL_SUCCESS) goto failure;
    client.ssl = wolfSSL_new(client.ctx);
    if (!client.ssl) goto failure;
    if (wolfSSL_set_fd(client.ssl, client.fd) != WOLFSSL_SUCCESS ||
        wolfSSL_UseALPN(client.ssl, "mqtt", 4, WOLFSSL_ALPN_FAILED_ON_MISMATCH) != WOLFSSL_SUCCESS) goto failure;
    for (;;) {
        if (esp_timer_get_time() >= deadline) {
            failed("TLS handshake timeout", ETIMEDOUT);
            goto failure;
        }
        int result = wolfSSL_connect(client.ssl);
        if (result == WOLFSSL_SUCCESS) {
#if FIXED_CT_MODE
            g_ct_tls_done_us = esp_timer_get_time();
#endif
            break;
        }
        int error = wolfSSL_get_error(client.ssl, result);
        if ((error != WOLFSSL_ERROR_WANT_READ && error != WOLFSSL_ERROR_WANT_WRITE) ||
            wait_socket(error, deadline) <= 0) {
            failed("TLS handshake", error);
            goto failure;
        }
    }
    if (!tls_report_negotiation("TCP_TLS", client.ssl)) {
        ESP_LOGE(TAG, "Required TLS1.3 / TLS_AES_128_GCM_SHA256 / mqtt was not negotiated");
        goto failure;
    }
    client.connected = true;
    client.last_io_us = esp_timer_get_time();
    ESP_LOGI(TAG, "Connected to %s:%u", server->pHostName, (unsigned)server->port);
    return 0;
failure:
    ESP_LOGE(TAG, "Connection setup failed or timed out (errno=%d)", errno);
    tcp_tls_client_cleanup();
    return -1;
}

static int write_packet(const uint8_t *data, size_t length)
{
    if (!client.connected || !data || length == 0 || length > INT_MAX) return -1;
    int64_t deadline = esp_timer_get_time() + (int64_t)client.timeout_ms * 1000;
    size_t sent = 0;
    while (sent < length) {
        if (esp_timer_get_time() >= deadline) return failed("TLS write timeout", ETIMEDOUT);
        int result = wolfSSL_write(client.ssl, data + sent, (int)(length - sent));
        if (result > 0) {
            sent += (size_t)result;
            client.last_io_us = esp_timer_get_time();
            continue;
        }
        int error = wolfSSL_get_error(client.ssl, result);
        // On WANT_*, retry the identical pointer and length. Do not requeue a
        // partially transmitted MQTT packet on failure: disconnect instead.
        if ((error != WOLFSSL_ERROR_WANT_READ && error != WOLFSSL_ERROR_WANT_WRITE) ||
            wait_socket(error, deadline) <= 0) return failed("TLS write", error);
    }
    return 0;
}

static int read_data(uint8_t *buffer, size_t capacity, size_t *received)
{
    if (!buffer || !received || capacity == 0) return -1;
    *received = 0;
    if (!client.connected) return -1;
    if (client.rx_position == client.rx_length) {
        int64_t deadline = esp_timer_get_time() + 100000;
        for (;;) {
            int result = wolfSSL_read(client.ssl, client.rx, sizeof(client.rx));
            if (result > 0) {
                client.rx_length = (size_t)result;
                client.rx_position = 0;
                client.last_io_us = esp_timer_get_time();
                break;
            }
            int error = wolfSSL_get_error(client.ssl, result);
            if (error == WOLFSSL_ERROR_WANT_READ) return -2; // Idle is retryable.
            if (error == WOLFSSL_ERROR_WANT_WRITE) {
                int ready = wait_socket(error, deadline);
                if (ready > 0) continue;
                if (ready == 0) return -2;
            }
            return failed("TLS read / peer disconnected", error);
        }
    }
    size_t available = client.rx_length - client.rx_position;
    *received = available < capacity ? available : capacity;
    memcpy(buffer, client.rx + client.rx_position, *received);
    client.rx_position += *received;
    return 0;
}

int tcp_tls_client_process(void)
{
    // Keep the application process call's existing 5 ms + 1 ms yields.
    vTaskDelay(pdMS_TO_TICKS(5));
    vTaskDelay(pdMS_TO_TICKS(1));
    if (client.connected && esp_timer_get_time() - client.last_io_us > TLS_IDLE_TIMEOUT_US)
        return failed("TLS idle timeout", ETIMEDOUT);
    return client.connected ? 0 : -1;
}

/* ---- RECONNECT PROFILE: TCP socket diagnostics ----------------------------------------------------
 * lwIP has no TCP_INFO/SIOCOUTQ. The TCP control block is read on the tcpip thread (tcpip_callback),
 * so the values are consistent with the stack. unacked = snd_nxt - lastack (sent, not acknowledged),
 * unsent = snd_lbb - snd_nxt (queued by the application, not yet sent). rto is in 500 ms ticks. */
static struct {
    int fd;
    int ok;
    uint32_t state, unacked, unsent, snd_buf, snd_wnd, rcv_wnd, nrtx, rto, queuelen, persist_backoff, has_unacked, has_unsent;
} s_tcpd;
static SemaphoreHandle_t s_tcpd_done;

static void tcpd_read(void *arg)
{
    (void)arg;
    s_tcpd.ok = 0;
    struct lwip_sock *sock = lwip_socket_dbg_get_socket(s_tcpd.fd);
    if (sock && sock->conn && NETCONNTYPE_GROUP(netconn_type(sock->conn)) == NETCONN_TCP && sock->conn->pcb.tcp) {
        struct tcp_pcb *pcb = sock->conn->pcb.tcp;
        s_tcpd.state = pcb->state;
        s_tcpd.unacked = pcb->snd_nxt - pcb->lastack;
        s_tcpd.unsent = pcb->snd_lbb - pcb->snd_nxt;
        s_tcpd.snd_buf = pcb->snd_buf;
        s_tcpd.snd_wnd = pcb->snd_wnd;
        s_tcpd.rcv_wnd = pcb->rcv_wnd;
        s_tcpd.nrtx = pcb->nrtx;
        s_tcpd.rto = (uint32_t)pcb->rto;
        s_tcpd.queuelen = pcb->snd_queuelen;
        s_tcpd.persist_backoff = pcb->persist_backoff;
        s_tcpd.has_unacked = pcb->unacked != NULL;
        s_tcpd.has_unsent = pcb->unsent != NULL;
        s_tcpd.ok = 1;
    }
    xSemaphoreGive(s_tcpd_done);
}

int tcp_tls_client_diag(char *out, size_t size)
{
    int64_t now = esp_timer_get_time();
    int rx_avail = -1;
    if (client.fd >= 0) (void)ioctl(client.fd, FIONREAD, &rx_avail);
    int n = snprintf(out, size, "tcp_connected=%d last_io_age_ms=%lld rx_avail=%d tls_pending=%d app_rx_left=%u",
                     client.connected, client.connected ? (long long)((now - client.last_io_us) / 1000) : -1LL, rx_avail,
                     client.ssl ? wolfSSL_pending(client.ssl) : -1, (unsigned)(client.rx_length - client.rx_position));
    if (n < 0 || (size_t)n >= size || client.fd < 0) return n;
    if (s_tcpd_done == NULL) s_tcpd_done = xSemaphoreCreateBinary();
    s_tcpd.fd = client.fd;
    if (s_tcpd_done == NULL || tcpip_callback(tcpd_read, NULL) != ERR_OK) {
        return n + snprintf(out + n, size - n, " tcp_pcb=unavailable");
    }
    /* The callback writes only the static s_tcpd, so a late completion cannot corrupt the stack. */
    if (xSemaphoreTake(s_tcpd_done, pdMS_TO_TICKS(500)) != pdTRUE) {
        return n + snprintf(out + n, size - n, " tcp_pcb=timeout");
    }
    if (!s_tcpd.ok) return n + snprintf(out + n, size - n, " tcp_pcb=none");
    return n + snprintf(out + n, size - n,
                        " tcp_state=%u unacked=%u unsent=%u queuelen=%u snd_buf=%u snd_wnd=%u rcv_wnd=%u nrtx=%u rto_ticks=%u persist=%u unacked_q=%u unsent_q=%u",
                        (unsigned)s_tcpd.state, (unsigned)s_tcpd.unacked, (unsigned)s_tcpd.unsent, (unsigned)s_tcpd.queuelen,
                        (unsigned)s_tcpd.snd_buf, (unsigned)s_tcpd.snd_wnd, (unsigned)s_tcpd.rcv_wnd, (unsigned)s_tcpd.nrtx,
                        (unsigned)s_tcpd.rto, (unsigned)s_tcpd.persist_backoff, (unsigned)s_tcpd.has_unacked,
                        (unsigned)s_tcpd.has_unsent);
}

BaseType_t mqtt_tcp_tls_transport_init(NetworkContext_t *context,
    const ServerInfo_t *server, const MQTTQUICConfig_t *config)
{
    if (mqtt_quic_transport_init(context, server, config) != pdPASS) return pdFAIL;
    context->write_packet = write_packet;
    context->read_data = read_data;
    context->is_connected = tcp_tls_client_is_connected;
    return pdPASS;
}
