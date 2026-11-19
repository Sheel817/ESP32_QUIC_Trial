# QUIC 12 h run: receive stall at 11.53 h (read-only notes, 19 Nov 2026)

Method: read-only, serial log and server logs only. No code was changed, no hardware touched.

## Evidence (UTC)
- Normal until seq 8282: echo logged 23:51:52.000Z (board uptime 41,501 s). Server received seq 8282 at 23:51:51.785Z.
- Server received seq 8283 at 23:51:56.795Z and echoed it ("Demo publication returned to ESP32"). The board never logged an APP_RTT for 8283.
- 23:51:56.963Z (168 ms after the server received 8283): the board begins to log `MQTT process returned: 11` (MQTTNeedMoreBytes: a partial MQTT packet was received, more bytes needed), 299 times in about 30 s.
- 23:52:26.99Z: `returned: 10` (MQTTKeepAliveTimeout: ping got no response) every 100 ms until the capture end (16,541 lines). From 23:53:17Z `APP_RTT storage full; dropping pending seq=...` for seq 8283-8605.
- The board kept running: HEAPLOG line every 60 s until the end (free 174,228 B, min free 144,048 B unchanged), no panic, no reboot, no QUIC close/cleanup line.
- The board kept publishing: server CSV has every seq up to 8,621 inside the capture window (8,635 when the server was stopped at 00:21Z) and the server echoed all of them. So board-to-server worked; server-to-board did not.
- Hotspot watchdog: no outage. No Wi-Fi disconnect message on the board.

## Reading of the evidence (hypotheses, not proven)
1. Software in the board's receive path: the board started reading the echo of seq 8283, got only part of an MQTT packet, and never got or processed the rest, so every later echo and the ping response were stuck behind it. The 168 ms timing right after the server's echo supports this. Candidate areas: QUIC stream receive handling or the MQTT-over-QUIC transport receive buffer (a partial packet that is never completed).
2. A lost or undelivered QUIC packet that was not recovered (retransmission/flow-control problem) on the server-to-board path.
3. A Wi-Fi/hotspot problem in the server-to-board direction only. Less likely than 1 because the board had just started to receive the packet when the fault began.

Compared with the TCP+TLS stall (10.0 h): there the board-to-server direction died and the board's own loop kept running; here the opposite direction died. The two stalls do not look like the same fault. Both are unexplained.

## What would help (no code changes now)
Log the receive state (bytes buffered, bytes needed) when `returned: 11` repeats, log QUIC stream/connection state and flow-control credit, add a laptop packet capture, and let the board close and reconnect when the keepalive times out.
