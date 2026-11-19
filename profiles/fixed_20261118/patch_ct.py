"""Apply to profiles/fixed_20261118/src (backs files up first, no device access):
 (1) ev_default_loop_init() runs only once per boot (event-loop leak fix),
 (2) FIXED_CT_MODE=1 : connection-time test task (50 attempts: connect -> MQTT CONNECT/CONNACK -> close -> wait 3 s),
 (3) FIXED_HEAPLOG=1 : normal sensor loop plus a free-heap / minimum-free-heap line every 60 s.
All new code is compiled only when the matching CMake cache variable is 1 (default 0)."""
from pathlib import Path
import datetime as dt, shutil

p = Path(__file__).resolve().parent
src = p / 'src'
stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
done = set()


def replace(rel, old, new, count=1):
    f = src / rel
    if rel not in done:
        shutil.copy2(f, str(f) + '.bak_' + stamp)
        done.add(rel)
    t = f.read_bytes().decode('utf-8')
    crlf = '\r\n' in t
    if crlf:
        t = t.replace('\r\n', '\n')
    assert t.count(old) == count, (rel, old, t.count(old))
    t = t.replace(old, new)
    f.write_bytes((t.replace('\n', '\r\n') if crlf else t).encode('utf-8'))


# (1) event loop once
replace('main/esp_ev_compat.c', 'void ev_default_loop_init(void) {\n    ESP_ERROR_CHECK(ev_loop_init(EV_DEFAULT));\n}',
        'void ev_default_loop_init(void) {\n'
        '    /* Run only once per boot: a second call would memset the live loop and create another event task. */\n'
        '    static bool default_loop_ready = false;\n'
        '    if (default_loop_ready) return;\n'
        '    ESP_ERROR_CHECK(ev_loop_init(EV_DEFAULT));\n'
        '    default_loop_ready = true;\n}')

# CMake switches
replace('main/CMakeLists.txt', 'set(FIXED_TEST_RUN_ID "f0" CACHE STRING "TEST ONLY: NVS namespace suffix")',
        'set(FIXED_TEST_RUN_ID "f0" CACHE STRING "TEST ONLY: NVS namespace suffix")\n'
        'set(FIXED_CT_MODE "0" CACHE STRING "1=connection-time test image (50 attempts)")\n'
        'set(FIXED_HEAPLOG "0" CACHE STRING "1=log free/min free heap every 60 s in the normal sensor loop")')
replace('main/CMakeLists.txt', 'FIXED_TEST_MODE=${FIXED_TEST_MODE} ',
        'FIXED_CT_MODE=${FIXED_CT_MODE} FIXED_HEAPLOG=${FIXED_HEAPLOG} FIXED_TEST_MODE=${FIXED_TEST_MODE} ')

# timestamps inside the transports (compiled only with FIXED_CT_MODE)
T = 'main/mqtt_tcp_tls_transport.c'
replace(T, 'void tcp_tls_client_cleanup(void)\n{',
        '#if FIXED_CT_MODE\nvolatile int64_t g_ct_tcp_t0_us, g_ct_tcp_connect_done_us, g_ct_tls_done_us;\n#endif\n\nvoid tcp_tls_client_cleanup(void)\n{')
replace(T, '    client.timeout_ms = timeout_ms;\n    int64_t deadline',
        '#if FIXED_CT_MODE\n    g_ct_tcp_t0_us = esp_timer_get_time(); g_ct_tcp_connect_done_us = 0; g_ct_tls_done_us = 0;\n#endif\n'
        '    client.timeout_ms = timeout_ms;\n    int64_t deadline')
replace(T, '    if (wolfSSL_Init() != WOLFSSL_SUCCESS) goto failure;',
        '#if FIXED_CT_MODE\n    g_ct_tcp_connect_done_us = esp_timer_get_time();\n#endif\n    if (wolfSSL_Init() != WOLFSSL_SUCCESS) goto failure;')
replace(T, '        if (result == WOLFSSL_SUCCESS) break;\n        int error = wolfSSL_get_error(client.ssl, result);\n        if ((error != WOLFSSL_ERROR_WANT_READ',
        '        if (result == WOLFSSL_SUCCESS) {\n#if FIXED_CT_MODE\n            g_ct_tls_done_us = esp_timer_get_time();\n#endif\n            break;\n        }\n'
        '        int error = wolfSSL_get_error(client.ssl, result);\n        if ((error != WOLFSSL_ERROR_WANT_READ')

