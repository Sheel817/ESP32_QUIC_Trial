# HTTP/3 trial profile (24 Nov 2026) — build only, NOT flashed, NOT run

Base: copy of `profiles/fixed_20261118` (ngtcp2 v1.13.0 + wolfSSL, fixed alignment / UDP close). Nothing in that profile was changed.

## What was added
- `src/components/nghttp3/nghttp3`: nghttp3 **v1.10.1** (git tag, commit df0d504b, 27 May 2025, with `lib/sfparse`).
  Chosen because it was released together with ngtcp2 v1.13.0 (26 May 2025); ngtcp2 itself only requires nghttp3 ≥ 1.0.0.
  nghttp3 does not link against ngtcp2; the two meet in the application glue.
  The library source is not committed. To rebuild, run
  `git clone --recurse-submodules --branch v1.10.1 https://github.com/ngtcp2/nghttp3 src/components/nghttp3/nghttp3` in this profile.
- `src/components/nghttp3/CMakeLists.txt`: ESP-IDF wrapper (same pattern as the ngtcp2 wrapper: generated `config.h`
  with `HAVE_DECL_BE64TOH`, generated `version.h`, static library). Library source is unmodified; `-Wno-error=format`
  because two debug prints use `%u` for `uint32_t` (which is `long` on RISC-V).
- `src/main/http3_client.c/.h`: minimal HTTP/3 client, one synchronous task, modelled on the ngtcp2 example client glue:
  UDP + select(), QUIC handshake (ALPN `h3`), HTTP/3 control + QPACK encoder/decoder uni streams, one `GET /`,
  counts response headers/body, sends CONNECTION_CLOSE, logs `H3_RESULT` (handshake ms, request→headers ms, total ms,
  heap). 5 attempts, 3 s apart. QPACK dynamic table off. Server address `192.168.137.1:4433` (compile-time macro).
- `src/main/CMakeLists.txt`: `DEMO_TRANSPORT=H3` builds this client instead of the MQTT task (`DEMO_HTTP3=1`).
- `src/partitions.csv`: factory app partition **1700K → 3M** (flash is 8 MB).

## Result (image tag `h3a`, `build.py h3a H3 0`)
| item | value |
|---|---|
| builds | **yes** (exit 0; only warning in app code: unused `quic_sensor_task`) |
| image size | **1,670,576 B** (sha256 `5158d61d…320724`) |
| app partition | 3 MB (3,145,728 B): **1,475,152 B free (47 %)** |
| would it fit the old 1700K partition? | yes, 96 % full (70 KB left) — too tight for further work, hence 3 MB |
| flash left outside partitions (8 MB chip) | ≈ 4.9 MB unallocated (nvs 24 KB + phy 4 KB + app 3 MB + bootloader/table ≈ 64 KB) |
| nghttp3 contribution | 87,215 B (83,607 B flash: 57.7 KB code + 25.9 KB rodata; 3,608 B RAM .data/.bss) |
| compared with MQTT-over-QUIC image fq2 (1,637,616 B) | +32,960 B (MQTT/coreMQTT code is dropped by the linker in the H3 image) |
| static RAM (DIRAM) | 145,319 B used of 452,112 B |

## What is still missing
1. **No HTTP/3 server on the laptop.** The current `quic_server.py` speaks MQTT over QUIC (ALPN `mqtt`). Needed: an
   HTTP/3 server with ALPN `h3` on UDP 4433 (e.g. aioquic's HTTP/3 server example, already-installed aioquic in `.quic-venv`).
2. **Never run on hardware.** Runtime heap use of nghttp3 (dynamic allocation for streams, QPACK, frames) and stack
   need of the task (28 KB, same as the MQTT task) are unknown; the code paths have not been exercised.
3. Certificate verification is off (`VERIFY_NONE`, same as the MQTT experiments).
4. No request body / POST, no response body storage (only counted), no 0-RTT or session resumption, no GOAWAY handling.
5. The libev compatibility layer of the MQTT client is not used here; if HTTP/3 has to coexist with the measurement
   harness (DIAG/heap logging, reconnect), the client has to be integrated with it.
6. No measurement harness (RTT logging, comparison with MQTT) yet.
