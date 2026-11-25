#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_event.h"
#include "esp_idf_version.h"
#include "esp_log.h"
#include "measurement_logging.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "nvs.h"
#include "esp_rom_sys.h"
#include "nvs_flash.h"

#include "protocol_examples_common.h"
#include "core_mqtt.h"
#include "mqtt_quic_transport.h"
#include "ngtcp2_sample.h"
#include "mqtt_tcp_tls_transport.h"
#include "dht.h"
#include "cJSON.h"

#if DEMO_TRANSPORT_TCP_TLS
#define DEMO_TRANSPORT_NAME "TCP_TLS"
#define DEMO_SERVER_PORT 14568
#define demo_client_is_connected tcp_tls_client_is_connected
#define demo_client_process tcp_tls_client_process
#define demo_client_cleanup tcp_tls_client_cleanup
#define demo_transport_init mqtt_tcp_tls_transport_init
#else
#define DEMO_TRANSPORT_NAME "QUIC"
#define DEMO_SERVER_PORT 14567
#define demo_client_is_connected quic_client_is_connected
#define demo_client_process quic_client_process
#define demo_client_cleanup quic_client_cleanup
#define demo_transport_init mqtt_quic_transport_init
#endif

#define DHT_GPIO GPIO_NUM_4
#define MQTT_TOPIC "esp32/quic/test"
#define MQTT_CLIENT_ID "esp32_quic_client"
#define PUBLISH_INTERVAL_US 5000000LL
#define APP_RTT_CAPACITY 16
#define APP_RTT_MAX_JSON_BYTES 512

static const char *TAG = "quic_demo_main";
static uint8_t mqtt_buffer[2048];

/* Only quic_sensor_task and its synchronous coreMQTT callback use this table.
 * The QUIC event task does not access it. Completed entries identify recent
 * duplicates; once reused, older echoes are simply unmatched.
 */
typedef enum { RTT_EMPTY, RTT_PENDING, RTT_MATCHED, RTT_FAILED } rtt_state_t;
typedef struct {
    uint32_t seq;
    int64_t send_time_us;
    rtt_state_t state;
} pending_rtt_t;
static pending_rtt_t pending_rtt[APP_RTT_CAPACITY];
static int64_t s_last_echo_us = 0;  /* RECONNECT PROFILE: time of the last matched echo */

static pending_rtt_t *app_rtt_reserve(uint32_t seq)
{
    pending_rtt_t *slot = NULL;
    for (size_t i = 0; i < APP_RTT_CAPACITY; i++) {
        pending_rtt_t *entry = &pending_rtt[i];
        if (entry->state != RTT_PENDING &&
            (slot == NULL || entry->send_time_us < slot->send_time_us)) {
            slot = entry;
        }
    }
    if (slot == NULL) {
        slot = &pending_rtt[0];
        for (size_t i = 1; i < APP_RTT_CAPACITY; i++) {
            if (pending_rtt[i].send_time_us < slot->send_time_us) {
                slot = &pending_rtt[i];
            }
        }
        ESP_LOGW(TAG, "APP_RTT storage full; dropping pending seq=%" PRIu32,
                 slot->seq);
    }
    slot->seq = seq;
    slot->state = RTT_PENDING;
    return slot;
}

/* MQTT payloads are length-delimited, not necessarily NUL-terminated. Require
 * one top-level seq, an exact uint32 value, and no trailing non-JSON content.
 */
static bool app_rtt_parse_seq(const void *payload, size_t length, uint32_t *seq)
{
    if (payload == NULL || length == 0 || length > APP_RTT_MAX_JSON_BYTES ||
        memchr(payload, '\0', length) != NULL) {
        return false;
    }
    /* Bound parser recursion before entering cJSON. Braces inside strings
     * (including escaped quotes/backslashes) do not contribute to depth.
     */
    const char *text = payload;
    unsigned depth = 0;
    bool quoted = false, escaped = false;
    for (size_t i = 0; i < length; i++) {
        char ch = text[i];
        if (quoted) {
            if (escaped) {
                escaped = false;
            } else if (ch == '\\') {
                escaped = true;
            } else if (ch == '"') {
                quoted = false;
            }
        } else if (ch == '"') {
            quoted = true;
        } else if (ch == '{' || ch == '[') {
            if (++depth > 16) {
                return false;
            }
        } else if ((ch == '}' || ch == ']') && depth > 0) {
            depth--;
        }
    }
    const char *end = NULL;
    const char *limit = (const char *)payload + length;
    cJSON *root = cJSON_ParseWithLengthOpts(payload, length, &end, false);
    bool valid = cJSON_IsObject(root);
    const cJSON *seq_item = NULL;
    const cJSON *item = NULL;
    cJSON_ArrayForEach(item, root) {
        if (item->string != NULL && strcmp(item->string, "seq") == 0) {
            if (seq_item != NULL) {
                valid = false;  // Reject ambiguous duplicate JSON keys.
            }
            seq_item = item;
        }
    }
    if (end == NULL) {
        valid = false;
    } else {
        while (end < limit && (*end == ' ' || *end == '\t' ||
                               *end == '\r' || *end == '\n')) {
            end++;
        }
        valid = valid && end == limit;
    }
    if (!cJSON_IsNumber(seq_item)) {
        valid = false;
    } else {
        double number = seq_item->valuedouble;
        if (!isfinite(number) || number < 0 || number > UINT32_MAX ||
            number != floor(number)) {
            valid = false;
        } else if (valid) {
            *seq = (uint32_t)number;
        }
    }
    cJSON_Delete(root);
    return valid;
}

