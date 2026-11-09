# University board QUIC before/on/after pilot

Descriptive pilot only: 10 observations per condition, same running board and serial session. Conditions are operator-reported. Every recorded value is retained; no trimming or outlier removal. Earlier files are unchanged.

Source log: [UNIVERSITY_BOARD serial log](../../logs/UNIVERSITY_BOARD_20261103T170943_serial.log). Board base MAC: `98:a3:16:7e:55:50`.

| Phase | Sequences | n | Mean RTT (ms) |
|---|---|---:|---:|
| Before | 243-252 | 10 | 66.5212 |
| Lag enabled | 404-413 | 10 | 597.6777 |
| After | 474-483 | 10 | 66.9393 |

Lag minus before: +531.1565 ms. After minus before: +0.4181 ms. After minus Lag: -530.7384 ms.

Before: capture-only, effects disabled. On: Clumsy 0.3 capture running, main Lag checked, 100 ms, Outbound checked, Inbound unchecked, other effects off. After: capture running, main Lag unchecked, all effects disabled. Settings were not changed or independently inspected during this analysis. The return toward baseline supports an association, not attribution of every millisecond to one mechanism.

## Before

Actual input: [UNIVERSITY_BOARD_QUIC_capture_only_20261103T151403438686Z.csv](./UNIVERSITY_BOARD_QUIC_capture_only_20261103T151403438686Z.csv). SHA-256: `267ff7ae1e72dcc09c7f4c884306b4e29529c1e42bb436bce820f6b1b73f303e`.

| Sequence | ESP timestamp (ms) | APP_RTT (ms) |
|---:|---:|---:|
| 243 | 1225754 | 45.258 |
| 244 | 1230784 | 65.266 |
| 245 | 1235814 | 85.411 |
| 246 | 1240844 | 105.141 |
| 247 | 1245774 | 29.644 |
| 248 | 1250804 | 45.257 |
| 249 | 1255834 | 65.501 |
| 250 | 1260864 | 84.554 |
| 251 | 1265894 | 105.060 |
| 252 | 1270824 | 34.120 |

## Lag enabled

Actual input: [UNIVERSITY_BOARD_QUIC_corrected_lag100_outbound_20261103T152730561852Z.csv](./UNIVERSITY_BOARD_QUIC_corrected_lag100_outbound_20261103T152730561852Z.csv). SHA-256: `97b08e2844895861404b41879ef25f30b2ca0db777ae2ed60bf919b56d6970fb`.

| Sequence | ESP timestamp (ms) | APP_RTT (ms) |
|---:|---:|---:|
| 404 | 2032984 | 665.798 |
| 405 | 2037914 | 591.006 |
| 406 | 2042944 | 606.512 |
| 407 | 2047674 | 325.457 |
| 408 | 2053004 | 648.500 |
| 409 | 2057934 | 564.562 |
| 410 | 2063064 | 690.050 |
| 411 | 2068094 | 709.135 |
| 412 | 2073024 | 625.815 |
| 413 | 2077954 | 549.942 |

## After

Actual input: [UNIVERSITY_BOARD_QUIC_return_to_control_20261103T153320788300Z.csv](./UNIVERSITY_BOARD_QUIC_return_to_control_20261103T153320788300Z.csv). SHA-256: `f31d313d51fdbbde1f56dbf45e45601d8b8943ddedbb1f38c39ee46e32d569f4`.

| Sequence | ESP timestamp (ms) | APP_RTT (ms) |
|---:|---:|---:|
| 474 | 2383084 | 64.904 |
| 475 | 2388114 | 84.903 |
| 476 | 2393144 | 104.207 |
| 477 | 2398074 | 28.363 |
| 478 | 2403104 | 48.683 |
| 479 | 2408134 | 68.819 |
| 480 | 2413164 | 89.312 |
| 481 | 2418194 | 109.326 |
| 482 | 2423124 | 25.441 |
| 483 | 2428154 | 45.435 |

## Separate unsuccessful attempt

