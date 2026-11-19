# 12 h run summary: QUIC 12 h (fixed image fq2)

Capture duration from reset release to capture close: 43200 s (12.00 h).
Boot markers seen (initial boot included): 1; sessions: 1; panic/fault markers: 0; disconnect markers: 16840.

## Session 0 (start 2026-11-18T12:20:10.948013+00:00)

- messages sent (highest seq seen): 8621; echoed with APP_RTT: 8282; missing seq: 339
- missing sequence numbers: 8283-8621
- RTT ms overall: n=8282 median=65.53 mean=66.76 P95=105.61 min=24.45 max=465.53

Server CSV rows: 8621; unique seq: 8621; highest seq: 8621.

## RTT per hour (ms, elapsed from reset release)

| hour | n | median | mean | P95 | min | max |
|---|---|---|---|---|---|---|
| 0-1 | 716 | 65.57 | 66.44 | 105.60 | 24.53 | 268.75 |
| 1-2 | 719 | 65.53 | 66.63 | 105.61 | 24.67 | 365.46 |
| 2-3 | 718 | 65.53 | 66.42 | 105.55 | 24.69 | 186.63 |
| 3-4 | 719 | 65.52 | 66.82 | 105.55 | 24.69 | 248.72 |
| 4-5 | 719 | 65.53 | 67.05 | 105.63 | 24.71 | 465.53 |
| 5-6 | 718 | 65.53 | 66.29 | 105.59 | 25.18 | 214.60 |
| 6-7 | 719 | 65.53 | 66.63 | 105.62 | 24.80 | 145.83 |
| 7-8 | 718 | 65.55 | 67.22 | 105.63 | 24.71 | 360.83 |
| 8-9 | 719 | 65.53 | 66.78 | 105.60 | 24.45 | 205.48 |
| 9-10 | 718 | 65.53 | 66.97 | 105.76 | 24.68 | 305.83 |
| 10-11 | 719 | 65.53 | 67.54 | 105.61 | 24.45 | 445.38 |
| 11-12 | 380 | 65.52 | 65.85 | 105.54 | 24.73 | 106.06 |

Overall (all sessions): sent 8621, echoed 8282.

## Connection setup at start (board uptime ms, first session)

`{"connecting": 4585, "established": 7365, "mqtt_connected": 8465}`
- transport setup (connecting -> connection established): 2780 ms (board log time stamps, 1 ms resolution)
- connecting -> MQTT connected (includes the fixed 1,000 ms application delay of the formal firmware): 3880 ms

## Free heap trend (HEAPLOG every 60 s)

- samples: 719; first free 175712 B, last free 174228 B, change -1484 B (-124 B/h)
- free min/max over run: 174228 / 175732 B; minimum-free-heap first/last/overall: 144048 / 144048 / 144048 B

## Crash / disconnect markers (first 20)

- 2026-11-18T23:51:56.963260+00:00 W (41506295) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:56.963408+00:00 W (41506395) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.171030+00:00 W (41506495) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.171172+00:00 W (41506595) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.377341+00:00 W (41506695) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.377516+00:00 W (41506795) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.588248+00:00 W (41506895) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.588378+00:00 W (41506995) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.796067+00:00 W (41507095) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:57.796208+00:00 W (41507195) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.002904+00:00 W (41507295) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.002995+00:00 W (41507395) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.209975+00:00 W (41507495) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.210066+00:00 W (41507595) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.417387+00:00 W (41507695) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.417529+00:00 W (41507795) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.624595+00:00 W (41507895) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.624730+00:00 W (41507995) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.832648+00:00 W (41508095) quic_demo_main: MQTT process returned: 11
- 2026-11-18T23:51:58.832743+00:00 W (41508195) quic_demo_main: MQTT process returned: 11
