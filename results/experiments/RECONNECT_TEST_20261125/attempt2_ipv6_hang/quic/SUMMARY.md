# Controlled reconnect test — QUIC (fq3)

Cycles run: 0 (test NOT completed; first connection (CONNECT session=0) not seen within 150 s). Reconnected: 0/0; reconnect timeouts: 0; failed attempts before success: 0; reboots during test (rst lines after the start reset): 0; panics: 0.

First connection: ``

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| server restart (READY) -> handshake done | 0 |  |  |  |  |  |
| server restart (READY) -> MQTT CONNACK | 0 |  |  |  |  |  |
| board: handshake of the successful attempt | 0 |  |  |  |  |  |
| board: CONNECT -> CONNACK | 0 |  |  |  |  |  |
| server kill -> board detects failure | 0 |  |  |  |  |  |
| board downtime (failure -> connected) | 0 |  |  |  |  |  |

Attempts per reconnect: n/a. Failure detection reasons: none. Cycles whose first attempt started before the server was READY: 0.
Echo: 0 APP_RTT lines (seq -..-), 0 APP_RTT_LOST, 0 STALL lines.

Per cycle:

| cycle | ok | attempts | detect | restart→handshake | restart→CONNACK | board handshake | board CONNACK | fail reason | failed attempt stages |
|---|---|---|---|---|---|---|---|---|---|
