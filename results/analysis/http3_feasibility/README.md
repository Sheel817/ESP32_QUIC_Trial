# HTTP/3 feasibility: sensor page next to MQTT over QUIC

Read-only analysis. No firmware, build setting, run data or register was changed, and the board was not touched. Facts were read from the files named in the last column; `facts.json` has the full detail and exact paths.

| Item | Value | Measured or estimated | Source |
|---|---|---|---|
| Configured flash size | 8 MB | measured | `sdkconfig:1004` |
| App partition (factory, no OTA) | 1,740,800 B (1700K) at 0x10000 | measured | `partitions.csv; profiles/wifi_ps_none_20261103/build/partition_table/partition-table.bin` |
| Unpartitioned flash after the table | 6,582,272 B | measured (computed) | `partition-table.bin` |
| QUIC_PSN image / free in app partition | 1,637,280 B / 103,520 B (5.9%) | measured | `profiles/wifi_ps_none_20261103/build/quic_demo.bin` |
| TCP_TLS_PSN image / free in app partition | 1,498,864 B / 241,936 B (13.9%) | measured | `profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.bin` |
| Static RAM used, QUIC_PSN | 149,011 B of 452,112 B (IRAM text 99,720 B, .bss 32,816 B, .data 16,475 B) | measured | `profiles/wifi_ps_none_20261103/build/quic_demo.map` |
| Static RAM used, TCP_TLS_PSN | 149,375 B of 452,112 B (IRAM text 99,796 B, .bss 31,056 B, .data 18,523 B) | measured | `profiles/tcp_tls_wifi_ps_none_20261104/build/quic_demo.map` |
| Free heap before connecting (QUIC runs) | min 287,744 B, max 288,140 B, n=9 | measured | `runs/HBPSN-*/attempt_*/serial.raw.log` |
| Free heap before connecting (TCP_TLS runs) | min 287,368 B, max 287,396 B, n=9 | measured | `runs/HBPSN-*/attempt_*/serial.raw.log` |
| ngtcp2 | 1.13.0 (+ ngtcp2.patch) | measured | `components/ngtcp2/ngtcp2/CMakeLists.txt:31` |
| wolfSSL | 5.8.0 | measured | `managed_components/wolfssl__wolfssl/wolfssl/version.h:31; dependencies.lock:217` |
| coreMQTT | v2.3.1+ | measured | `components/coreMQTT/coreMQTT/source/include/core_mqtt.h:51` |
| nghttp3 / HTTP/3 library in repository | not present | measured | `managed_components/, dependencies.lock, main/, both map files` |
| HTTP/3 flash cost | about 85 to 215 KB | ESTIMATE | `see Estimates` |
| HTTP/3 extra RAM | about 20 to 40 KB steady, 40 to 60 KB handshake peak | ESTIMATE | `see Estimates` |
| Work for a minimal HTTP/3 page | 8 to 12 working days | ESTIMATE | `see Estimates` |

## Facts

- **Flash and partitions:** 8 MB flash. The custom table (`partitions.csv`) has `nvs` 0x6000, `phy_init` 0x1000 and one `factory` app of 1700K. It ends at 0x1B9000, leaving 6,582,272 B unused. There are no OTA slots and no `otadata`. Both frozen builds use the same table.
- **Images:** QUIC_PSN is 1,637,280 B, leaving 103,520 B (5.9%). TCP_TLS_PSN is 1,498,864 B, leaving 241,936 B (13.9%).
- **Libraries in the QUIC build (measured archive sizes):** wolfSSL 412,546 B, ngtcp2 171,628 B, coreMQTT 12,386 B, project code 21,199 B.
- **Heap:** free heap is logged once per run, after Wi-Fi is up and before the transport connects (`main/quic_demo_main.c:353`), not at MQTT connect. Heap during a connection and the minimum free heap are not logged.
- **nghttp3:** not in the repository. Only the ngtcp2 submodule's own examples and build scripts mention it, and this project does not build them. The ngtcp2 core is built with its wolfSSL crypto backend only.

## Estimates (not measured)

**Library:** HTTP/3 on ngtcp2 needs nghttp3 (HTTP/3 framing and QPACK) plus the server side of ngtcp2 and wolfSSL, which this project does not use today (the client code keeps one global client struct, `main/ngtcp2_sample.c:81`).

**Flash: ESTIMATE of about 85 to 215 KB.** nghttp3 60 to 150 KB, server-side QUIC and TLS 20 to 50 KB, application code 5 to 15 KB. nghttp3 source is not available locally, so nothing could be built. The nghttp3 range is anchored on the measured ngtcp2 archive (171,628 B) with an assumed size ratio and widened; the other parts are rough guesses. Treat the range, not a single number, as the result.

**Fit:** the QUIC image has 103,520 B free. Only the optimistic end of the range fits, with almost no margin, so plan on it not fitting.

**Partition change:** one larger factory partition, for example 2048K (0x200000), gives about 0.2 to 0.4 MB headroom over the estimated 1.72 to 1.86 MB image and fits in the 8 MB flash. Trade-offs:
- The current table has no OTA slots, so enlarging the single factory partition loses no OTA that exists today.
- Adding OTA later needs two app slots (for example 2048K each plus `otadata`, about 4.2 MB of 8 MB), which still fits but doubles the app space and adds rollback handling.
- A new table must be flashed with the app, moves offsets and changes every image hash, so it has to be a separate exploratory profile, never the frozen QUIC_PSN or TCP_TLS_PSN artifacts.

**RAM: ESTIMATE.** About 40 to 60 KB transient at the handshake (wolfSSL server with ECDSA signing), about 20 to 40 KB steady for one HTTP/3 connection with the QPACK dynamic table set to 0, and 2 to 8 KB static. Free heap before connecting is measured at about 287 to 288 KB, but the heap used by the existing MQTT/QUIC connection is unknown, so the margin is unconfirmed. It probably fits for one concurrent HTTP/3 connection; minimum free heap must be logged to confirm.

**Work: ESTIMATE of 8 to 12 working days** for a minimal page with sensor values.

| Task | Days |
|---|---|
| add nghttp3 as an ESP-IDF component and build it with ngtcp2 and wolfSSL | 1 to 2 |
| server-side ngtcp2 + wolfSSL (UDP listen socket, certificate and key on board, multiple-connection state; the client code uses one global client struct, main/ngtcp2_sample.c:81) | 3 to 4 |
| HTTP/3 request handler and the sensor page | 1 to 1 |
| new partition table, exploratory build profile, flash and verify | 0.5 to 1 |
| HTTP/3 test client (curl built with HTTP/3 or an aioquic client script) and browser quirks (self-signed certificate, QUIC discovery) | 1 to 2 |
| coexistence with the MQTT client, heap logging, stability runs (the QUIC tlsf_free panic from HBPSN-03/08 is unresolved) | 2 to 3 |

The main risk is stability: the QUIC `tlsf_free` panic from HBPSN-03 and HBPSN-08 is unresolved, and more QUIC code adds more heap activity.

## Not verified

- Whether an ESP-IDF component for nghttp3 exists (no registry access checked).
- All HTTP/3 flash, RAM and day figures (estimates).
- Heap during an MQTT connection and the minimum free heap (not logged).
- Whether the linker would drop unused ngtcp2 server code (not built).
- Browser behaviour with a self-signed HTTP/3 certificate (general knowledge, not tested here).
- The ngtcp2.patch contents were not re-checked against the built objects.