S = 'main/ngtcp2_sample.c'
replace(S, 'static int handshake_completed_cb(ngtcp2_conn *conn, void *user_data) {\n    (void)conn;',
        '#if FIXED_CT_MODE\nvolatile int64_t g_ct_quic_t0_us, g_ct_quic_init_done_us, g_ct_quic_hs_us;\n#endif\n'
        'static int handshake_completed_cb(ngtcp2_conn *conn, void *user_data) {\n#if FIXED_CT_MODE\n    g_ct_quic_hs_us = esp_timer_get_time();\n#endif\n    (void)conn;')
replace(S, '    ESP_LOGI(TAG, "init random number generator");',
        '#if FIXED_CT_MODE\n    g_ct_quic_t0_us = esp_timer_get_time(); g_ct_quic_init_done_us = 0; g_ct_quic_hs_us = 0;\n#endif\n    ESP_LOGI(TAG, "init random number generator");')
replace(S, '    g_quic_connected = false;\n    g_quic_handshake_completed = false;\n    \n    xSemaphoreGive(quic_mutex);\n    ESP_LOGI(TAG, "QUIC client initialization completed");',
        '    g_quic_connected = false;\n    g_quic_handshake_completed = false;\n#if FIXED_CT_MODE\n    g_ct_quic_init_done_us = esp_timer_get_time();\n#endif\n    \n    xSemaphoreGive(quic_mutex);\n    ESP_LOGI(TAG, "QUIC client initialization completed");')