[Earlier lag-labelled CSV](./UNIVERSITY_BOARD_QUIC_lag100_outbound_20261103T152014259159Z.csv) remains separate and unchanged: sequences 317-326, recomputed mean 65.8950 ms. It is excluded from before/on/after. The earlier attempt did not validate delay: a subsequent screenshot showed the main Lag checkbox unchecked (reported in the session).

## Confirmed firmware receive path

The inspected main source/configuration hashes match all 20 entries in the preserved October 25 manifest; Git HEAD was not used as the baseline.

1. UDP readiness is watched by select with a 50 ms timeout. Readiness can wake select immediately; this is not a mandatory 50 ms delay. IO notifications use a zero-wait event post: [esp_ev_compat.c:58](../../main/esp_ev_compat.c#L58), [esp_ev_compat.c:84](../../main/esp_ev_compat.c#L84). The event queue has 32 entries and runs at priority 5: [esp_ev_compat.c:170](../../main/esp_ev_compat.c#L170). Failed posts are not checked, and level-triggered readiness is retried.
2. Event dispatch invokes read_cb, which takes the QUIC mutex with portMAX_DELAY, runs client_read, and releases it: [esp_ev_compat.c:128](../../main/esp_ev_compat.c#L128), [ngtcp2_sample.c:672](../../main/ngtcp2_sample.c#L672), [ngtcp2_sample.c:685](../../main/ngtcp2_sample.c#L685). This callback does not call client_write.
3. client_read drains at most four UDP datagrams per call with MSG_DONTWAIT and feeds ngtcp2_conn_read_pkt: [ngtcp2_sample.c:448](../../main/ngtcp2_sample.c#L448). ngtcp2 dispatches stream data to recv_stream_data, which appends to a 4096-byte application buffer: [ngtcp2_sample.c:99](../../main/ngtcp2_sample.c#L99), [ngtcp2_sample.c:873](../../main/ngtcp2_sample.c#L873). This is a shared byte buffer, not a per-message FreeRTOS receive queue.
4. MQTT task calls MQTT_ProcessLoop every five iterations. Its transport recv calls quic_client_read_safe, with a 100 ms mutex acquisition limit, then copies available application bytes. No data or lock timeout becomes a zero-byte read; the direct socket-read fallback is commented out: [mqtt_quic_transport.c:260](../../main/mqtt_quic_transport.c#L260), [ngtcp2_sample.c:1119](../../main/ngtcp2_sample.c#L1119), [ngtcp2_sample.c:832](../../main/ngtcp2_sample.c#L832).
5. MQTT_ProcessLoop performs one receiveSingleIteration, retains incomplete bytes, and handles a complete PUBLISH before dispatching the synchronous application callback: [core_mqtt.c:3468](../../components/coreMQTT/coreMQTT/source/core_mqtt.c#L3468), [core_mqtt.c:1740](../../components/coreMQTT/coreMQTT/source/core_mqtt.c#L1740), [core_mqtt.c:1825](../../components/coreMQTT/coreMQTT/source/core_mqtt.c#L1825), [core_mqtt.c:1556](../../components/coreMQTT/coreMQTT/source/core_mqtt.c#L1556). Additional buffered packets can wait until another application poll.
6. The application takes receive_time_us in the PUBLISH callback before JSON parsing/logging; send_time_us is immediately before MQTT_Publish: [quic_demo_main.c:228](../../main/quic_demo_main.c#L228), [quic_demo_main.c:525](../../main/quic_demo_main.c#L525). Thus APP_RTT includes send buffering, transport/network delays and receive scheduling, but excludes the preceding DHT read and payload construction. It is not pure wire RTT.

## Confirmed scheduling, waits and queues

- Application delay is 20 ms each iteration; MQTT polling is every five iterations (nominally 100 ms); QUIC process is every 25 iterations (nominally 500 ms), before the MQTT poll on that iteration: [quic_demo_main.c:474](../../main/quic_demo_main.c#L474). These are iteration-based cadences, stretched by work and blocking, not hard periodic deadlines.
- quic_client_process requests 5 ms delay, up to 50 ms mutex wait, reads, requests 1 ms delay while holding the mutex, then writes: [ngtcp2_sample.c:948](../../main/ngtcp2_sample.c#L948). CONFIG_FREERTOS_HZ=100 gives 10 ms ticks: [sdkconfig:2669](../../sdkconfig#L2669). With the installed default integer pdMS_TO_TICKS conversion, 5 ms and 1 ms become zero ticks (yield), not guaranteed sleeps of those durations.
- Complete MQTT packet send deliberately delays 10 ms, then waits up to 1000 ms for the QUIC mutex: [mqtt_quic_transport.c:135](../../main/mqtt_quic_transport.c#L135), [ngtcp2_sample.c:1072](../../main/ngtcp2_sample.c#L1072). Both lie inside APP_RTT.
- QUIC transmit chunks are retained for acknowledgments, limited to 16 KiB, and written immediately if possible. Pacing/congestion/stream credit can leave bytes queued: [ngtcp2_sample.c:169](../../main/ngtcp2_sample.c#L169), [ngtcp2_sample.c:808](../../main/ngtcp2_sample.c#L808), [ngtcp2_sample.c:563](../../main/ngtcp2_sample.c#L563).
- Writer consults ngtcp2 expiry, rearms a timer with minimum 1 ms requested interval, and timer callback handles expiry plus pending writes: [ngtcp2_sample.c:609](../../main/ngtcp2_sample.c#L609), [ngtcp2_sample.c:699](../../main/ngtcp2_sample.c#L699). Timer event posting also uses zero wait and its return is unchecked: [esp_ev_compat.c:112](../../main/esp_ev_compat.c#L112).
- Configured transport timeoutMs=5000/nonBlocking=false is stored by QUIC init but not enforced as a receive wait in this adapter: [quic_demo_main.c:374](../../main/quic_demo_main.c#L374), [mqtt_quic_transport.c:350](../../main/mqtt_quic_transport.c#L350). MQTT_ProcessLoop uses the single-iteration path; generic MQTT receive polling timeout defaults do not establish a mandatory wait in that path.

## Hypotheses about the increase

The nominal 500 ms transport cadence is near the observed +531.1565 ms, but proximity alone proves no causal link. Async read_cb processes incoming ACKs/data without immediately flushing/rearming writer output. ACK generation, new send credit, queued bytes, retransmission or expiry may therefore interact with the next timer/process opportunity. A delayed host echo can also move arrival across a roughly 100 ms MQTT polling boundary. Queue backlog, mutex contention and repeated partial packet handling could extend delay further. None is measured by these pilot CSVs; timeouts are upper limits, not evidence that the task waited that long. The 50 ms select timeout is interruptible on readiness and should not be added as a fixed cost.

Host outbound Lag can affect echo packets and QUIC ACK/control traffic, including retransmission and congestion dynamics. Exactly +100 ms at APP_RTT is not guaranteed. No packet timestamps, Clumsy per-packet evidence or ESP internal stage timestamps were captured, so the +531 ms cannot be apportioned among host delay, QUIC transport behavior and firmware scheduling.

## Errors and next minimal diagnostic

The three recorded capture reports observed no connection errors or sequence gaps. These CSVs contain selected matched echoes, not all send attempts; they alone cannot prove absence of unlogged packet loss, retransmissions or late echoes.

Next minimal diagnostic: with Lag left off and capture running, passively capture UDP 14567 packets on the laptop (no firmware change), synchronized with a fresh serial-log boundary and the server echo log. Record capture interface, board IP/MAC and capture timestamps. Compare packet arrival/departure timing with APP_RTT patterns; QUIC encryption and different host/ESP clocks limit sequence attribution, so do not subtract host UTC from ESP uptime. If that leaves receive scheduling ambiguous, propose a separately authorized instrumented firmware run with timestamps at publish entry, UDP recvmsg, recv_stream_data and MQTT callback plus mutex wait durations; do not modify firmware in this pilot.

This analysis did not access COM7, reset, build, flash, change firmware, or change Clumsy/server settings. Lag-off/capture-running state remains operator-reported.