static void app_rtt_on_echo(const MQTTPublishInfo_t *message, int64_t receive_time_us)
{
    if (message->topicNameLength != sizeof(MQTT_TOPIC) - 1 ||
        message->pTopicName == NULL ||
        memcmp(message->pTopicName, MQTT_TOPIC, sizeof(MQTT_TOPIC) - 1) != 0) {
        return;
    }
    uint32_t seq;
    if (!app_rtt_parse_seq(message->pPayload, message->payloadLength, &seq)) {
        ESP_LOGW(TAG, "APP_RTT ignored echo with invalid JSON seq");
        return;
    }
    for (size_t i = 0; i < APP_RTT_CAPACITY; i++) {
        pending_rtt_t *entry = &pending_rtt[i];
        if (entry->state == RTT_EMPTY || entry->seq != seq) {
            continue;
        }
        if (entry->state != RTT_PENDING) {
            ESP_LOGW(TAG, "APP_RTT ignored duplicate or failed-publish seq=%" PRIu32, seq);
            return;
        }
        entry->state = RTT_MATCHED;  // Each pending message matches at most once.
        s_last_echo_us = receive_time_us;
        if (receive_time_us < entry->send_time_us) {
            ESP_LOGW(TAG, "APP_RTT ignored invalid clock order seq=%" PRIu32, seq);
            return;
        }
        double app_rtt_ms = (receive_time_us - entry->send_time_us) / 1000.0;
        ESP_LOGI(TAG, "APP_RTT seq=%" PRIu32 " app_rtt_ms=%.3f", seq, app_rtt_ms);
        return;
    }
    ESP_LOGW(TAG, "APP_RTT ignored unmatched seq=%" PRIu32, seq);
}

static const ServerInfo_t server_info = {
    .pHostName = "192.168.137.1",
    .port = DEMO_SERVER_PORT,
    .pAlpn = "mqtt"
};

extern TransportInterface_t xTransportInterface;
extern uint32_t mqtt_get_time_ms(void);


/* Display messages returned by the laptop. */
static void mqtt_event_callback(
    MQTTContext_t *context,
    MQTTPacketInfo_t *packet_info,
    MQTTDeserializedInfo_t *deserialized_info)
{
    (void)context;

    if (packet_info->type == MQTT_PACKET_TYPE_PUBLISH &&
        deserialized_info != NULL &&
        deserialized_info->pPublishInfo != NULL) {

        const MQTTPublishInfo_t *message =
            deserialized_info->pPublishInfo;

        /* Measure receipt before JSON parsing and console logging. This is
         * application RTT, including MQTT/QUIC processing and scheduling,
         * rather than ngtcp2's transport RTT.
         */
        int64_t receive_time_us = esp_timer_get_time();
        app_rtt_on_echo(message, receive_time_us);

        MEASUREMENT_LOGI(TAG, "=== MQTT PUBLISH RECEIVED ===");

        MEASUREMENT_LOGI(
            TAG,
            "Topic: %.*s",
            (int)message->topicNameLength,
            message->pTopicName
        );

        MEASUREMENT_LOGI(
            TAG,
            "Payload: %.*s",
            (int)message->payloadLength,
            (const char *)message->pPayload
        );
    } else if (packet_info->type == MQTT_PACKET_TYPE_SUBACK) {
        ESP_LOGI(TAG, "Subscription acknowledged");
    }
}


