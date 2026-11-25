/* HTTP3 TRIAL PROFILE (build-only trial, 24 Nov 2026): minimal HTTP/3 GET over ngtcp2 v1.13.0 + nghttp3 v1.10.1
 * with wolfSSL, modelled on the ngtcp2 example client's HTTP/3 glue. One synchronous task, no libev layer:
 * UDP socket + select(), QUIC handshake, HTTP/3 control + QPACK streams, one GET request, response headers and
 * body are counted, then CONNECTION_CLOSE. Times are logged as H3_RESULT. Not flashed or run yet. */
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>

#include <ngtcp2/ngtcp2.h>
#include <ngtcp2/ngtcp2_crypto.h>
#include <ngtcp2/ngtcp2_crypto_wolfssl.h>
#include <nghttp3/nghttp3.h>
#include <openssl/ssl.h>
#include <openssl/rand.h>

#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "http3_client.h"

static const char *TAG = "H3";

typedef struct {
    ngtcp2_crypto_conn_ref conn_ref;
    int fd;
    struct sockaddr_storage local_addr, remote_addr;
    socklen_t local_addrlen, remote_addrlen;
    SSL_CTX *ssl_ctx;
    SSL *ssl;
    ngtcp2_conn *conn;
    nghttp3_conn *h3;
    ngtcp2_ccerr last_error;
    const http3_client_config_t *cfg;
    int64_t req_stream_id;
    bool handshake_done, bidi_ready, request_sent, response_done;
    int status_code;
    size_t header_count;
    uint64_t body_bytes;
    int64_t t0_us, t_handshake_us, t_request_us, t_headers_us, t_done_us;
} h3_client_t;

static uint64_t ts_ns(void) { return (uint64_t)esp_timer_get_time() * 1000; }

/* ---------------- nghttp3 callbacks ---------------- */
static int h3_consume(h3_client_t *c, int64_t stream_id, size_t n)
{
    ngtcp2_conn_extend_max_stream_offset(c->conn, stream_id, n);
    ngtcp2_conn_extend_max_offset(c->conn, n);
    return 0;
}

static int h3_recv_header(nghttp3_conn *conn, int64_t stream_id, int32_t token, nghttp3_rcbuf *name,
                          nghttp3_rcbuf *value, uint8_t flags, void *user_data, void *stream_user_data)
{
    (void)conn; (void)stream_id; (void)flags; (void)stream_user_data;
    h3_client_t *c = user_data;
    nghttp3_vec n = nghttp3_rcbuf_get_buf(name), v = nghttp3_rcbuf_get_buf(value);
    c->header_count++;
    if (token == NGHTTP3_QPACK_TOKEN__STATUS && v.len == 3) {
        c->status_code = (v.base[0] - '0') * 100 + (v.base[1] - '0') * 10 + (v.base[2] - '0');
    }
    ESP_LOGI(TAG, "header %.*s: %.*s", (int)n.len, n.base, (int)v.len, v.base);
    return 0;
}

static int h3_end_headers(nghttp3_conn *conn, int64_t stream_id, int fin, void *user_data, void *stream_user_data)
{
    (void)conn; (void)stream_id; (void)fin; (void)stream_user_data;
    h3_client_t *c = user_data;
    c->t_headers_us = esp_timer_get_time();
    return 0;
}

static int h3_recv_data(nghttp3_conn *conn, int64_t stream_id, const uint8_t *data, size_t datalen,
                        void *user_data, void *stream_user_data)
{
    (void)conn; (void)data; (void)stream_user_data;
    h3_client_t *c = user_data;
    c->body_bytes += datalen;
    return h3_consume(c, stream_id, datalen);
}

static int h3_deferred_consume(nghttp3_conn *conn, int64_t stream_id, size_t consumed, void *user_data,
                               void *stream_user_data)
{
    (void)conn; (void)stream_user_data;
    return h3_consume(user_data, stream_id, consumed);
}

static int h3_end_stream(nghttp3_conn *conn, int64_t stream_id, void *user_data, void *stream_user_data)
{
    (void)conn; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (stream_id == c->req_stream_id) {
        c->response_done = true;
        c->t_done_us = esp_timer_get_time();
    }
    return 0;
}

