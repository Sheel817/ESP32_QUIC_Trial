# Logging comparison

The values in `logging_comparison.csv` are application round-trip time (RTT)
measurements in milliseconds. They measure the interval from immediately before
ESP32 `MQTT_Publish` to delivery of the returned publication to the ESP32's MQTT
callback, matched by JSON sequence number on `esp32/quic/test`.

Application RTT includes processing, logging, and scheduling delays. It is
different from ngtcp2's transport RTT. Both timestamps use ESP32
`esp_timer_get_time()`; laptop UTC and ESP32 uptime are not subtracted.

There was **one run per logging mode**, with 415 samples summarized for each.
The quiet sample consists of **the first 415 records selected from the quiet
log**. These are descriptive results for those two runs, not statistics across
multiple independent runs. The summary values and selection rule were supplied
by the user; raw RTT log filenames and the p95 calculation method were not
specified, and these values have not been recomputed from raw records here.

Logging was the only intended experimental variable. The quiet build preserves
the publication interval, payload construction, QoS, Wi-Fi configuration, and
QUIC processing schedule. It disables packet/frame traces and verbose message
diagnostics while retaining APP_RTT, connection status, warnings, and errors.
