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
    PRIV_REQUIRES 
        spi_flash 
        nvs_flash
    REQUIRES 
        ngtcp2 
        wolfssl 
        coreMQTT
        esp_timer
        esp_wifi
        protocol_examples_common
    INCLUDE_DIRS "")

if(DEMO_TRANSPORT STREQUAL "TCP_TLS")
    target_compile_definitions(${COMPONENT_LIB} PRIVATE DEMO_TRANSPORT_TCP_TLS=1)
else()
    target_compile_definitions(${COMPONENT_LIB} PRIVATE DEMO_TRANSPORT_TCP_TLS=0)
endif()
message(STATUS "Measurement transport: ${DEMO_TRANSPORT}")
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    DEMO_WIFI_PS_NONE=$<BOOL:${DEMO_WIFI_PS_NONE}>)
message(STATUS "Experimental Wi-Fi power-saving-off profile: ${DEMO_WIFI_PS_NONE}")
