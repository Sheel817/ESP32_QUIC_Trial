# ESP32-C6 MQTT over QUIC vs TCP/TLS 1.3

Thesis experiment comparing application-level round-trip time (APP_RTT) for MQTT over QUIC and MQTT over TCP/TLS 1.3 on an ESP32-C6, under controlled network impairment.

The firmware started from [emqx/ESP32-QUIC](https://github.com/emqx/ESP32-QUIC) and was extended with the TCP/TLS transport, measurement logging and fixed build profiles. It uses [ngtcp2](https://github.com/ngtcp2/ngtcp2), wolfSSL and [coreMQTT](https://github.com/FreeRTOS/coreMQTT) on ESP-IDF v6.1.

## Experiment design

The rules are frozen in [EXPERIMENT_PLAN_PROPOSED_V1.md](results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md).

- **Design:** 2 transports × 3 conditions × 3 boot sessions = 18 runs, each recording for 2,220 s (37 min) from a controlled reset.
- **Conditions:** set with Clumsy 0.3 on the host.
  - `CONTROL`: capture running, all effects off.
  - `LAG100_OUT`: 100 ms lag, outbound only.
  - `DROP1_OUT`: 1% drop, outbound only.
- **Traffic:** a DHT11 reading published every 5 s at QoS 0, with the RTT matched by sequence number.
- **Protocol on both transports:** TLS 1.3, `TLS_AES_128_GCM_SHA256`, ALPN `mqtt`. Certificate verification is off, as in the original QUIC demo.
- **Sample:** the first 415 eligible RTTs from the initial boot, with uptime from 60 s to the end of the window. P95 uses the nearest-rank method.

## Progress

As of 11 November 2026, all 18 runs have been attempted: 15 are valid, 1 is FAILED_SETTINGS with a reassessment awaiting supervisor approval (HBPSN-01) and 2 failed during startup. The [run register](results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/run_register.csv) is the record of status and results.

| Run | Transport | Condition | Status |
|---|---|---|---|
| HBPSN-01 | QUIC | CONTROL | FAILED_SETTINGS (reassessment pending supervisor approval) |
| HBPSN-02 | TCP_TLS | LAG100_OUT | COMPLETE |
| HBPSN-03 | QUIC | DROP1_OUT | FAILED_STARTUP |
| HBPSN-04 | TCP_TLS | CONTROL | COMPLETE |
| HBPSN-05 | QUIC | LAG100_OUT | COMPLETE |
| HBPSN-06 | TCP_TLS | DROP1_OUT | COMPLETE |
| HBPSN-07 | TCP_TLS | DROP1_OUT | COMPLETE with retained flags |
| HBPSN-08 | QUIC | LAG100_OUT | FAILED_STARTUP |
| HBPSN-09 | TCP_TLS | CONTROL | COMPLETE with retained flags |
| HBPSN-10 | QUIC | DROP1_OUT | COMPLETE with retained flags |
| HBPSN-11 | TCP_TLS | LAG100_OUT | COMPLETE with retained flags |
| HBPSN-12 | QUIC | CONTROL | COMPLETE with retained flags |
| HBPSN-13 | QUIC | LAG100_OUT | COMPLETE with retained flags |
| HBPSN-14 | TCP_TLS | DROP1_OUT | COMPLETE with retained flags |
| HBPSN-15 | QUIC | CONTROL | COMPLETE with retained flags |
| HBPSN-16 | TCP_TLS | LAG100_OUT | COMPLETE with retained flags |
| HBPSN-17 | QUIC | DROP1_OUT | COMPLETE with retained flags |
| HBPSN-18 | TCP_TLS | CONTROL | COMPLETE with retained flags |

**Known issue:** HBPSN-03 and HBPSN-08 hit the same QUIC panic during startup, a load access fault in `tlsf_free`. The root cause has not been established.

## Repository layout

| Path | Contents |
|---|---|
| `main/`, `components/` | Firmware source and the ngtcp2 and coreMQTT submodules |
| `profiles/` | Preserved build profiles for the QUIC and TCP_TLS firmware, plus a test-only heap diagnostic |
| `quic_server.py`, `tcp_tls_server.py` | Host MQTT servers on UDP 14567 and TCP 14568 |
| `tools/run_recorder/` | Collector, serial monitor and run tooling |
| `results/experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/` | Plan, freeze manifest, run register and one folder per run |
| `outputs/` | Run register workbook |
| `TRANSPORTS.md` | Transport behaviour and build selection |

Each run folder holds the raw serial log, the selected RTTs, statistics, Clumsy screenshots, the manual review and a `SHA256SUMS.json` manifest.

## Building

Clone with long paths on (needed on Windows) and with submodules, then apply `ngtcp2.patch` inside `components/ngtcp2/ngtcp2`:

```powershell
git clone -c core.longpaths=true --recurse-submodules <repo-url>
```

Choose the transport in an ESP-IDF v6.1 terminal:

```powershell
idf.py -DDEMO_TRANSPORT=QUIC reconfigure build
idf.py -DDEMO_TRANSPORT=TCP_TLS reconfigure build
```

See [TRANSPORTS.md](TRANSPORTS.md) for details.

## Not in this repository

- `server-key.pem`, the host TLS private key. The servers need one to run.
- `profiles/*/build/`, including the frozen firmware binaries. Their hashes are in `freeze_manifest.json`.
- `backups/*.zip`, which are over GitHub's file size limit.
- `node_modules/`.

## Handling this repository

Keep this repository private. The `sdkconfig` files contain Wi-Fi credentials, and the run folders hold raw experiment records.

`.gitattributes` turns off line-ending conversion so that files keep matching their `SHA256SUMS.json` hashes. Please do not change it.
