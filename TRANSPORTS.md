# Firmware transport selection

Select the CMake cache option in an ESP-IDF terminal at the project root:

```powershell
idf.py -DDEMO_TRANSPORT=QUIC reconfigure build
idf.py -DDEMO_TRANSPORT=TCP_TLS reconfigure build
```

The value persists in `build/CMakeCache.txt`. A fresh build defaults to
`TCP_TLS`. The normal output for either choice is `build/quic_demo.bin`.
Build-check copies of both images are under `build/transport_artifacts/`.
Flashing is a separate step; these commands do not flash.

QUIC uses `192.168.137.1:14567` with the existing ngtcp2 fixes. TCP_TLS uses
`192.168.137.1:14568`, wolfSSL's TLS-1.3-only client method, and the single cipher
`TLS_AES_128_GCM_SHA256` (wolfSSL spelling `TLS13-AES128-GCM-SHA256`, suite
`0x1301`). Both use ALPN `mqtt`. TCP_TLS rejects a successful handshake if its
actual version, suite or ALPN does not match these requirements.

After the handshake, both paths log actual negotiated version, IANA and wolfSSL
cipher names, suite ID, ALPN, and certificate verification mode. TCP_TLS also
sets and reads back TCP_NODELAY, logging the observed value (must be 1).
Certificate verification is `NONE`, matching the existing QUIC experiment;
this mode does not authenticate the laptop certificate.

The shared coreMQTT send callback retains the existing 512-byte complete-packet
assembly, including its 10 ms pre-send delay. Its raw operations select the QUIC
writer/reader or TCP_TLS. TCP_TLS uses a nonblocking socket, a 5-second combined
TCP-connect/TLS-handshake deadline, a 5-second complete-packet write deadline,
partial-write handling, and WANT_READ/WANT_WRITE retries with the same write
buffer. Receive calls use an internal stable buffer, return retryable no-data
on WANT_READ, and bound WANT_WRITE waits to 100 ms. Plaintext receive leftovers
are retained for subsequent coreMQTT calls. An inactive connection expires
after 60 seconds; cleanup bounds TLS shutdown to 250 ms before freeing TLS
objects and closing the socket. TLS operations run only on the MQTT task.

DHT11 GPIO4, five-second sensor interval, client ID `esp32_quic_client`, topic
`esp32/quic/test`, JSON construction, QoS 0, and the sequence-matched
`APP_RTT seq=N app_rtt_ms=X.XXX` measurement remain shared. The application
retains its 20 ms loop delay, transport-processing call every 25 iterations,
and MQTT processing every five iterations. TCP_TLS retains the QUIC process
call's 5 ms and 1 ms yields. The quiet measurement switch stays enabled.

Build validation does not establish the ESP32's runtime negotiation or RTT.
After the separate flash step, run `quic_server.py` for QUIC or
`tcp_tls_server.py` for TCP_TLS, then check the startup negotiation logs,
subscription acknowledgment, and repeated APP_RTT results.
