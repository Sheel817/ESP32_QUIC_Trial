# Controlled reconnect test — QUIC (fq3v4, IPv4-only start-up)

Cycles run: 20 (test completed). Reconnected: 20/20; reconnect timeouts: 0; failed attempts before success: 0; reboots during test (rst lines after the start reset): 0; panics: 0.

First connection: `CONNECT session=0 initial=1 transport_ms=2725.1 connack_ms=84.0`

## Headline: (2) reconnect duration, board clock

Reconnect start = the board gives up the old connection (RECONNECT_START, same instant as CONNECTION_FAILED); the duration includes the 1 s backoff and any failed attempts while the server was still down.

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (2a) reconnect start -> handshake done | 20 | 3,808.9 | 3,655.1 | 3,848.5 | 3,838.4 | 3,801.3 |
| (2b) reconnect start -> MQTT CONNACK | 20 | 3,864.8 | 3,738.5 | 6,548.6 | 3,928.6 | 3,990.6 |
| successful attempt only: attempt start -> handshake done | 20 | 2,773.9 | 2,620.1 | 2,812.5 | 2,803.4 | 2,766.1 |
| successful attempt only: attempt start -> MQTT CONNACK | 20 | 2,829.3 | 2,703.5 | 5,513.6 | 2,893.6 | 2,955.4 |
| successful attempt only: CONNECT -> CONNACK | 20 | 51.0 | 26.3 | 2,744.5 | 90.2 | 189.3 |

## (1) Detection: server stop -> board notices (host clock)

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (1) server kill -> CONNECTION_FAILED | 20 | 19,977.3 | 15,109.8 | 20,176.3 | 20,154.0 | 18,820.3 |

## (3) Reference: server restart (READY) -> board connected (host clock, includes detection when it ends after the restart)

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (3a) server READY -> handshake done | 20 | 13,067.5 | 7,960.6 | 13,499.0 | 13,368.0 | 11,958.5 |
| (3b) server READY -> MQTT CONNACK | 20 | 13,129.3 | 8,027.2 | 13,536.9 | 13,408.2 | 12,147.8 |
| board downtime (failure -> subscribed) | 20 | 3,874.3 | 3,756.4 | 6,559.6 | 3,939.6 | 4,002.4 |

Attempts per reconnect: median 1.0, min 1, max 1. Failure detection reasons: {'stall': 20}. Cycles whose reconnect started before the server was READY: 0/20.
Echo: 246 APP_RTT lines (seq 1..306), 60 APP_RTT_LOST, 20 STALL lines.

Per cycle (ms):

| cycle | ok | attempts | (1) detect | (2a) start→handshake | (2b) start→CONNACK | (3b) READY→CONNACK | attempt handshake | CONNECT→CONNACK | start before READY | fail reason | failed attempt stages |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | 1 | 19,974.1 | 3,819.1 | 3,858.6 | 12,978.8 | 2,783.1 | 39.5 | no | stall |  |
| 2 | yes | 1 | 19,975.0 | 3,655.1 | 3,738.5 | 13,118.9 | 2,620.1 | 83.4 | no | stall |  |
| 3 | yes | 1 | 20,036.7 | 3,799.6 | 3,865.7 | 13,104.1 | 2,763.6 | 66.1 | no | stall |  |
| 4 | yes | 1 | 20,089.4 | 3,848.5 | 3,881.1 | 13,249.2 | 2,812.5 | 32.6 | no | stall |  |
| 5 | yes | 1 | 15,375.9 | 3,804.1 | 6,548.6 | 11,064.3 | 2,769.1 | 2,744.5 | no | stall |  |
| 6 | yes | 1 | 20,036.4 | 3,696.1 | 3,766.4 | 12,930.9 | 2,660.1 | 70.3 | no | stall |  |
| 7 | yes | 1 | 15,130.0 | 3,819.6 | 3,863.9 | 8,319.0 | 2,784.6 | 44.3 | no | stall |  |
| 8 | yes | 1 | 19,979.7 | 3,794.5 | 3,820.8 | 13,359.0 | 2,759.5 | 26.3 | no | stall |  |
| 9 | yes | 1 | 20,021.1 | 3,805.3 | 3,843.4 | 13,306.3 | 2,770.3 | 38.1 | no | stall |  |
| 10 | yes | 1 | 15,109.8 | 3,804.7 | 3,870.9 | 8,579.6 | 2,769.7 | 66.2 | no | stall |  |
| 11 | yes | 1 | 19,865.4 | 3,838.4 | 3,928.6 | 12,888.8 | 2,803.4 | 90.2 | no | stall |  |
| 12 | yes | 1 | 15,183.7 | 3,809.4 | 3,876.0 | 8,027.2 | 2,774.4 | 66.6 | no | stall |  |
| 13 | yes | 1 | 19,973.7 | 3,819.1 | 3,859.3 | 13,408.2 | 2,784.1 | 40.2 | no | stall |  |
| 14 | yes | 1 | 20,176.3 | 3,799.0 | 3,841.6 | 13,334.6 | 2,764.0 | 42.6 | no | stall |  |
| 15 | yes | 1 | 20,154.0 | 3,833.0 | 3,911.3 | 13,299.8 | 2,798.0 | 78.3 | no | stall |  |
| 16 | yes | 1 | 20,093.1 | 3,834.3 | 3,872.2 | 13,536.9 | 2,799.3 | 37.9 | no | stall |  |
| 17 | yes | 1 | 20,076.1 | 3,808.5 | 3,888.7 | 13,402.2 | 2,773.5 | 80.2 | no | stall |  |
| 18 | yes | 1 | 15,192.3 | 3,824.4 | 3,882.2 | 8,644.2 | 2,789.4 | 57.8 | no | stall |  |
| 19 | yes | 1 | 20,102.0 | 3,813.2 | 3,851.0 | 13,264.3 | 2,778.2 | 37.8 | no | stall |  |
| 20 | yes | 1 | 19,861.2 | 3,800.8 | 3,843.6 | 13,139.7 | 2,765.8 | 42.8 | no | stall |  |