/* Read DHT11 and create the JSON message. */
static int make_sensor_payload(
    char *payload,
    size_t capacity,
    uint32_t sequence)
{
    int16_t humidity10 = 0;
    int16_t temperature10 = 0;

    esp_err_t sensor_status = dht_read_data(
        DHT_TYPE_DHT11,
        DHT_GPIO,
        &humidity10,
        &temperature10
    );

    int64_t uptime_ms = esp_timer_get_time() / 1000;

    if (sensor_status == ESP_OK) {
        double temperature = temperature10 / 10.0;
        double humidity = humidity10 / 10.0;

        MEASUREMENT_LOGI(
            TAG,
            "DHT11 seq=%" PRIu32 ": %.1f C, %.1f %%RH",
            sequence,
            temperature,
            humidity
        );

        return snprintf(
            payload,
            capacity,
            "{\"seq\":%" PRIu32 ","
            "\"sensor\":\"DHT11\","
            "\"uptime_ms\":%" PRId64 ","
            "\"temperature_c\":%.1f,"
            "\"humidity_pct\":%.1f,"
            "\"sensor_error\":0}",
            sequence,
            uptime_ms,
            temperature,
            humidity
        );
    }

    ESP_LOGW(
        TAG,
        "DHT11 read failed: %s",
        esp_err_to_name(sensor_status)
    );

    /* A failed read is reported without fake measurements. */
    return snprintf(
        payload,
        capacity,
        "{\"seq\":%" PRIu32 ","
        "\"sensor\":\"DHT11\","
        "\"uptime_ms\":%" PRId64 ","
        "\"temperature_c\":null,"
        "\"humidity_pct\":null,"
        "\"sensor_error\":%d}",
        sequence,
        uptime_ms,
        (int)sensor_status
    );
}


#if !DEMO_TRANSPORT_TCP_TLS
/* Allow up to approximately 20 seconds for QUIC setup. */
static bool wait_for_quic_ready(void)
{
    for (int attempt = 0; attempt < 200; attempt++) {
        if (quic_client_process() != 0) {
            ESP_LOGE(TAG, "QUIC processing failed during setup");
            return false;
        }

        if (quic_client_is_connected() &&
            quic_client_local_stream_avail()) {
            return true;
        }

        vTaskDelay(pdMS_TO_TICKS(100));
    }

    ESP_LOGE(TAG, "QUIC connection setup timed out");
    return false;
}


#endif

/* ==== RECONNECT PROFILE (reconnect_20261124) =========================================================
 * Diagnostics: DIAG line every 60 s (Wi-Fi RSSI, heap, pending echoes, transport state), Wi-Fi event lines,
 * STALL line when the oldest unanswered publish is older than 15 s.
 * Reconnect: on transport close/error, MQTT error/keepalive timeout, failed publish or STALL the session is
 * closed cleanly (MQTT DISCONNECT, TLS close_notify / QUIC CONNECTION_CLOSE) and opened again; Wi-Fi stays up.
 * The first connection runs the same calls in the same order as the fixed profile (including the 1 s delay).
 * Reconnects skip the 1 s delay (as in the connection-time test). */
#define STALL_TIMEOUT_US 15000000LL
#define DIAG_INTERVAL_US 60000000LL
#define RECONNECT_MAX_BACKOFF_MS 30000
#define WIFI_KICK_INTERVAL_US 30000000LL

#if DEMO_TRANSPORT_TCP_TLS
#define demo_client_diag tcp_tls_client_diag
#define demo_client_close_cleanup tcp_tls_client_cleanup
#else
#define demo_client_diag quic_client_diag
#define demo_client_close_cleanup quic_client_close_and_cleanup
#endif

static volatile uint32_t s_wifi_disconnects = 0;
static volatile bool s_wifi_has_ip = true;
static int64_t s_last_diag_us = 0;
static int s_last_mqtt_status = 0;
static uint32_t s_need_more_bytes_run = 0;
static uint32_t s_session = 0;
static NetworkContext_t s_network_context;
static MQTTContext_t s_mqtt_context;
static const MQTTQUICConfig_t s_transport_config = { .timeoutMs = 5000, .nonBlocking = false };

static long long uptime_ms(void) { return (long long)(esp_timer_get_time() / 1000); }

static int wifi_rssi(void)
{
    wifi_ap_record_t ap;
    return esp_wifi_sta_get_ap_info(&ap) == ESP_OK ? ap.rssi : 0;  /* 0 = not associated */
}

