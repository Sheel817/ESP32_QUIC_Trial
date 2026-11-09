# The following lines of boilerplate have to be in your project's
# CMakeLists in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.16)

# TEST_ONLY: use existing private dependency copies without dependency resolution.
set(EXTRA_COMPONENT_DIRS "${CMAKE_SOURCE_DIR}/managed_components"
    "$ENV{IDF_PATH}/examples/common_components/protocol_examples_common")
set(PROJECT_VER "3c8c7a3-dirty-TEST_ONLY")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
add_compile_definitions(WOLFSSL_QUIC MICRO_SESSION_CACHE HAVE_ALPN OPENSSL_ALL)
# "Trim" the build. Include the minimal set of components, main, and anything it depends on.
idf_build_set_property(MINIMAL_BUILD OFF)
project(quic_demo)
# Compatibility for the bundled wolfSSL port with ESP-IDF 6.x.
# Its hardware crypto port uses APIs removed from IDF 6; use software crypto.
idf_component_get_property(wolfssl_lib wolfssl__wolfssl COMPONENT_LIB)
target_compile_definitions(${wolfssl_lib} PUBLIC
    NO_ESP32_CRYPT
    NO_WOLFSSL_ESP32_CRYPT_HASH
    NO_WOLFSSL_ESP32_CRYPT_AES
    NO_WOLFSSL_ESP32_CRYPT_RSA_PRI)
# The bundled port uses thread_local as an identifier (a keyword in C23).
target_compile_options(${wolfssl_lib} PRIVATE -std=gnu17)
