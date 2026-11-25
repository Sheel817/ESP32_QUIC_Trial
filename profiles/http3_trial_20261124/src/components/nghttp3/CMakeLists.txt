# HTTP3 TRIAL PROFILE: ESP-IDF wrapper for nghttp3 v1.10.1 (released with ngtcp2 v1.13.0, May 2025).
# Same pattern as components/ngtcp2/CMakeLists.txt: static library, generated config.h and version.h.
file(GLOB NGHTTP3_SRCS "nghttp3/lib/*.c")
list(APPEND NGHTTP3_SRCS "nghttp3/lib/sfparse/sfparse.c")

set(PACKAGE_VERSION "1.10.1")
set(PACKAGE_VERSION_NUM "0x010a01")
configure_file("${CMAKE_CURRENT_LIST_DIR}/nghttp3/lib/includes/nghttp3/version.h.in"
               "${CMAKE_CURRENT_BINARY_DIR}/gen/nghttp3/version.h" @ONLY)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/gen/config.h"
     "#define HAVE_ARPA_INET_H 1\n"
     "#define HAVE_NETINET_IN_H 1\n"
     "#define HAVE_UNISTD_H 1\n"
     "#define HAVE_ENDIAN_H 1\n"
     "#define HAVE_DECL_BE64TOH 1\n"
     "#define HAVE_DECL_BSWAP_64 0\n")

idf_component_register(SRCS ${NGHTTP3_SRCS}
                       INCLUDE_DIRS "nghttp3/lib/includes" "${CMAKE_CURRENT_BINARY_DIR}/gen"
                       PRIV_INCLUDE_DIRS "nghttp3/lib" "nghttp3/lib/sfparse"
                       REQUIRES lwip)
target_compile_definitions(${COMPONENT_LIB} PUBLIC NGHTTP3_STATICLIB)
target_compile_definitions(${COMPONENT_LIB} PRIVATE HAVE_CONFIG_H)
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-error=maybe-uninitialized -Wno-error=unused-function
                       -Wno-error=format)  # nghttp3 debug prints use %u for uint32_t (long on RISC-V)
