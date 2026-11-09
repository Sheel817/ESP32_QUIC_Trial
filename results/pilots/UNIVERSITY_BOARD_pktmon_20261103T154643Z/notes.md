# Passive university board QUIC packet timing diagnostic

Condition: Clumsy capture running, Lag OFF and all effects disabled, operator-reported. No Clumsy UI or settings were changed/independently verified. Existing server and serial monitor were retained.

## Capture and clocks

Pktmon initially reported not running and no filters. Elevated PowerShell was required. Only this temporary session was stopped; the filter set was restored to its original empty state. Local help, component inventory and commands are saved alongside this report.

ETL host UTC start: 2026-11-03T15:47:34.345513900Z. ETL stop: 2026-11-03T15:48:41.055568200Z. Full trace duration: 66.7100543 seconds. The script waited 60 seconds, but metadata serialization added overhead before that wait. The original is preserved without trimming. The explicit analysis interval is [2026-11-03T15:47:34.345513900Z, 2026-11-03T15:48:34.345513900Z), exactly 60 seconds. The filtered pcapng uses microsecond timestamp resolution; start/end comparisons are at that resolution.

Start command invoked UTC: 2026-11-03T15:47:34.3216385Z; completed: 2026-11-03T15:47:34.4586515Z. Stop invoked: 2026-11-03T15:48:40.9197764Z; completed: 2026-11-03T15:48:41.7066132Z.

Text export clock is host local time UTC+02:00; pcapng is host epoch time. ESP timestamps are device uptime. No subtraction of ESP uptime from host UTC was performed.

## Interfaces, components and commands

Capture selected all components, full packet length. Hotspot interface: Microsoft Wi-Fi Direct Virtual Adapter #2, Local Area Connection* 2, ifIndex 4, host IP 192.168.137.1, MAC B6-8C-9D-8C-8A-BB, Pktmon component 1. University board: 192.168.137.11, MAC 98:A3:16:7E:55:50. Observed UDP endpoints: board port 60133 and host port 14567.

Observed component IDs: 1, 13, 16, 17, 18, 19, 35, 36, 44, 45, 48. Full names/drivers/topology are in [components_before.txt](./components_before.txt) and [components_before.json](./components_before.json). Component 48 is hotspot TCPIP IPv4; it supplies one representative per observed candidate datagram. The pcapng export declares one Ethernet linktype interface even though Pktmon records Wi-Fi and Ethernet component types: do not treat every exported frame as a clean independent Ethernet wire packet.

```powershell
pktmon status
pktmon filter list
pktmon list --json
pktmon list --all --include-hidden
pktmon filter add UNIVERSITY_QUIC_154643 -t UDP -i 192.168.137.11 -p 14567
pktmon start --capture --comp all --pkt-size 0 --file-name university_quic.etl --file-size 64 --log-mode circular
# wait 60 seconds, with metadata overhead documented above
pktmon stop
pktmon etl2txt university_quic.etl --out university_quic.txt --timestamp --verbose
pktmon etl2pcap university_quic.etl --out university_quic.pcapng
pktmon etl2txt university_quic.etl --stats
pktmon filter remove # initial set was empty; only our unchanged filter existed
```

Exact absolute-path invocation and output are in [commands_and_output.txt](./commands_and_output.txt); local option help is saved in local_help.txt.

## Fresh log boundaries

| Source | Start byte | End byte |
|---|---:|---:|
| C:\Users\newsh\Desktop\ESP32_QUIC_Trial\logs\UNIVERSITY_BOARD_20261103T170943_serial.log | 33680 | 34645 |
| C:\Users\newsh\Desktop\ESP32_QUIC_Trial\logs\quic_server_start_20261103T163259.stdout.log | 112231 | 114467 |
| C:\Users\newsh\Desktop\ESP32_QUIC_Trial\logs\sensor_20261103T143300_220342Z_c7ett8c2.csv | 60502 | 61711 |

Boundary UTC measurement times and tails are in capture_start.json/capture_end.json. These per-file boundaries are not atomic with Pktmon start/stop. Exact byte slices are preserved as serial_window.log, server_window.log and sensor_window.csv. Sensor slice has no header because it is an original appended-byte extract. The joined CSV uses server receive UTC to choose the 60-second interval; serial lines themselves have no host receipt timestamps.

## Packet observations and duplicate handling

Full capture: 182 packet observations across components; 86 decode as IP/UDP in text. These reduce to 13 distinct candidate IPv4 datagrams at component 48 edge 1: 10 board-to-host (Rx), 3 host-to-board (Tx). First 60 seconds: 12 representative candidates, 10 Rx and 2 Tx; 168 component observations in the 60-second pcapng.

