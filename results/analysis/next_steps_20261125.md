# Next steps (25 Nov 2026): session resumption / 0-RTT, and HTTP/3 status

Planning only. Nothing was built, flashed or changed for this document. The findings below come from:
- the build that runs today: `profiles/reconnect_20261124`, its `build_fq3` library symbols and its sources;
- the installed server stack: `.quic-venv` with aioquic 1.7.0, and Python `ssl` on OpenSSL 3.5.7.

## 1. Session resumption and 0-RTT

### 1.1 What the current stack supports

| component | session resumption (PSK from a ticket) | 0-RTT / early data | evidence |
|---|---|---|---|
| wolfSSL 5.8.0 (managed component, `user_settings.h` + our CMake defines) | **compiled in.** `HAVE_SESSION_TICKET` is set because `NO_SESSION_CACHE` is not defined. `MICRO_SESSION_CACHE` holds 1 server-side entry; it does not matter for a client. | **not compiled in.** `WOLFSSL_EARLY_DATA` is not defined anywhere. | `libwolfssl__wolfssl.a` exports `wolfSSL_UseSessionTicket`, `wolfSSL_get1_session`, `wolfSSL_set_session`, `wolfSSL_i2d/d2i_SSL_SESSION`, `wolfSSL_CTX_sess_set_new_cb`. It does **not** export `wolfSSL_set_quic_early_data_enabled` or `wolfSSL_write_early_data`. |
| ngtcp2 1.13.0 crypto backend (`crypto/wolfssl/wolfssl.c`) | **yes.** `ngtcp2_crypto_wolfssl_configure_client_context` already calls `wolfSSL_CTX_UseSessionTicket`, so our ClientHello already asks for tickets. | **yes in the library** (0-RTT encryption level mapped, `ngtcp2_conn_encode_0rtt_transport_params`, `..._decode_and_set_0rtt_transport_params`, `tls_early_data_rejected` callback). It needs wolfSSL built with `WOLFSSL_EARLY_DATA`. | ngtcp2's own `examples/tls_client_session_wolfssl.cc` does exactly this flow: `d2i_SSL_SESSION` → `set_session` → `set_quic_early_data_enabled`. |
| our QUIC client (`ngtcp2_sample.c`) | **not used.** A new `SSL_CTX`/`SSL` is made for each connection; no session is kept. | not used. Streams are opened and MQTT CONNECT is sent only after the handshake (`wait_for_quic_ready`). | lines 245–257, 403–441 |
| aioquic 1.7.0 server (`quic_server.py`) | **supported, but off.** Tickets are issued only if `serve()` gets `session_ticket_handler`, and resumed only with `session_ticket_fetcher`. Our server passes neither. | **supported.** Tickets carry `max_early_data = 0xffffffff` as QUIC requires, and 0-RTT stream data reaches the protocol as normal stream events. **No anti-replay protection.** | `asyncio/server.py:66–76`, `quic/connection.py:1782–1841` |
| our TCP+TLS client (`mqtt_tcp_tls_transport.c`) | **not used.** A new `CTX`/`SSL` per connection, and `wolfSSL_Cleanup()` on every close. | not used | lines 71–131 |
| Python `ssl` server (`tcp_tls_server.py`, OpenSSL 3.5.7) | **on by default.** TLS 1.3 tickets, `num_tickets = 2`, stateless with a random key per `SSLContext`. | **not possible.** The Python `ssl` module has no early-data API. | `SSLContext().num_tickets == 2` |

PSK mode: aioquic only offers `psk_dhe_ke`, so a resumed handshake **still performs ECDHE**; it skips only the certificate and CertificateVerify. Python/OpenSSL also uses `psk_dhe_ke` by default.

### 1.2 Code changes needed

**A. QUIC session resumption, 1-RTT. About 8–12 h including tests.**
1. Client (`ngtcp2_sample.c`):
   - Register `wolfSSL_CTX_sess_set_new_cb`. In the callback, serialize the session with `wolfSSL_i2d_SSL_SESSION` into a static RAM buffer (about 0.3–1 KB).
   - On reconnect, `wolfSSL_d2i_SSL_SESSION` + `wolfSSL_set_session` before `ngtcp2_conn_client_new` hands the SSL to ngtcp2.
   - Log `resumed=wolfSSL_session_reused()` in `CONNECT`/`RECONNECT`.
   - Keep it in RAM only (no NVS), so it survives a reconnect but not a reboot. 3–4 h.
