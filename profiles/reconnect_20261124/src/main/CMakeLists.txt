set(DEMO_TRANSPORT "TCP_TLS" CACHE STRING "Measurement transport: QUIC or TCP_TLS")
option(DEMO_WIFI_PS_NONE "Experimental profile: disable Wi-Fi power saving after connection" OFF)
set_property(CACHE DEMO_TRANSPORT PROPERTY STRINGS QUIC TCP_TLS)
if(NOT DEMO_TRANSPORT STREQUAL "QUIC" AND NOT DEMO_TRANSPORT STREQUAL "TCP_TLS")
    message(FATAL_ERROR "DEMO_TRANSPORT must be QUIC or TCP_TLS")
endif()

idf_component_register(
    SRCS 
        "quic_demo_main.c"
        "ngtcp2_sample.c" 
        "esp_ev_compat.c"
        "mqtt_quic_transport.c"
        "mqtt_tcp_tls_transport.c"
        "tls_negotiation.c"
        "quic_internal_diag.c"
    PRIV_REQUIRES
        spi_flash 
        nvs_flash
    REQUIRES 
        ngtcp2 
        wolfssl__wolfssl 
        coreMQTT
        esp_timer
        esp_wifi
        protocol_examples_common
        esp-idf-lib__dht
        espressif__cjson
    INCLUDE_DIRS "")

if(DEMO_TRANSPORT STREQUAL "TCP_TLS")
    target_compile_definitions(${COMPONENT_LIB} PRIVATE DEMO_TRANSPORT_TCP_TLS=1)
else()
    target_compile_definitions(${COMPONENT_LIB} PRIVATE DEMO_TRANSPORT_TCP_TLS=0)
endif()
message(STATUS "Measurement transport: ${DEMO_TRANSPORT}")
# RECONNECT PROFILE: ngtcp2 internal headers for read-only connection/stream diagnostics.
set_source_files_properties(quic_internal_diag.c PROPERTIES INCLUDE_DIRECTORIES "${CMAKE_CURRENT_LIST_DIR}/../components/ngtcp2/ngtcp2/lib")
set(FIXED_TEST_MODE "0" CACHE STRING "TEST ONLY: 0=measurement image (default), 1=reboot cycles, 2=soft reconnect cycles")
set(FIXED_TEST_CYCLES "30" CACHE STRING "TEST ONLY: cycles")
set(FIXED_TEST_RUN_ID "f0" CACHE STRING "TEST ONLY: NVS namespace suffix")
set(FIXED_CT_MODE "0" CACHE STRING "1=connection-time test image (50 attempts)")
set(FIXED_HEAPLOG "0" CACHE STRING "1=log free/min free heap every 60 s in the normal sensor loop")
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    DEMO_WIFI_PS_NONE=$<BOOL:${DEMO_WIFI_PS_NONE}>
    FIXED_CT_MODE=${FIXED_CT_MODE} FIXED_HEAPLOG=${FIXED_HEAPLOG} FIXED_TEST_MODE=${FIXED_TEST_MODE} FIXED_TEST_CYCLES=${FIXED_TEST_CYCLES} "FIXED_TEST_RUN_ID=\"${FIXED_TEST_RUN_ID}\"")
message(STATUS "Experimental Wi-Fi power-saving-off profile: ${DEMO_WIFI_PS_NONE}")