static void wifi_diag_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        const wifi_event_sta_disconnected_t *d = data;
        s_wifi_disconnects++;
        s_wifi_has_ip = false;
        printf("WIFI_EVENT disconnected uptime_ms=%lld reason=%u rssi=%d count=%u\n", uptime_ms(),
               (unsigned)d->reason, (int)d->rssi, (unsigned)s_wifi_disconnects);
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_CONNECTED) {
        const wifi_event_sta_connected_t *d = data;
        printf("WIFI_EVENT associated uptime_ms=%lld channel=%u rssi=%d\n", uptime_ms(), (unsigned)d->channel, wifi_rssi());
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        s_wifi_has_ip = true;
        printf("WIFI_EVENT got_ip uptime_ms=%lld rssi=%d\n", uptime_ms(), wifi_rssi());
    } else if (base == IP_EVENT && id == IP_EVENT_STA_LOST_IP) {
        s_wifi_has_ip = false;
        printf("WIFI_EVENT lost_ip uptime_ms=%lld\n", uptime_ms());
    }
}

static void rtt_pending_stats(int64_t now, unsigned *count, uint32_t *oldest_seq, int64_t *oldest_age_us)
{
    *count = 0; *oldest_seq = 0; *oldest_age_us = -1;
    for (size_t i = 0; i < APP_RTT_CAPACITY; i++) {
        if (pending_rtt[i].state != RTT_PENDING) continue;
        (*count)++;
        int64_t age = now - pending_rtt[i].send_time_us;
        if (age > *oldest_age_us) { *oldest_age_us = age; *oldest_seq = pending_rtt[i].seq; }
    }
}

/* Unanswered publishes of a closed session are reported once and never matched later. */
static void rtt_drop_pending(const char *reason)
{
    for (size_t i = 0; i < APP_RTT_CAPACITY; i++) {
        if (pending_rtt[i].state == RTT_PENDING) {
            pending_rtt[i].state = RTT_FAILED;
            printf("APP_RTT_LOST seq=%" PRIu32 " reason=%s\n", pending_rtt[i].seq, reason);
        }
    }
}