2. Server (`quic_server.py`):
   - Add `session_ticket_handler` / `session_ticket_fetcher` with a dict.
   - For server-restart tests, optionally store the tickets in a file (test-only: the file holds resumption secrets).
   - Log `resumed`. 1–2 h.
3. `analyze_cycles.py` / `analyze_reconnect.py`: a `resumed` column and stats split by full and resumed handshake. 1–2 h.
4. Smoke test plus 20 cycles. 3–4 h.

**B. QUIC 0-RTT on top of A. About 11–17 h more.**
1. Build:
   - Define `WOLFSSL_EARLY_DATA` for the wolfSSL library (top-level `CMakeLists.txt`, `target_compile_definitions(${wolfssl_lib} …)`).
   - Define it identically for ngtcp2 and `main`, so every unit sees the same wolfSSL headers.
   - 1–2 h, plus checking image and heap size.
2. Client:
   - Save the 0-RTT transport parameters with `ngtcp2_conn_encode_0rtt_transport_params` together with the session.
   - On reconnect: `ngtcp2_conn_decode_and_set_0rtt_transport_params`, `wolfSSL_set_quic_early_data_enabled(ssl, 1)`, then open the MQTT stream **before** the handshake completes and send CONNECT as early data.
   - This is the main change. `session_open` currently waits for "QUIC ready" and then calls the blocking `MQTT_Connect`. Both the call order and the transport send path (which must accept writes before the handshake is confirmed) have to change.
   - Implement `tls_early_data_rejected`: reset the stream state and resend CONNECT in 1-RTT.
   - Only CONNECT (and perhaps SUBSCRIBE) may go into 0-RTT, never PUBLISH, because of replay.
   - 6–10 h.
3. Server:
   - aioquic needs no protocol change.
   - Log whether CONNECT arrived in 0-RTT (`early_data_accepted` in the `HandshakeCompleted` event).
   - 1 h.
4. Logging, analysis and the 20-cycle test: 3–4 h.

**C. TCP+TLS session resumption (TLS 1.3 PSK, 1-RTT). About 6–8 h.**
1. Client (`mqtt_tcp_tls_transport.c`):
   - In TLS 1.3 the ticket arrives *after* the handshake, with the first `wolfSSL_read`. Capture it via `wolfSSL_CTX_sess_set_new_cb` or `wolfSSL_get1_session` after the first read.
   - Serialize it with `i2d` into a RAM buffer. Do not keep a `WOLFSSL_SESSION*`, because the close path calls `wolfSSL_Cleanup()`.
   - On reconnect, `d2i` + `wolfSSL_set_session` before `wolfSSL_connect`.
   - Log `resumed`.
   - 3–4 h.
2. Server: nothing is needed to resume. Logging `ssl_object.session_reused` takes 0.5 h.
3. Logging and test: 2–3 h.

**D. TCP+TLS 0-RTT: not recommended.** Python `ssl` cannot accept early data. It would need a different server (a C server on OpenSSL or wolfSSL with early data, plus an MQTT broker logic port) and `wolfSSL_write_early_data` on the client, about 12–20 h. Without it, the realistic comparison is **QUIC 0-RTT vs. TLS 1.3 resumption (1-RTT)**. That is also the deployed reality for MQTT over TCP+TLS.

**Total.** A + C (symmetric resumption for both protocols): **about 14–20 h**. Adding B (QUIC 0-RTT): **about 25–37 h**.

### 1.3 Risks and caveats
1. **The test design must keep server state.**
   - The current reconnect test kills the server process. Python `ssl` ticket keys are random per process, and aioquic's ticket store is in memory. After a restart, every ticket is invalid on both sides and every reconnect falls back to a full handshake.
   - Resumption tests need a **network outage with the server kept alive**, for example blocking the board's traffic for N s on the laptop (firewall rule or Clumsy drop) or stopping and starting the board's Wi-Fi association.
   - The aioquic store can be persisted for tests; Python `ssl` ticket keys cannot be set through the stdlib API.
