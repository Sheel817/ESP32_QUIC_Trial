#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/ssl.h>
#include <wolfssl/quic.h>
#include <wolfssl/openssl/evp.h>
#include <wolfssl/openssl/hmac.h>
#include <wolfssl/wolfcrypt/aes.h>
#include <wolfssl/wolfcrypt/chacha.h>
#include <wolfssl/wolfcrypt/poly1305.h>
#include <wolfssl/wolfcrypt/random.h>
#define S(T) char sz_##T[sizeof(T)];
#ifdef HAVE_CHACHA
S(ChaCha)
#endif
#ifdef HAVE_POLY1305
S(Poly1305)
#endif
S(WOLFSSL_EVP_CIPHER_CTX) S(WOLFSSL_EVP_MD_CTX) S(WOLFSSL_EVP_PKEY) S(WOLFSSL_HMAC_CTX) S(WOLFSSL_QUIC_METHOD) S(Aes) S(WC_RNG)
#ifdef HAVE_AESGCM
char flag_HAVE_AESGCM;
#endif
#ifdef HAVE_AESCCM
char flag_HAVE_AESCCM;
#endif
#ifdef HAVE_AES_ECB
char flag_HAVE_AES_ECB;
#endif
#ifdef HAVE_CHACHA
char flag_HAVE_CHACHA;
#endif
#ifdef HAVE_POLY1305
char flag_HAVE_POLY1305;
#endif
#ifdef WOLFSSL_KEY_GEN
char flag_WOLFSSL_KEY_GEN;
#endif
#ifdef OPENSSL_EXTRA
char flag_OPENSSL_EXTRA;
#endif
#ifdef OPENSSL_ALL
char flag_OPENSSL_ALL;
#endif
#ifdef HAVE_SNI
char flag_HAVE_SNI;
#endif
#ifdef WOLFSSL_SNI
char flag_WOLFSSL_SNI;
#endif
#ifdef HAVE_ALPN
char flag_HAVE_ALPN;
#endif
#ifdef HAVE_SESSION_TICKET
char flag_HAVE_SESSION_TICKET;
#endif
#ifdef NO_SESSION_CACHE
char flag_NO_SESSION_CACHE;
#endif
#ifdef WOLFSSL_SMALL_STACK
char flag_WOLFSSL_SMALL_STACK;
#endif
#ifdef WOLFSSL_TLS13
char flag_WOLFSSL_TLS13;
#endif
#ifdef WOLFSSL_EVP_INCLUDED
char flag_WOLFSSL_EVP_INCLUDED;
#endif
#ifdef WOLFSSL_HAVE_EVP_PKEY
char flag_WOLFSSL_HAVE_EVP_PKEY;
#endif
#ifdef WOLFSSL_EARLY_DATA
char flag_WOLFSSL_EARLY_DATA;
#endif
#ifdef WOLFSSL_QUIC
char flag_WOLFSSL_QUIC;
#endif