Grouping uses source/destination IP and ports, IPv4 ID, UDP length and near-simultaneous observation across components, cross-checked against component 48 edge 1. It is an observation-reduction method, not proof of complete unique wire-packet counts. PktGroupId changes across components here and was not treated as a retransmission identifier. Decoded same-identity component observations span roughly 0.0076-0.0812 ms. No QUIC retransmission count is inferred.

| Host UTC | Direction | UDP payload bytes | IPv4 ID |
|---|---|---:|---:|
| 2026-11-03T15:47:37.336181+00:00 | board to host | 33 | 1343 |
| 2026-11-03T15:47:42.286193+00:00 | board to host | 159 | 1344 |
| 2026-11-03T15:47:42.356248+00:00 | board to host | 33 | 1345 |
| 2026-11-03T15:47:47.293897+00:00 | board to host | 159 | 1346 |
| 2026-11-03T15:47:47.298106+00:00 | host to board | 167 | 8429 |
| 2026-11-03T15:48:02.386517+00:00 | board to host | 33 | 1353 |
| 2026-11-03T15:48:07.334433+00:00 | board to host | 159 | 1354 |
| 2026-11-03T15:48:12.347995+00:00 | host to board | 167 | 8435 |
| 2026-11-03T15:48:12.407578+00:00 | board to host | 33 | 1357 |
| 2026-11-03T15:48:22.363993+00:00 | board to host | 159 | 1360 |
| 2026-11-03T15:48:22.466744+00:00 | board to host | 33 | 1361 |
| 2026-11-03T15:48:32.383595+00:00 | board to host | 159 | 1364 |

Example host-only timing: component 48 sees board-to-host 159-byte UDP payload at 15:47:47.2938971Z, then host-to-board 167-byte payload at 15:47:47.2981062Z: 4.2091 ms apart. This is temporal adjacency, not a proven MQTT request/response match. Server plaintext sequence 656 was recorded at 15:47:47.295261Z, supporting temporal proximity only. The inbound 33-byte payloads are not labelled ACKs without QUIC decryption.

## Corresponding application records

Exact sequence-number joins between plaintext server CSV and serial log give 13 records in the full boundary slices and 12 with server receive UTC in the 60-second analysis interval. Their mean APP_RTT is 67.4666 ms. No specific encrypted packet has been labelled as an MQTT PUBLISH or echo.

| Seq | Server receive UTC | ESP log timestamp ms | APP_RTT ms |
|---:|---|---:|---:|
| 654 | 2026-11-03T15:47:37.274591Z | 3284884 | 70.275 |
| 655 | 2026-11-03T15:47:42.287155Z | 3289914 | 85.810 |
| 656 | 2026-11-03T15:47:47.295261Z | 3294944 | 105.789 |
| 657 | 2026-11-03T15:47:52.304567Z | 3299874 | 25.463 |
| 658 | 2026-11-03T15:47:57.316159Z | 3304904 | 45.432 |
| 659 | 2026-11-03T15:48:02.324605Z | 3309934 | 65.310 |
| 660 | 2026-11-03T15:48:07.334873Z | 3314964 | 85.420 |
| 661 | 2026-11-03T15:48:12.346166Z | 3319994 | 105.423 |
| 662 | 2026-11-03T15:48:17.354684Z | 3324924 | 25.298 |
| 663 | 2026-11-03T15:48:22.364469Z | 3329954 | 45.189 |
| 664 | 2026-11-03T15:48:27.375654Z | 3334984 | 65.085 |
| 665 | 2026-11-03T15:48:32.384073Z | 3340014 | 85.105 |

## Findings, limitations and next diagnostic

No matching connection error/disconnect warnings occurred in the captured serial/server slices; sequence joins are consecutive. Sensor errors were zero. Pktmon reports no lost ETW events and zero packet-drop events. Nevertheless packet visibility is incomplete: the server and serial log record regular messages that have no matching packet observation in this export. Zero ETW loss therefore does not establish complete wire visibility, nor does missing observation prove packet loss.

This control capture shows short cross-component host residence for the datagrams it sees, but it cannot explain or exclude ESP MQTT poll delay, mutex waits, QUIC retransmission timing or the earlier Lag-induced increase. It did not measure a Lag-on period. Host-only event adjacency cannot be substituted for ESP APP_RTT.

Next minimal diagnostic: first establish reliable complete visibility at a single appropriate hotspot capture point using a separately authorized passive capture; compare its packet counts against Pktmon/interface counters and server records. Only after that should an operator-controlled on/off comparison be used to locate actual added host delay. No firmware modification is justified from this incomplete trace alone.

Artifacts: original university_quic.etl, full university_quic.txt/university_quic.pcapng, bounded university_quic_analysis_60s.pcapng, packet_timing_60s.csv, packet_observations.json, corresponding_app_rtt.csv, log slices, component inventories, command transcript and boundary metadata. SHA-256 values are in SHA256SUMS.txt.