static int h3_stream_close(nghttp3_conn *conn, int64_t stream_id, uint64_t app_error_code, void *user_data,
                           void *stream_user_data)
{
    (void)conn; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (stream_id == c->req_stream_id && !c->response_done) {
        ESP_LOGW(TAG, "request stream closed early, app_error_code=0x%" PRIx64, app_error_code);
        c->response_done = true;
        c->t_done_us = esp_timer_get_time();
    }
    return 0;
}

/* ---------------- ngtcp2 callbacks ---------------- */
static void rand_cb(uint8_t *dest, size_t destlen, const ngtcp2_rand_ctx *ctx)
{
    (void)ctx;
    if (RAND_bytes(dest, (int)destlen) != 1) abort();
}

static int new_cid_cb(ngtcp2_conn *conn, ngtcp2_cid *cid, uint8_t *token, size_t cidlen, void *user_data)
{
    (void)conn; (void)user_data;
    if (RAND_bytes(cid->data, (int)cidlen) != 1 || RAND_bytes(token, NGTCP2_STATELESS_RESET_TOKENLEN) != 1) {
        return NGTCP2_ERR_CALLBACK_FAILURE;
    }
    cid->datalen = cidlen;
    return 0;
}

static int handshake_completed_cb(ngtcp2_conn *conn, void *user_data)
{
    (void)conn;
    h3_client_t *c = user_data;
    c->handshake_done = true;
    c->t_handshake_us = esp_timer_get_time();
    return 0;
}

static int extend_max_local_streams_bidi_cb(ngtcp2_conn *conn, uint64_t max_streams, void *user_data)
{
    (void)conn; (void)max_streams;
    ((h3_client_t *)user_data)->bidi_ready = true;
    return 0;
}

