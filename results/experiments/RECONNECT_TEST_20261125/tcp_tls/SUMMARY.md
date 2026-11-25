# Controlled reconnect test — TCP+TLS (ft3v4, IPv4-only start-up)

Cycles run: 20 (test completed). Reconnected: 20/20; reconnect timeouts: 0; failed attempts before success: 20; reboots during test (rst lines after the start reset): 0; panics: 0.

First connection: `CONNECT session=0 initial=1 transport_ms=1549.9 connack_ms=18.7`

## Headline: (2) reconnect duration, board clock

Reconnect start = the board gives up the old connection (RECONNECT_START, same instant as CONNECTION_FAILED); the duration includes the 1 s backoff and any failed attempts while the server was still down.

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (2a) reconnect start -> handshake done | 20 | 12,316.9 | 12,296.0 | 12,554.7 | 12,550.7 | 12,371.4 |
| (2b) reconnect start -> MQTT CONNACK | 20 | 12,330.5 | 12,305.6 | 12,762.3 | 12,566.8 | 12,395.1 |
| successful attempt only: attempt start -> handshake done | 20 | 4,280.6 | 4,278.0 | 4,535.7 | 4,531.7 | 4,345.8 |
| successful attempt only: attempt start -> MQTT CONNACK | 20 | 4,297.8 | 4,287.5 | 4,743.3 | 4,547.8 | 4,369.5 |
| successful attempt only: CONNECT -> CONNACK | 20 | 14.8 | 9.0 | 215.4 | 19.0 | 23.7 |

## (1) Detection: server stop -> board notices (host clock)

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (1) server kill -> CONNECTION_FAILED | 20 | 213.9 | 124.9 | 349.6 | 347.4 | 221.0 |

## (3) Reference: server restart (READY) -> board connected (host clock, includes detection when it ends after the restart)

| metric (ms) | n | median | min | max | P95 | mean |
|---|---|---|---|---|---|---|
| (3a) server READY -> handshake done | 20 | 2,025.5 | 1,791.1 | 2,387.8 | 2,294.5 | 2,037.1 |
| (3b) server READY -> MQTT CONNACK | 20 | 2,039.8 | 1,806.0 | 2,509.9 | 2,399.1 | 2,060.8 |
| board downtime (failure -> subscribed) | 20 | 12,345.2 | 12,320.6 | 12,780.7 | 12,581.0 | 12,410.1 |

Attempts per reconnect: median 2.0, min 2, max 2. Failure detection reasons: {'mqtt_process_error': 16, 'publish_failed': 4}. Cycles whose reconnect started before the server was READY: 20/20.
Echo: 247 APP_RTT lines (seq 1..252), 5 APP_RTT_LOST, 0 STALL lines.

Per cycle (ms):

| cycle | ok | attempts | (1) detect | (2a) start→handshake | (2b) start→CONNACK | (3b) READY→CONNACK | attempt handshake | CONNECT→CONNACK | start before READY | fail reason | failed attempt stages |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | 2 | 347.4 | 12,550.7 | 12,566.8 | 2,172.4 | 4,531.7 | 16.1 | yes | mqtt_process_error | tcp_tls_connect |
| 2 | yes | 2 | 301.2 | 12,297.9 | 12,316.9 | 2,045.2 | 4,278.9 | 19.0 | yes | mqtt_process_error | tcp_tls_connect |
| 3 | yes | 2 | 237.5 | 12,546.3 | 12,557.6 | 2,399.1 | 4,527.3 | 11.3 | yes | publish_failed | tcp_tls_connect |
| 4 | yes | 2 | 270.5 | 12,299.0 | 12,316.7 | 1,930.3 | 4,280.0 | 17.7 | yes | mqtt_process_error | tcp_tls_connect |
| 5 | yes | 2 | 124.9 | 12,554.7 | 12,566.7 | 2,101.1 | 4,535.7 | 12.0 | yes | publish_failed | tcp_tls_connect |
| 6 | yes | 2 | 235.9 | 12,301.3 | 12,316.8 | 1,986.2 | 4,282.3 | 15.5 | yes | mqtt_process_error | tcp_tls_connect |
| 7 | yes | 2 | 140.1 | 12,547.1 | 12,557.1 | 2,144.6 | 4,528.1 | 10.0 | yes | publish_failed | tcp_tls_connect |
| 8 | yes | 2 | 253.3 | 12,301.9 | 12,316.5 | 1,945.8 | 4,282.9 | 14.6 | yes | mqtt_process_error | tcp_tls_connect |
| 9 | yes | 2 | 349.6 | 12,298.1 | 12,316.9 | 2,012.6 | 4,279.1 | 18.8 | yes | mqtt_process_error | tcp_tls_connect |
| 10 | yes | 2 | 172.1 | 12,546.9 | 12,762.3 | 2,509.9 | 4,527.9 | 215.4 | yes | mqtt_process_error | tcp_tls_connect |
| 11 | yes | 2 | 187.4 | 12,296.4 | 12,305.6 | 1,865.7 | 4,278.4 | 9.2 | yes | publish_failed | tcp_tls_connect |
| 12 | yes | 2 | 171.8 | 12,296.0 | 12,305.7 | 2,100.4 | 4,278.0 | 9.7 | yes | mqtt_process_error | tcp_tls_connect |
| 13 | yes | 2 | 204.4 | 12,297.1 | 12,306.7 | 2,034.3 | 4,278.1 | 9.6 | yes | mqtt_process_error | tcp_tls_connect |
| 14 | yes | 2 | 237.7 | 12,356.0 | 12,365.6 | 2,067.7 | 4,318.0 | 9.6 | yes | mqtt_process_error | tcp_tls_connect |
| 15 | yes | 2 | 163.8 | 12,317.1 | 12,335.4 | 2,001.1 | 4,279.1 | 18.3 | yes | mqtt_process_error | tcp_tls_connect |
| 16 | yes | 2 | 187.0 | 12,319.1 | 12,335.6 | 2,073.2 | 4,281.1 | 16.5 | yes | mqtt_process_error | tcp_tls_connect |
| 17 | yes | 2 | 235.8 | 12,316.5 | 12,325.5 | 2,033.6 | 4,278.5 | 9.0 | yes | mqtt_process_error | tcp_tls_connect |
| 18 | yes | 2 | 202.5 | 12,316.6 | 12,325.6 | 2,122.6 | 4,278.6 | 9.0 | yes | mqtt_process_error | tcp_tls_connect |
| 19 | yes | 2 | 223.3 | 12,318.2 | 12,335.7 | 1,864.1 | 4,280.2 | 17.5 | yes | mqtt_process_error | tcp_tls_connect |
| 20 | yes | 2 | 173.8 | 12,350.9 | 12,365.8 | 1,806.0 | 4,312.9 | 14.9 | yes | mqtt_process_error | tcp_tls_connect |
