# TCP+TLS 12 h run: stall at 10.0 h, read-only analysis (18 Nov 2026)

Method: read-only. Serial log, server log/CSV, Windows event logs and the firmware source were read. COM6 was not opened, nothing was flashed or reset, and no code was changed.
Conclusion: the firmware did not freeze. From 10:17:55Z on, the board's packets stopped reaching the laptop while Wi-Fi still looked connected. The exact cause is **not proven**.

## Evidence (all times UTC, 18 Nov 2026)
- Until 10:17:55Z all normal: seq 7135-7195 echoed every 5 s, RTT sawtooth 27-108 ms, no warnings or errors, no DHT11 failure message, no panic or reboot, free heap flat at 270,012 B.
- Last message received by the server: seq 7195 (server CSV 10:17:55.390Z). Last echo received by the board: uptime 36,054.2 s (10:17:55.548Z). The board received nothing after that.
- The main loop kept running: a heap line at 10:18:14Z (free 265,340 B) and a keepalive-timeout warning ("MQTT process returned: 10") every 100 ms from 10:18:30Z to 10:18:55Z (248 lines in about 25 s).
- Free heap fell by 4,672 B between 10:17:14Z and 10:18:14Z, which fits unacknowledged data held by the TCP stack.
- Keepalive timing matches coreMQTT: ping after 30 s without receiving anything (about 36,084 s), 5 s ping-response timeout, first timeout at 36,089.3 s.
- The server's 60 s read timeout expired at 10:18:55.39Z and it closed the connection. The board logged the closed connection (`TLS read failed error=6`) at 10:18:55.617Z. The close from the server did reach the board, so the laptop-to-board direction still worked.
- Windows event logs 10:08Z-10:30Z: no Wi-Fi/hotspot/network events. WLAN-AutoConfig for the day only has the hotspot start-up (00:02-00:11Z). System log has a Defender definition update at 10:16:09-10:16:16Z (about 1.5 min before the stall, no visible effect) and an unrelated system-component entry at 10:09:30Z. The hotspot watchdog logged no outage.
- No Wi-Fi disconnect or IP-lost message on the board. There is no stack-usage logging, so stack headroom is unknown.
- Earlier small hiccups: RTT outliers of 167-387 ms at 02:10, 02:40, 03:10, 03:40, 04:10, 06:10 and 06:40 (roughly at :10/:40 minute marks), no gaps longer than 5.6 s between echoes before the stall.

## Where the firmware could block forever
No place found. TLS write has a 5 s deadline, TLS read 100 ms, TLS idle check 60 s, the MQTT process loop ran continuously (shown above), the DHT11 read is short and prints a warning on failure (none appeared). A write on a dead link succeeds into the TCP buffer, so the board only noticed through the MQTT keepalive and the server's close. Publishes after seq 7195 print nothing in quiet mode, so whether they were sent could not be confirmed.

## Ranked possible causes
1. **Board-to-laptop packets stopped arriving while the Wi-Fi link looked up** (most likely): hotspot sharing/NAT layer on the laptop, or a transmit stall in the ESP32 Wi-Fi driver.
2. **Laptop-side hotspot hiccup** (the repeating :10/:40 outliers show the laptop path has recurring small stalls; the stall time does not match one, so the link is unclear).
3. **Address-resolution (ARP) problem** between board and laptop: speculation, no direct evidence.
4. Unlikely: firmware hang (loop kept running), out of memory (265 KB free, minimum free heap unchanged), stack overflow or crash (no panic or reboot), server failure (its timeout fired on time).

## What would separate the causes next time (not done, no code changes during the QUIC run)
Log Wi-Fi signal strength and disconnect events, log unsent bytes on the connection, record a laptop packet capture on the hotspot interface during the run, ping the board from the laptop during a stall, and use a shorter application keepalive (about 10 s).