static void log_diag(const char *kind, int64_t now)
{
    static char transport[480];
    demo_client_diag(transport, sizeof(transport));
    unsigned pending; uint32_t oldest_seq; int64_t oldest_age;
    rtt_pending_stats(now, &pending, &oldest_seq, &oldest_age);
    printf("%s uptime_ms=%lld session=%u rssi=%d wifi_ip=%d wifi_disc=%u free=%u min_free=%u pending=%u oldest_seq=%" PRIu32
           " oldest_age_ms=%lld last_echo_age_ms=%lld last_mqtt_status=%d need_more_run=%u %s\n",
           kind, (long long)(now / 1000), (unsigned)s_session, wifi_rssi(), (int)s_wifi_has_ip, (unsigned)s_wifi_disconnects,
           (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size(), pending, oldest_seq,
           oldest_age < 0 ? -1LL : (long long)(oldest_age / 1000),
           s_last_echo_us ? (long long)((now - s_last_echo_us) / 1000) : -1LL, s_last_mqtt_status,
           (unsigned)s_need_more_bytes_run, transport);
}

static void diag_tick(int64_t now)
{
    if (now - s_last_diag_us >= DIAG_INTERVAL_US) {
        s_last_diag_us = now;
        log_diag("DIAG", now);
    }
}

typedef struct {
    int64_t start_us;
    int64_t transport_us;   /* connect start -> TCP+TLS established / QUIC ready, -1 if not reached */
    int64_t connack_us;     /* MQTT_Connect duration (CONNECT -> CONNACK), -1 if not reached */
    const char *fail;       /* NULL on success */
} open_result_t;

/* Open transport + MQTT session + subscription. initial=true is the unchanged first connection. */
static bool session_open(bool initial, open_result_t *r)
{
    r->start_us = esp_timer_get_time();
    r->transport_us = -1;
    r->connack_us = -1;
    r->fail = NULL;

    ESP_LOGI(TAG, "Connecting to %s server %s:%u", DEMO_TRANSPORT_NAME,
             server_info.pHostName, (unsigned)server_info.port);
    ESP_LOGI(TAG, "Free heap: %" PRIu32 " bytes", (uint32_t)esp_get_free_heap_size());
#if DEMO_TRANSPORT_TCP_TLS
    if (tcp_tls_client_connect(&server_info, 5000) != 0) {
        r->fail = "tcp_tls_connect";
        return false;
    }
#else
    static char port_text[16];
    snprintf(port_text, sizeof(port_text), "%u", (unsigned)server_info.port);
    static quic_client_config_t quic_config;
    quic_config.hostname = server_info.pHostName;
    quic_config.port = port_text;
    quic_config.alpn = server_info.pAlpn;
    if (quic_client_init_with_config(&quic_config) != 0) {
        ESP_LOGE(TAG, "QUIC initialization failed");
        r->fail = "quic_init";
        return false;
    }
    if (!wait_for_quic_ready()) {
        r->fail = "quic_handshake";
        return false;
    }
#endif
    r->transport_us = esp_timer_get_time() - r->start_us;
    ESP_LOGI(TAG, "%s connection established", DEMO_TRANSPORT_NAME);
    if (initial) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    memset(&s_network_context, 0, sizeof(s_network_context));
    if (demo_transport_init(&s_network_context, &server_info, &s_transport_config) != pdPASS) {
        ESP_LOGE(TAG, "MQTT transport initialization failed");
        r->fail = "transport_init";
        return false;
    }
    xTransportInterface.pNetworkContext = &s_network_context;
    xTransportInterface.recv = mqtt_quic_transport_recv;
    xTransportInterface.send = mqtt_quic_transport_send;

    MQTTFixedBuffer_t network_buffer = { .pBuffer = mqtt_buffer, .size = sizeof(mqtt_buffer) };
    MQTTStatus_t mqtt_status = MQTT_Init(&s_mqtt_context, &xTransportInterface, mqtt_get_time_ms,
                                         mqtt_event_callback, &network_buffer);
    if (mqtt_status != MQTTSuccess) {
        ESP_LOGE(TAG, "MQTT initialization failed: %d", (int)mqtt_status);
        r->fail = "mqtt_init";
        return false;
    }

    MQTTConnectInfo_t connect_info = {0};
    connect_info.cleanSession = true;
    connect_info.pClientIdentifier = MQTT_CLIENT_ID;
    connect_info.clientIdentifierLength = (uint16_t)strlen(MQTT_CLIENT_ID);
    bool session_present = false;
    int64_t connect_t0 = esp_timer_get_time();
    mqtt_status = MQTT_Connect(&s_mqtt_context, &connect_info, NULL, 5000, &session_present);
    if (mqtt_status != MQTTSuccess) {
        ESP_LOGE(TAG, "MQTT connection failed: %d", (int)mqtt_status);
        r->fail = "mqtt_connack";
        return false;
    }
    r->connack_us = esp_timer_get_time() - connect_t0;
    ESP_LOGI(TAG, "MQTT connected over %s", DEMO_TRANSPORT_NAME);

    MQTTSubscribeInfo_t subscription = {0};
    subscription.qos = MQTTQoS0;
    subscription.pTopicFilter = MQTT_TOPIC;
    subscription.topicFilterLength = (uint16_t)strlen(MQTT_TOPIC);
    mqtt_status = MQTT_Subscribe(&s_mqtt_context, &subscription, 1, 2);
    if (mqtt_status != MQTTSuccess) {
        ESP_LOGE(TAG, "Subscription failed: %d", (int)mqtt_status);
        r->fail = "subscribe";
        return false;
    }
    return true;
}

/* Clean close: MQTT DISCONNECT if the session was up, then TLS close_notify / QUIC CONNECTION_CLOSE and free. */
static void session_close(bool mqtt_up)
{
    ESP_LOGI(TAG, "Cleaning up %s connection", DEMO_TRANSPORT_NAME);
    if (mqtt_up && demo_client_is_connected()) {
        MQTTStatus_t st = MQTT_Disconnect(&s_mqtt_context);
        printf("MQTT_DISCONNECT_SENT status=%d\n", (int)st);
        /* Give the transport one cycle to put DISCONNECT on the wire before closing. */
        (void)demo_client_process();
    }
    demo_client_close_cleanup();
}

/* Runs one connected session; returns the failure reason. */
static const char *session_run(uint32_t *sequence)
{
    uint32_t loop_count = 0;
    int64_t last_publish_us = esp_timer_get_time();
#if FIXED_HEAPLOG
    static int64_t last_heaplog_us = 0;
    if (last_heaplog_us == 0) last_heaplog_us = last_publish_us;
#endif
    char payload[256];
    s_need_more_bytes_run = 0;
    s_last_mqtt_status = 0;

    while (demo_client_is_connected()) {
        vTaskDelay(pdMS_TO_TICKS(20));
        loop_count++;

        /* Service the selected transport at the unchanged application cadence. */
        if (loop_count % 25 == 0) {
            if (demo_client_process() != 0) {
                ESP_LOGW(TAG, "%s process returned an error", DEMO_TRANSPORT_NAME);
                log_diag("FAIL_DIAG", esp_timer_get_time());
                return "transport_process_error";
            }
        }

        /* Read subscription acknowledgments and returned messages. */
        if (loop_count % 5 == 0) {
            MQTTStatus_t mqtt_status = MQTT_ProcessLoop(&s_mqtt_context);
            s_last_mqtt_status = (int)mqtt_status;
            if (mqtt_status != MQTTSuccess) {
                ESP_LOGW(TAG, "MQTT process returned: %d", (int)mqtt_status);
            }
            if (mqtt_status == MQTTNeedMoreBytes) {
                s_need_more_bytes_run++;
            } else {
                s_need_more_bytes_run = 0;
            }
            if (mqtt_status == MQTTKeepAliveTimeout) {
                log_diag("FAIL_DIAG", esp_timer_get_time());
                return "mqtt_keepalive_timeout";
            }
            if (mqtt_status != MQTTSuccess && mqtt_status != MQTTNeedMoreBytes) {
                log_diag("FAIL_DIAG", esp_timer_get_time());
                return "mqtt_process_error";
            }
        }

        if (!demo_client_is_connected()) {
            break;
        }

        int64_t now_us = esp_timer_get_time();
#if FIXED_HEAPLOG
        if (now_us - last_heaplog_us >= 60000000LL) {
            last_heaplog_us = now_us;
            printf("HEAPLOG uptime_s=%lld free=%u min_free=%u\n", (long long)(now_us / 1000000LL),
                           (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size());
        }
#endif
        diag_tick(now_us);

        /* Application-level stall check: an echo is overdue by 15 s. */
        unsigned pending; uint32_t oldest_seq; int64_t oldest_age;
        rtt_pending_stats(now_us, &pending, &oldest_seq, &oldest_age);
        if (oldest_age >= STALL_TIMEOUT_US) {
            log_diag("STALL", now_us);
            return "stall";
        }

        if (now_us - last_publish_us >= PUBLISH_INTERVAL_US) {
            last_publish_us = now_us;

            int length = make_sensor_payload(payload, sizeof(payload), *sequence);

            if (length > 0 && (size_t)length < sizeof(payload)) {
                MQTTPublishInfo_t publication = {0};
                publication.qos = MQTTQoS0;
                publication.pTopicName = MQTT_TOPIC;
                publication.topicNameLength = (uint16_t)strlen(MQTT_TOPIC);
                publication.pPayload = payload;
                publication.payloadLength = (size_t)length;

                pending_rtt_t *rtt_entry = app_rtt_reserve(*sequence);
                rtt_entry->send_time_us = esp_timer_get_time();
                MQTTStatus_t mqtt_status = MQTT_Publish(&s_mqtt_context, &publication, 0);

                if (mqtt_status == MQTTSuccess) {
                    MEASUREMENT_LOGI(TAG, "Published sensor seq=%" PRIu32, *sequence);
                } else {
                    rtt_entry->state = RTT_FAILED;
                    ESP_LOGW(TAG, "Sensor publish failed: %d", (int)mqtt_status);
                    printf("APP_RTT_LOST seq=%" PRIu32 " reason=publish_failed\n", *sequence);
                    (*sequence)++;
                    log_diag("FAIL_DIAG", esp_timer_get_time());
                    return "publish_failed";
                }
            } else {
                ESP_LOGE(TAG, "Sensor message exceeded its buffer");
            }

            (*sequence)++;
        }
    }
    log_diag("FAIL_DIAG", esp_timer_get_time());
    return "transport_closed";
}

static void quic_sensor_task(void *argument)
{
    (void)argument;
    uint32_t sequence = 1;
    uint32_t reconnects = 0;
    open_result_t r;

    bool up = session_open(true, &r);
    if (up) {
        printf("CONNECT session=0 initial=1 transport_ms=%.1f connack_ms=%.1f\n",
               r.transport_us / 1000.0, r.connack_us / 1000.0);
        ESP_LOGI(TAG, "Starting DHT11 readings every five seconds");
    } else {
        printf("CONNECT session=0 initial=1 result=FAIL stage=%s\n", r.fail);
    }
    s_last_diag_us = esp_timer_get_time();

    for (;;) {
        const char *reason;
        int64_t fail_us;
        if (up) {
            reason = session_run(&sequence);
            fail_us = esp_timer_get_time();
            printf("CONNECTION_FAILED uptime_ms=%lld session=%u reason=%s next_seq=%" PRIu32 "\n",
                   (long long)(fail_us / 1000), (unsigned)s_session, reason, sequence);
            rtt_drop_pending(reason);
            session_close(true);
        } else {
            reason = r.fail ? r.fail : "connect_failed";
            fail_us = esp_timer_get_time();
            session_close(false);
        }

        /* Reconnect with backoff 1, 2, 4, 8, 16, 30, 30 ... s; Wi-Fi is not restarted. */
        reconnects++;
        printf("RECONNECT_START n=%u reason=%s fail_uptime_ms=%lld\n", (unsigned)reconnects, reason,
               (long long)(fail_us / 1000));
        unsigned attempt = 0;
        int64_t first_start_us = -1;
        do {
            attempt++;
            uint32_t backoff_ms = attempt >= 6 ? RECONNECT_MAX_BACKOFF_MS : (1000u << (attempt - 1));
            if (backoff_ms > RECONNECT_MAX_BACKOFF_MS) backoff_ms = RECONNECT_MAX_BACKOFF_MS;
            vTaskDelay(pdMS_TO_TICKS(backoff_ms));
            int64_t wait_start = esp_timer_get_time(), last_kick = wait_start;
            while (!s_wifi_has_ip) {
                vTaskDelay(pdMS_TO_TICKS(500));
                int64_t now = esp_timer_get_time();
                diag_tick(now);
                if (now - last_kick >= WIFI_KICK_INTERVAL_US) {
                    last_kick = now;
                    esp_err_t e = esp_wifi_connect();
                    printf("WIFI_KICK uptime_ms=%lld waited_ms=%lld esp_wifi_connect=%s\n", (long long)(now / 1000),
                           (long long)((now - wait_start) / 1000), esp_err_to_name(e));
                }
            }
            up = session_open(false, &r);
            if (first_start_us < 0) first_start_us = r.start_us;
            if (!up) {
                printf("RECONNECT_ATTEMPT n=%u attempt=%u result=FAIL stage=%s start_uptime_ms=%lld elapsed_ms=%.1f\n",
                       (unsigned)reconnects, attempt, r.fail, (long long)(r.start_us / 1000),
                       (esp_timer_get_time() - r.start_us) / 1000.0);
                session_close(false);
            }
        } while (!up);

        int64_t connected_us = esp_timer_get_time();
        s_session++;
        printf("RECONNECT n=%u session=%u attempts=%u reason=%s fail_uptime_ms=%lld start_uptime_ms=%lld"
               " last_start_uptime_ms=%lld connected_uptime_ms=%lld handshake_ms=%.1f connack_ms=%.1f"
               " attempt_total_ms=%.1f downtime_ms=%.1f free=%u next_seq=%" PRIu32 "\n",
               (unsigned)reconnects, (unsigned)s_session, attempt, reason, (long long)(fail_us / 1000),
               (long long)(first_start_us / 1000), (long long)(r.start_us / 1000), (long long)(connected_us / 1000),
               r.transport_us / 1000.0, r.connack_us / 1000.0, (connected_us - r.start_us) / 1000.0,
               (connected_us - fail_us) / 1000.0, (unsigned)esp_get_free_heap_size(), sequence);
    }
}


#if FIXED_CT_MODE
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
/* TEST ONLY cycle task (not present in measurement images): QUIC connect, wait for handshake, then reboot (mode 1)
 * or close and reconnect (mode 2). Counters live in NVS so crashes (reboot) are counted: started - passed - failed. */
static void test_cycle_task(void *argument)
{
    (void)argument;
    nvs_handle_t h;
    char ns[16];
    snprintf(ns, sizeof(ns), "tf%s", FIXED_TEST_RUN_ID);
    uint32_t started = 0, passed = 0, failed = 0, init_failed = 0;
    ESP_ERROR_CHECK(nvs_open(ns, NVS_READWRITE, &h));
    (void)nvs_get_u32(h, "started", &started);
    (void)nvs_get_u32(h, "passed", &passed);
    (void)nvs_get_u32(h, "failed", &failed);
    (void)nvs_get_u32(h, "initfail", &init_failed);
    esp_rom_printf("TEST RESUME run=%s mode=%d started=%u passed=%u failed=%u init_failed=%u crashed_so_far=%d\n", FIXED_TEST_RUN_ID,
                   FIXED_TEST_MODE, (unsigned)started, (unsigned)passed, (unsigned)failed, (unsigned)init_failed,
                   (int)started - (int)passed - (int)failed);
    char port_text[16];
    snprintf(port_text, sizeof(port_text), "%u", (unsigned)server_info.port);
    quic_client_config_t quic_config = {.hostname = server_info.pHostName, .port = port_text, .alpn = server_info.pAlpn};
    while (started < FIXED_TEST_CYCLES) {
        started++;
        ESP_ERROR_CHECK(nvs_set_u32(h, "started", started));
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("TEST CYCLE %u START mode=%d free_heap=%u\n", (unsigned)started, FIXED_TEST_MODE, (unsigned)esp_get_free_heap_size());
        bool init_ok = quic_client_init_with_config(&quic_config) == 0;
        bool ok = init_ok && wait_for_quic_ready();
        if (ok) {
            vTaskDelay(pdMS_TO_TICKS(1000));
            passed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "passed", passed));
        } else {
            failed++;
            ESP_ERROR_CHECK(nvs_set_u32(h, "failed", failed));
            if (!init_ok) {
                init_failed++;
                ESP_ERROR_CHECK(nvs_set_u32(h, "initfail", init_failed));
            }
        }
        ESP_ERROR_CHECK(nvs_commit(h));
        esp_rom_printf("TEST CYCLE %u %s\n", (unsigned)started, ok ? "PASS" : (init_ok ? "FAIL_HANDSHAKE_TIMEOUT" : "FAIL_CLIENT_INIT"));
        if (FIXED_TEST_MODE == 1) {
            esp_rom_printf("TEST REBOOTING\n");
            vTaskDelay(pdMS_TO_TICKS(200));
            esp_restart();
        }
        quic_client_cleanup();
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
    esp_rom_printf("TEST COMPLETE run=%s mode=%d cycles=%d started=%u passed=%u failed=%u init_failed=%u crashed=%d free_heap=%u\n",
                   FIXED_TEST_RUN_ID, FIXED_TEST_MODE, FIXED_TEST_CYCLES, (unsigned)started, (unsigned)passed, (unsigned)failed,
                   (unsigned)init_failed, (int)started - (int)passed - (int)failed, (unsigned)esp_get_free_heap_size());
    nvs_close(h);
    vTaskDelete(NULL);
}
#endif

void app_main(void)
{
    ESP_LOGI(TAG, "Starting ESP32-C6 DHT11 over %s", DEMO_TRANSPORT_NAME);
    ESP_LOGI(TAG, "ESP-IDF version: %s", esp_get_idf_version());

    /* DHT11 DATA = GPIO4, VCC = 3V3, GND = GND. */
    ESP_ERROR_CHECK(gpio_reset_pin(DHT_GPIO));
    ESP_ERROR_CHECK(
        gpio_set_pull_mode(DHT_GPIO, GPIO_PULLUP_ONLY)
    );

    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    /* Uses the Wi-Fi credentials saved in menuconfig. */
    ESP_ERROR_CHECK(example_connect());

    ESP_LOGI(TAG, "Wi-Fi connected");

#if DEMO_WIFI_PS_NONE
    /* Optional experimental profile, shared by QUIC and TCP_TLS. */
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    wifi_ps_type_t returned_ps_mode;
    ESP_ERROR_CHECK(esp_wifi_get_ps(&returned_ps_mode));
    const char *returned_ps_name =
        returned_ps_mode == WIFI_PS_NONE ? "WIFI_PS_NONE" :
        returned_ps_mode == WIFI_PS_MIN_MODEM ? "WIFI_PS_MIN_MODEM" :
        returned_ps_mode == WIFI_PS_MAX_MODEM ? "WIFI_PS_MAX_MODEM" : "UNKNOWN";
    ESP_LOGI(TAG, "EXPERIMENTAL Wi-Fi profile: requested=WIFI_PS_NONE(%d), returned=%s(%d)",
             (int)WIFI_PS_NONE, returned_ps_name, (int)returned_ps_mode);
    ESP_ERROR_CHECK(returned_ps_mode == WIFI_PS_NONE ? ESP_OK : ESP_ERR_INVALID_STATE);
#endif

#if !FIXED_CT_MODE && !FIXED_TEST_MODE
    /* RECONNECT PROFILE: Wi-Fi event logging (in addition to the example's own handlers). */
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_DISCONNECTED, wifi_diag_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_CONNECTED, wifi_diag_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_diag_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_LOST_IP, wifi_diag_event, NULL));
    printf("WIFI_EVENT start uptime_ms=%lld rssi=%d\n", uptime_ms(), wifi_rssi());
#endif

    BaseType_t task_status = xTaskCreate(
#if FIXED_CT_MODE
        ct_task,
#elif FIXED_TEST_MODE
        test_cycle_task,
#else
        quic_sensor_task,
#endif
        "quic_dht11",
        28 * 1024,
        NULL,
        5,
        NULL
    );

    if (task_status != pdPASS) {
        ESP_LOGE(TAG, "Not enough memory to start QUIC task");
    }
}