# (2)+(3) main
M = 'main/quic_demo_main.c'
ct = r'''#if FIXED_CT_MODE
#define CT_ATTEMPTS 50
#if DEMO_TRANSPORT_TCP_TLS
extern volatile int64_t g_ct_tcp_t0_us, g_ct_tcp_connect_done_us, g_ct_tls_done_us;
#else
extern volatile int64_t g_ct_quic_t0_us, g_ct_quic_init_done_us, g_ct_quic_hs_us;
#endif

/* Connection-time test task: replaces the sensor task. One CSV-like line per attempt, all times in microseconds
 * from esp_timer_get_time(); -1 = not applicable / not reached. */
static void ct_task(void *argument)
{
    (void)argument;
    unsigned ok_count = 0, fail_count = 0;
    printf("CT HEADER attempt,proto,status,tcp_connect_us,tls_handshake_us,tcp_tls_total_us,quic_init_us,quic_handshake_cb_us,quic_ready_seen_us,mqtt_connect_to_connack_us,connack_from_start_us,reason\n");
    for (int attempt = 1; attempt <= CT_ATTEMPTS; attempt++) {
        int64_t t0 = esp_timer_get_time();
        int64_t tcp_connect = -1, tls = -1, tcp_total = -1, qinit = -1, qhs = -1, qready = -1, mq = -1, connack = -1;
        const char *reason = "ok";
        bool ok = false;
        bool transport_up = false;
#if DEMO_TRANSPORT_TCP_TLS
        transport_up = tcp_tls_client_connect(&server_info, 5000) == 0;
        if (transport_up) {
            tcp_connect = g_ct_tcp_connect_done_us - g_ct_tcp_t0_us;
            tls = g_ct_tls_done_us - g_ct_tcp_connect_done_us;
            tcp_total = g_ct_tls_done_us - g_ct_tcp_t0_us;
        } else {
            reason = "tcp_tls_connect_failed";
        }
#else
        char port_text[16];
        snprintf(port_text, sizeof(port_text), "%u", (unsigned)server_info.port);
        quic_client_config_t quic_config = {.hostname = server_info.pHostName, .port = port_text, .alpn = server_info.pAlpn};
        if (quic_client_init_with_config(&quic_config) != 0) {
            reason = "quic_init_failed";
        } else {
            qinit = g_ct_quic_init_done_us - g_ct_quic_t0_us;
            for (int i = 0; i < 200; i++) {   /* same polling loop as wait_for_quic_ready(): 100 ms steps, 20 s limit */
                if (quic_client_process() != 0) { reason = "quic_process_failed"; break; }
                if (quic_client_is_connected() && quic_client_local_stream_avail()) {
                    qready = esp_timer_get_time() - t0;
                    transport_up = true;
                    break;
                }
                vTaskDelay(pdMS_TO_TICKS(100));
            }
            if (transport_up) {
                qhs = g_ct_quic_hs_us - g_ct_quic_t0_us;
            } else if (strcmp(reason, "ok") == 0) {
                reason = "quic_handshake_timeout";
            }
        }
#endif
        if (transport_up) {
            NetworkContext_t network_context = {0};
            MQTTQUICConfig_t transport_config = {.timeoutMs = 5000, .nonBlocking = false};
            MQTTContext_t mqtt_context;
            MQTTFixedBuffer_t network_buffer = {.pBuffer = mqtt_buffer, .size = sizeof(mqtt_buffer)};
            if (demo_transport_init(&network_context, &server_info, &transport_config) != pdPASS) {
                reason = "transport_init_failed";
            } else {
                xTransportInterface.pNetworkContext = &network_context;
                xTransportInterface.recv = mqtt_quic_transport_recv;
                xTransportInterface.send = mqtt_quic_transport_send;
                if (MQTT_Init(&mqtt_context, &xTransportInterface, mqtt_get_time_ms, mqtt_event_callback, &network_buffer) != MQTTSuccess) {
                    reason = "mqtt_init_failed";
                } else {
                    MQTTConnectInfo_t connect_info = {0};
                    connect_info.cleanSession = true;
                    connect_info.pClientIdentifier = MQTT_CLIENT_ID;
                    connect_info.clientIdentifierLength = (uint16_t)strlen(MQTT_CLIENT_ID);
                    bool session_present = false;
                    int64_t tm0 = esp_timer_get_time();
                    MQTTStatus_t st = MQTT_Connect(&mqtt_context, &connect_info, NULL, 5000, &session_present);
                    int64_t tm1 = esp_timer_get_time();
                    if (st == MQTTSuccess) {
                        mq = tm1 - tm0;
                        connack = tm1 - t0;
                        ok = true;
                        (void)MQTT_Disconnect(&mqtt_context);
                    } else {
                        reason = "mqtt_connack_failed";
                    }
                }
            }
        }
        demo_client_cleanup();
        if (ok) ok_count++; else fail_count++;
        printf("CT %d,%s,%s,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%s\n", attempt, DEMO_TRANSPORT_NAME, ok ? "OK" : "FAIL",
                       (long long)tcp_connect, (long long)tls, (long long)tcp_total, (long long)qinit, (long long)qhs,
                       (long long)qready, (long long)mq, (long long)connack, reason);
        if (attempt % 10 == 0) {
            printf("CT HEAP attempt=%d free=%u min_free=%u\n", attempt, (unsigned)esp_get_free_heap_size(),
                           (unsigned)esp_get_minimum_free_heap_size());
        }
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
    printf("CT COMPLETE proto=%s attempts=%d ok=%u failed=%u free=%u min_free=%u\n", DEMO_TRANSPORT_NAME, CT_ATTEMPTS,
                   ok_count, fail_count, (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size());
    vTaskDelete(NULL);
}
#endif

#if FIXED_TEST_MODE
/* TEST ONLY cycle task'''
replace(M, '#if FIXED_TEST_MODE\n/* TEST ONLY cycle task', ct)
replace(M, '#if FIXED_TEST_MODE\n        test_cycle_task,\n#else\n        quic_sensor_task,\n#endif',
        '#if FIXED_CT_MODE\n        ct_task,\n#elif FIXED_TEST_MODE\n        test_cycle_task,\n#else\n        quic_sensor_task,\n#endif')
# heap log every 60 s inside the sensor loop
replace(M, '    int64_t last_publish_us = esp_timer_get_time();\n    char payload[256];',
        '    int64_t last_publish_us = esp_timer_get_time();\n#if FIXED_HEAPLOG\n    int64_t last_heaplog_us = last_publish_us;\n#endif\n    char payload[256];')
replace(M, '        int64_t now_us = esp_timer_get_time();\n\n        if (now_us - last_publish_us >= PUBLISH_INTERVAL_US) {',
        '        int64_t now_us = esp_timer_get_time();\n#if FIXED_HEAPLOG\n        if (now_us - last_heaplog_us >= 60000000LL) {\n'
        '            last_heaplog_us = now_us;\n'
        '            printf("HEAPLOG uptime_s=%lld free=%u min_free=%u\\n", (long long)(now_us / 1000000LL),\n'
        '                           (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size());\n        }\n#endif\n\n'
        '        if (now_us - last_publish_us >= PUBLISH_INTERVAL_US) {')
print('patched; backups stamp', stamp)
