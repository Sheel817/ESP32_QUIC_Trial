# Connection setup timing, HBPSN-01 to HBPSN-18

How long the ESP32-C6 takes after a reset to get a Wi-Fi IP, connect the transport and connect MQTT, for the first boot of every run (including the two failed startups).

## Files

| File | Contents |
|---|---|
| `analyze_connection_setup.py` | The script. Run `python -I analyze_connection_setup.py`. It only reads the run folders and writes the three CSVs next to itself. |
| `connection_setup_per_run.csv` | One row per run: event times and durations on both clocks, the attempt used, the serial log SHA-256, and a note. |
| `connection_setup_events.csv` | One row per event found, with its line number in `serial.raw.log`, the raw log line, the uptime and the host receipt time. Every value in the other files can be traced here. |
| `connection_setup_summary.csv` | Median, min, max and n per protocol, metric and clock, with the runs included. |
| `SHA256SUMS.json` | Hashes of the files in this folder. |

Input state: `run_register.csv` sha256 `1f2a35984a3ea81538c188a6f1f428dcd9690fd66fabfea12cd1870ac4533f3f`.

## Method

- **Attempt:** the attempt named by `raw_serial_path` in `run_register.csv`. HBPSN-04 and HBPSN-08 each also have an earlier attempt folder; those were not analyzed.
- **First boot only:** the lines from the first `ESP-ROM:` banner up to the next banner. HBPSN-03 and HBPSN-08 rebooted after a panic; their second boots are excluded.
- **Events:** each is the first matching log line of the first boot.
  - Wi-Fi associated: `wifi:connected with …`
  - Wi-Fi IP: `esp_netif_handlers: example_netif_sta ip: …`
  - Transport connected: QUIC `QUIC handshake completed callback triggered`; TCP_TLS `TCP_TLS: Connected to …` (after TLS 1.3 completes)
  - Application-level connection line: `QUIC connection established` or `TCP_TLS connection established`
  - MQTT connected: `quic_demo_main: MQTT connected over …`
- **Clock A (primary):** the ESP log uptime, the number in `I (ms)`. It starts at the board's boot and is treated here as time since the reset release. It ticks in 10 ms steps, so differences have about 10 ms resolution. Durations inside the board (for example Wi-Fi IP to MQTT) use clock A.
- **Clock B (cross-check):** the host receipt time of the log line (from `serial_receipts.jsonl`) minus `reset_release_utc` from `reset_event.json`. It includes ROM boot time, serial transfer and host latency, so it runs about 15 to 25 ms above clock A. Two lines were received late by the host (HBPSN-04 Wi-Fi IP, +111 ms; HBPSN-08 Wi-Fi IP, +75 ms), which is why clock A is used for durations.
- Run folders were not modified.
- The Wi-Fi network name and the access point MAC address in the raw log lines of `connection_setup_events.csv` are replaced by `<SSID>` and `<BSSID>` (the script masks them automatically); the original `serial.raw.log` files are unchanged.

## Results (clock A, ms)

| Metric | QUIC median (min to max), n | TCP_TLS median (min to max), n |
|---|---|---|
| Wi-Fi IP | 4443 (4413 to 4513), 9 | 4417 (4397 to 4487), 9 |
| Transport connected | 7243 (7203 to 7443), 9 | 6097 (6087 to 6367), 9 |
| MQTT connected | 8413 (8303 to 8693), 7 | 7117 (7107 to 7507), 9 |
| Wi-Fi IP to MQTT (setup time) | 3980 (3850 to 4270), 7 | 2710 (2630 to 3090), 9 |
| Wi-Fi IP to transport | 2810 (2710 to 2990), 9 | 1690 (1610 to 1950), 9 |
| Transport to MQTT | 1170 (1100 to 1350), 7 | 1020 (1020 to 1150), 9 |

## TLS stack in the two builds

The TLS library and the negotiated cipher suite are the same in both builds. The paths around them differ. This is recorded as a possible factor in the setup-time difference only; no experiment here separates it from the transport itself, and no cause is claimed.

| | QUIC build | TCP_TLS build |
|---|---|---|
| TLS library on the board | wolfSSL 5.8.0 (managed component `wolfssl/wolfssl`), used through ngtcp2's wolfSSL crypto backend (`ngtcp2_crypto_wolfssl`) | wolfSSL 5.8.0, used directly (`wolfTLSv1_3_client_method`) over a TCP socket |
| mbedTLS | Enabled in the ESP-IDF configuration of both builds (for example `CONFIG_ESP_TLS_USING_MBEDTLS`, `CONFIG_ESP_WIFI_MBEDTLS_CRYPTO`); the project's TLS session code calls wolfSSL only | same |
| Negotiated, from the first boot log of all 18 runs | TLS 1.3, `TLS_AES_128_GCM_SHA256` (0x1301), ALPN `mqtt`, certificate verification off | identical |
| Cipher list offered by the board | none set in the project code, so the client's offer was not captured in the logs | one suite only: `TLS13-AES128-GCM-SHA256` |
| Host server TLS stack | aioquic (Python TLS 1.3), `cipher_suites` limited to AES_128_GCM_SHA256 | Python `ssl` (OpenSSL), TLS 1.3 only, ALPN `mqtt`, no cipher restriction |
| Server certificate | `server-cert.pem`, ECDSA P-256, SHA-256 signature, created 2026-10-21, sha256 `dad4aa42a253793e77b161ac0846e6a1b39447b4d207572739b24b41dbfce462`; both servers load it from the project folder | same file |

- The two profile `sdkconfig` files are byte-identical, and the profile comparison (`compile_settings_comparison.json`) finds the compile settings of 1139 shared translation units identical apart from the `DEMO_TRANSPORT` flag.
- What differs is the code path on the board (QUIC through ngtcp2 and its wolfSSL wrapper, TCP_TLS through wolfSSL directly), the host-side TLS implementation (aioquic or OpenSSL), the cipher list the board offers, and the transport itself (QUIC over UDP or TCP). Any of these could contribute to the setup-time difference. The data here cannot tell which, if any, does.
- Not examined: wolfSSL's key-exchange group choice and its default cipher offer in the QUIC build, because neither is logged.

## Caveats

- **Failed startups:** HBPSN-03 and HBPSN-08 (QUIC) reached the handshake but not MQTT; the first boot ended with the known `Load access fault` panic. They are in the n = 9 rows for Wi-Fi IP and transport connected, and not in the MQTT rows (n = 7).
- **One boot per run:** each run contributes a single first boot, so the spread is between runs on different days and conditions, not repeated measurements.
- **Impairment during setup:** Clumsy was already active when the board booted, so the setup values include the run's condition. The three TCP_TLS LAG100_OUT runs (HBPSN-02, 11, 16) are about 190 to 280 ms later at transport connected than the CONTROL and DROP1_OUT runs. Protocol and condition are not separated here.
- **Descriptive only:** no cause is asserted for the difference between the protocols, and no significance is claimed.
- **Event choice:** for QUIC the application line `QUIC connection established` appears 30 to 120 ms after the handshake callback used as "transport connected". For TCP_TLS the two coincide within 10 ms.