static int recv_stream_data_cb(ngtcp2_conn *conn, uint32_t flags, int64_t stream_id, uint64_t offset,
                               const uint8_t *data, size_t datalen, void *user_data, void *stream_user_data)
{
    (void)offset; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (!c->h3) return 0;
    nghttp3_ssize consumed = nghttp3_conn_read_stream(c->h3, stream_id, data, datalen,
                                                      (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0);
    if (consumed < 0) {
        ESP_LOGE(TAG, "nghttp3_conn_read_stream: %s", nghttp3_strerror((int)consumed));
        ngtcp2_ccerr_set_application_error(&c->last_error, nghttp3_err_infer_quic_app_error_code((int)consumed), NULL, 0);
        return NGTCP2_ERR_CALLBACK_FAILURE;
    }
    ngtcp2_conn_extend_max_stream_offset(conn, stream_id, (uint64_t)consumed);
    ngtcp2_conn_extend_max_offset(conn, (uint64_t)consumed);
    return 0;
}

static int acked_stream_data_offset_cb(ngtcp2_conn *conn, int64_t stream_id, uint64_t offset, uint64_t datalen,
                                       void *user_data, void *stream_user_data)
{
    (void)conn; (void)offset; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (c->h3 && nghttp3_conn_add_ack_offset(c->h3, stream_id, datalen) != 0) return NGTCP2_ERR_CALLBACK_FAILURE;
    return 0;
}

static int stream_close_cb(ngtcp2_conn *conn, uint32_t flags, int64_t stream_id, uint64_t app_error_code,
                           void *user_data, void *stream_user_data)
{
    (void)conn; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (!(flags & NGTCP2_STREAM_CLOSE_FLAG_APP_ERROR_CODE_SET)) app_error_code = NGHTTP3_H3_NO_ERROR;
    if (c->h3) {
        int rv = nghttp3_conn_close_stream(c->h3, stream_id, app_error_code);
        if (rv != 0 && rv != NGHTTP3_ERR_STREAM_NOT_FOUND) return NGTCP2_ERR_CALLBACK_FAILURE;
    }
    return 0;
}

static int stream_reset_cb(ngtcp2_conn *conn, int64_t stream_id, uint64_t final_size, uint64_t app_error_code,
                           void *user_data, void *stream_user_data)
{
    (void)conn; (void)final_size; (void)app_error_code; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (c->h3 && nghttp3_conn_shutdown_stream_read(c->h3, stream_id) != 0) return NGTCP2_ERR_CALLBACK_FAILURE;
    return 0;
}

static int stream_stop_sending_cb(ngtcp2_conn *conn, int64_t stream_id, uint64_t app_error_code, void *user_data,
                                  void *stream_user_data)
{
    return stream_reset_cb(conn, stream_id, 0, app_error_code, user_data, stream_user_data);
}

static int extend_max_stream_data_cb(ngtcp2_conn *conn, int64_t stream_id, uint64_t max_data, void *user_data,
                                     void *stream_user_data)
{
    (void)conn; (void)max_data; (void)stream_user_data;
    h3_client_t *c = user_data;
    if (c->h3 && nghttp3_conn_unblock_stream(c->h3, stream_id) != 0) return NGTCP2_ERR_CALLBACK_FAILURE;
    return 0;
}

static ngtcp2_conn *get_conn(ngtcp2_crypto_conn_ref *ref) { return ((h3_client_t *)ref->user_data)->conn; }

/* ---------------- setup ---------------- */
static int socket_setup(h3_client_t *c)
{
    struct addrinfo hints = { .ai_family = AF_UNSPEC, .ai_socktype = SOCK_DGRAM }, *res = NULL;
    if (getaddrinfo(c->cfg->host, c->cfg->port, &hints, &res) != 0 || res == NULL) return -1;
    c->fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    memcpy(&c->remote_addr, res->ai_addr, res->ai_addrlen);
    c->remote_addrlen = res->ai_addrlen;
    freeaddrinfo(res);
    if (c->fd < 0) return -1;
    if (connect(c->fd, (struct sockaddr *)&c->remote_addr, c->remote_addrlen) != 0) return -1;
    c->local_addrlen = sizeof(c->local_addr);
    return getsockname(c->fd, (struct sockaddr *)&c->local_addr, &c->local_addrlen);
}

static int tls_setup(h3_client_t *c)
{
    static const uint8_t alpn_h3[] = { 2, 'h', '3' };
    c->ssl_ctx = SSL_CTX_new(TLS_client_method());
    if (!c->ssl_ctx || ngtcp2_crypto_wolfssl_configure_client_context(c->ssl_ctx) != 0) return -1;
    wolfSSL_CTX_set_verify(c->ssl_ctx, WOLFSSL_VERIFY_NONE, NULL);  /* same as the MQTT experiments; see report */
    c->ssl = SSL_new(c->ssl_ctx);
    if (!c->ssl) return -1;
    SSL_set_app_data(c->ssl, &c->conn_ref);
    SSL_set_connect_state(c->ssl);
    SSL_set_alpn_protos(c->ssl, alpn_h3, sizeof(alpn_h3));
    return 0;
}

static int quic_setup(h3_client_t *c)
{
    ngtcp2_path path = { .local = { (struct sockaddr *)&c->local_addr, c->local_addrlen },
                         .remote = { (struct sockaddr *)&c->remote_addr, c->remote_addrlen } };
    ngtcp2_callbacks cb = {
        .client_initial = ngtcp2_crypto_client_initial_cb,
        .recv_crypto_data = ngtcp2_crypto_recv_crypto_data_cb,
        .encrypt = ngtcp2_crypto_encrypt_cb,
        .decrypt = ngtcp2_crypto_decrypt_cb,
        .hp_mask = ngtcp2_crypto_hp_mask_cb,
        .recv_retry = ngtcp2_crypto_recv_retry_cb,
        .update_key = ngtcp2_crypto_update_key_cb,
        .delete_crypto_aead_ctx = ngtcp2_crypto_delete_crypto_aead_ctx_cb,
        .delete_crypto_cipher_ctx = ngtcp2_crypto_delete_crypto_cipher_ctx_cb,
        .get_path_challenge_data = ngtcp2_crypto_get_path_challenge_data_cb,
        .version_negotiation = ngtcp2_crypto_version_negotiation_cb,
        .rand = rand_cb,
        .get_new_connection_id = new_cid_cb,
        .handshake_completed = handshake_completed_cb,
        .extend_max_local_streams_bidi = extend_max_local_streams_bidi_cb,
        .recv_stream_data = recv_stream_data_cb,
        .acked_stream_data_offset = acked_stream_data_offset_cb,
        .stream_close = stream_close_cb,
        .stream_reset = stream_reset_cb,
        .stream_stop_sending = stream_stop_sending_cb,
        .extend_max_stream_data = extend_max_stream_data_cb,
    };
    ngtcp2_cid dcid = { .datalen = NGTCP2_MIN_INITIAL_DCIDLEN }, scid = { .datalen = 8 };
    if (RAND_bytes(dcid.data, (int)dcid.datalen) != 1 || RAND_bytes(scid.data, (int)scid.datalen) != 1) return -1;
    ngtcp2_settings settings;
    ngtcp2_settings_default(&settings);
    settings.initial_ts = ts_ns();
    ngtcp2_transport_params params;
    ngtcp2_transport_params_default(&params);
    params.initial_max_streams_uni = 3;                      /* peer control + QPACK encoder/decoder */
    params.initial_max_stream_data_bidi_local = 64 * 1024;
    params.initial_max_stream_data_uni = 64 * 1024;
    params.initial_max_data = 256 * 1024;
    params.max_idle_timeout = 30 * NGTCP2_SECONDS;
    int rv = ngtcp2_conn_client_new(&c->conn, &dcid, &scid, &path, NGTCP2_PROTO_VER_V1, &cb, &settings, &params, NULL, c);
    if (rv != 0) { ESP_LOGE(TAG, "ngtcp2_conn_client_new: %s", ngtcp2_strerror(rv)); return -1; }
    ngtcp2_conn_set_tls_native_handle(c->conn, c->ssl);
    return 0;
}

static int h3_setup(h3_client_t *c)
{
    nghttp3_callbacks cb = {
        .recv_header = h3_recv_header,
        .end_headers = h3_end_headers,
        .recv_data = h3_recv_data,
        .deferred_consume = h3_deferred_consume,
        .end_stream = h3_end_stream,
        .stream_close = h3_stream_close,
    };
    nghttp3_settings settings;
    nghttp3_settings_default(&settings);
    settings.qpack_max_dtable_capacity = 0;   /* no dynamic table: smallest memory use */
    settings.qpack_blocked_streams = 0;
    if (ngtcp2_conn_get_streams_uni_left(c->conn) < 3) { ESP_LOGE(TAG, "peer allows < 3 uni streams"); return -1; }
    int rv = nghttp3_conn_client_new(&c->h3, &cb, &settings, nghttp3_mem_default(), c);
    if (rv != 0) { ESP_LOGE(TAG, "nghttp3_conn_client_new: %s", nghttp3_strerror(rv)); return -1; }
    int64_t ctrl, qenc, qdec;
    if (ngtcp2_conn_open_uni_stream(c->conn, &ctrl, NULL) != 0 || ngtcp2_conn_open_uni_stream(c->conn, &qenc, NULL) != 0 ||
        ngtcp2_conn_open_uni_stream(c->conn, &qdec, NULL) != 0) return -1;
    if (nghttp3_conn_bind_control_stream(c->h3, ctrl) != 0 || nghttp3_conn_bind_qpack_streams(c->h3, qenc, qdec) != 0) return -1;
    return 0;
}

#define NV(n, v) { (uint8_t *)(n), (uint8_t *)(v), sizeof(n) - 1, strlen(v), NGHTTP3_NV_FLAG_NONE }
static int h3_submit_get(h3_client_t *c)
{
    if (ngtcp2_conn_open_bidi_stream(c->conn, &c->req_stream_id, NULL) != 0) return -1;
    nghttp3_nv nva[] = {
        NV(":method", "GET"), NV(":scheme", "https"), NV(":authority", c->cfg->authority),
        NV(":path", c->cfg->path), NV("user-agent", "esp32c6-h3-trial"),
    };
    int rv = nghttp3_conn_submit_request(c->h3, c->req_stream_id, nva, sizeof(nva) / sizeof(nva[0]), NULL, c);
    if (rv != 0) { ESP_LOGE(TAG, "nghttp3_conn_submit_request: %s", nghttp3_strerror(rv)); return -1; }
    c->request_sent = true;
    c->t_request_us = esp_timer_get_time();
    return 0;
}

/* ---------------- I/O ---------------- */
static int read_packets(h3_client_t *c)
{
    uint8_t buf[1500];
    for (int i = 0; i < 16; i++) {
        struct sockaddr_storage addr;
        socklen_t addrlen = sizeof(addr);
        ssize_t n = recvfrom(c->fd, buf, sizeof(buf), MSG_DONTWAIT, (struct sockaddr *)&addr, &addrlen);
        if (n < 0) return (errno == EAGAIN || errno == EWOULDBLOCK) ? 0 : -1;
        ngtcp2_path path = { .local = { (struct sockaddr *)&c->local_addr, c->local_addrlen },
                             .remote = { (struct sockaddr *)&addr, addrlen } };
        ngtcp2_pkt_info pi = {0};
        int rv = ngtcp2_conn_read_pkt(c->conn, &path, &pi, buf, (size_t)n, ts_ns());
        if (rv != 0) {
            ESP_LOGE(TAG, "ngtcp2_conn_read_pkt: %s", ngtcp2_strerror(rv));
            if (!c->last_error.error_code) ngtcp2_ccerr_set_liberr(&c->last_error, rv, NULL, 0);
            return -1;
        }
    }
    return 0;
}

static int write_packets(h3_client_t *c)
{
    uint8_t buf[1452];
    ngtcp2_path_storage ps;
    ngtcp2_path_storage_zero(&ps);
    for (;;) {
        int64_t stream_id = -1;
        int fin = 0;
        nghttp3_vec vec[16];
        nghttp3_ssize sveccnt = 0;
        if (c->h3 && ngtcp2_conn_get_max_data_left(c->conn)) {
            sveccnt = nghttp3_conn_writev_stream(c->h3, &stream_id, &fin, vec, 16);
            if (sveccnt < 0) { ESP_LOGE(TAG, "nghttp3_conn_writev_stream: %s", nghttp3_strerror((int)sveccnt)); return -1; }
        }
        ngtcp2_ssize ndatalen = -1;
        uint32_t flags = NGTCP2_WRITE_STREAM_FLAG_MORE | (fin ? NGTCP2_WRITE_STREAM_FLAG_FIN : 0);
        ngtcp2_pkt_info pi;
        ngtcp2_ssize nwrite = ngtcp2_conn_writev_stream(c->conn, &ps.path, &pi, buf, sizeof(buf), &ndatalen, flags,
                                                        stream_id, (const ngtcp2_vec *)vec, (size_t)sveccnt, ts_ns());
        if (nwrite < 0) {
            switch (nwrite) {
            case NGTCP2_ERR_STREAM_DATA_BLOCKED:
                nghttp3_conn_block_stream(c->h3, stream_id);
                continue;
            case NGTCP2_ERR_STREAM_SHUT_WR:
                nghttp3_conn_shutdown_stream_write(c->h3, stream_id);
                continue;
            case NGTCP2_ERR_WRITE_MORE:
                if (nghttp3_conn_add_write_offset(c->h3, stream_id, (size_t)ndatalen) != 0) return -1;
                continue;
            }
            ESP_LOGE(TAG, "ngtcp2_conn_writev_stream: %s", ngtcp2_strerror((int)nwrite));
            ngtcp2_ccerr_set_liberr(&c->last_error, (int)nwrite, NULL, 0);
            return -1;
        }
        if (ndatalen >= 0 && stream_id >= 0 && nghttp3_conn_add_write_offset(c->h3, stream_id, (size_t)ndatalen) != 0) return -1;
        if (nwrite == 0) return 0;
        if (send(c->fd, buf, (size_t)nwrite, 0) < 0 && errno != EAGAIN) { ESP_LOGE(TAG, "send: %d", errno); return -1; }
    }
}

static void send_close(h3_client_t *c)
{
    if (!c->conn || ngtcp2_conn_in_closing_period(c->conn) || ngtcp2_conn_in_draining_period(c->conn)) return;
    uint8_t buf[1280];
    ngtcp2_path_storage ps;
    ngtcp2_path_storage_zero(&ps);
    ngtcp2_pkt_info pi;
    if (!c->last_error.error_code) ngtcp2_ccerr_set_application_error(&c->last_error, NGHTTP3_H3_NO_ERROR, NULL, 0);
    ngtcp2_ssize n = ngtcp2_conn_write_connection_close(c->conn, &ps.path, &pi, buf, sizeof(buf), &c->last_error, ts_ns());
    if (n > 0) send(c->fd, buf, (size_t)n, 0);
}

int http3_client_get(const http3_client_config_t *cfg, http3_result_t *out)
{
    h3_client_t c = { .fd = -1, .req_stream_id = -1, .cfg = cfg };
    memset(out, 0, sizeof(*out));
    c.conn_ref.get_conn = get_conn;
    c.conn_ref.user_data = &c;
    ngtcp2_ccerr_default(&c.last_error);
    c.t0_us = esp_timer_get_time();
    int result = -1;
    if (socket_setup(&c) != 0 || tls_setup(&c) != 0 || quic_setup(&c) != 0) { ESP_LOGE(TAG, "setup failed"); goto done; }

    int64_t deadline = c.t0_us + (int64_t)cfg->timeout_ms * 1000;
    while (!c.response_done && esp_timer_get_time() < deadline) {
        if (c.handshake_done && !c.h3 && h3_setup(&c) != 0) goto done;
        if (c.h3 && c.bidi_ready && !c.request_sent && h3_submit_get(&c) != 0) goto done;
        if (write_packets(&c) != 0) goto done;
        ngtcp2_tstamp expiry = ngtcp2_conn_get_expiry(c.conn), now = ts_ns();
        int64_t wait_us = expiry <= now ? 0 : (int64_t)((expiry - now) / 1000);
        if (wait_us > 100000) wait_us = 100000;
        fd_set rfds;
        FD_ZERO(&rfds);
        FD_SET(c.fd, &rfds);
        struct timeval tv = { .tv_sec = 0, .tv_usec = wait_us };
        int s = select(c.fd + 1, &rfds, NULL, NULL, &tv);
        if (s > 0 && read_packets(&c) != 0) goto done;
        if (ngtcp2_conn_get_expiry(c.conn) <= ts_ns()) {
            int rv = ngtcp2_conn_handle_expiry(c.conn, ts_ns());
            if (rv != 0) { ESP_LOGE(TAG, "handle_expiry: %s", ngtcp2_strerror(rv)); goto done; }
        }
        if (ngtcp2_conn_in_closing_period(c.conn) || ngtcp2_conn_in_draining_period(c.conn)) goto done;
    }
    result = c.response_done ? 0 : -2;
done:
    out->status_code = c.status_code;
    out->header_count = c.header_count;
    out->body_bytes = c.body_bytes;
    out->handshake_ms = c.t_handshake_us ? (c.t_handshake_us - c.t0_us) / 1000.0 : -1;
    out->first_header_ms = c.t_headers_us && c.t_request_us ? (c.t_headers_us - c.t_request_us) / 1000.0 : -1;
    out->total_ms = c.t_done_us ? (c.t_done_us - c.t0_us) / 1000.0 : -1;
    out->free_heap_min = esp_get_minimum_free_heap_size();
    if (c.conn) send_close(&c);
    if (c.h3) nghttp3_conn_del(c.h3);
    if (c.conn) ngtcp2_conn_del(c.conn);
    if (c.ssl) SSL_free(c.ssl);
    if (c.ssl_ctx) SSL_CTX_free(c.ssl_ctx);
    if (c.fd >= 0) close(c.fd);
    return result;
}

void http3_client_task(void *arg)
{
    (void)arg;
    static const http3_client_config_t cfg = {
        .host = HTTP3_SERVER_HOST, .port = HTTP3_SERVER_PORT, .authority = HTTP3_SERVER_HOST, .path = "/", .timeout_ms = 20000,
    };
    for (int i = 1; i <= 5; i++) {
        http3_result_t r;
        int rv = http3_client_get(&cfg, &r);
        printf("H3_RESULT attempt=%d rv=%d status=%d headers=%u body_bytes=%llu handshake_ms=%.1f request_to_headers_ms=%.1f"
               " total_ms=%.1f free=%u min_free=%u\n", i, rv, r.status_code, (unsigned)r.header_count,
               (unsigned long long)r.body_bytes, r.handshake_ms, r.first_header_ms, r.total_ms,
               (unsigned)esp_get_free_heap_size(), (unsigned)r.free_heap_min);
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
    vTaskDelete(NULL);
}