2. **The gain may be small compared with today's handshake time.**
   - Measured last night: QUIC handshake about 2.7–2.8 s; TCP+TLS connect about 1.55 s; network RTT median 65 ms.
   - Resumption with `psk_dhe_ke` still does ECDHE on the ESP32-C6. It saves the certificate transfer and parsing, and the server's signature (which costs the laptop, not the board).
   - 0-RTT saves about one RTT before CONNECT.
   - Unless most of the 2.7 s is certificate handling, the improvement could be tens to a few hundred ms. **Recommended step 0 (2–3 h, no protocol change):** time the handshake phases on the board (ClientHello sent, ServerHello received, keys derived, handshake done) to find where the 2.7 s goes, and why QUIC takes about 1.2 s longer than TCP+TLS. The 9.9 s smoke-test handshake (cwnd 4,200, srtt 423 ms) also points to packet-level effects worth checking first.
3. **wolfSSL configuration consistency.** `WOLFSSL_EARLY_DATA` changes internal structures. It must be defined the same way for the wolfSSL library, the ngtcp2 crypto backend and `main`. A mismatch builds without error and fails at run time. Today the defines are spread over `CMakeLists.txt`, `components/ngtcp2/CMakeLists.txt` and `user_settings.h`.
4. **Replay.** aioquic has no 0-RTT anti-replay. A replayed MQTT CONNECT is mostly harmless (it replaces the session), but a replayed PUBLISH is not. This is why 0-RTT is limited to CONNECT/SUBSCRIBE, and it should be stated in the thesis.
5. **Memory.** A serialized session plus 0-RTT parameters is about 1 KB, against a minimum free heap of 142,684 B in the 8 h run. Small, but heap has to be re-measured with `WOLFSSL_EARLY_DATA`.
6. **Fairness.** QUIC can get 0-RTT and TCP+TLS cannot with our server. Results should be reported as three variants: full handshake (both), resumed 1-RTT (both), QUIC 0-RTT.
7. **Profiles.** This needs a new profile (for example `profiles/resumption_<date>/`) copied from `reconnect_20261124`. The fixed and reconnect profiles stay frozen.

## 2. HTTP/3 Track B: status (unchanged since 24 Nov)
- **Profile:** `profiles/http3_trial_20261124`, committed in `c4c1b7e34` / `c160030de` on `long-run-reconnect`.
  - nghttp3 v1.10.1 (released with ngtcp2 v1.13.0). The library source is not committed; the README has the clone command.
  - ESP-IDF wrapper component, minimal HTTP/3 client (`http3_client.c`: handshake with ALPN `h3`, control and QPACK streams, one `GET /`, `H3_RESULT` line).
  - Factory partition 1700K → 3M.
- **Builds:** yes. Image `h3a` builds with exit 0 (the first attempt failed on `-Werror=format` in nghttp3 debug prints; fixed in the wrapper flags, library unchanged).
- **Image size:** 1,670,576 B (sha256 `5158d61d…320724`, rechecked today).
  - 3 MB partition: 1,475,152 B (47 %) free. It would also fit the old 1700K partition, at 96 %.
  - About 4.9 MB of the 8 MB flash is unallocated.
  - nghttp3 adds 87,215 B (83.6 KB flash, 3.6 KB RAM); the image is +32,960 B against fq2 because coreMQTT drops out. Static DIRAM 145,319 / 452,112 B.
- **Never flashed or run.**
- **Still missing:**
  1. An HTTP/3 server on the laptop. Our `quic_server.py` speaks MQTT (ALPN `mqtt`). aioquic in `.quic-venv` includes an HTTP/3 stack (`aioquic.h3`); a small server on UDP 4433 with ALPN `h3` would take about 2–3 h.
  2. A first hardware run: runtime heap and stack of nghttp3 are unknown, and the code paths are unexercised. 2–4 h including fixes.
  3. A measurement harness: RTT/heap logging, repeated requests, the reconnect logic, and integration with the libev compatibility layer. 6–10 h.
  4. Certificate verification is off (`VERIFY_NONE`), as in the MQTT experiments.
  5. No POST/request body, no 0-RTT or resumption (the same work as section 1 B would apply), no GOAWAY handling.
