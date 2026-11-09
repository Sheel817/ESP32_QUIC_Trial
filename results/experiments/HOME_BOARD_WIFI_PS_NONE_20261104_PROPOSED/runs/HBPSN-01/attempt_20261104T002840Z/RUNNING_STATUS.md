# HBPSN-01 QUIC CONTROL — RUNNING

Actual reset-release start (UTC): 2026-11-04T00:38:26.326642+00:00

Actual start, Helsinki: 2026-11-04T02:38:26.326642+02:00

Fixed 37-minute deadline, Helsinki: 2026-11-04T03:15:26.326642+02:00

Fixed deadline (UTC): 2026-11-04T01:15:26.326642+00:00

Fresh startup gates all passed: HOME_BOARD MAC, matching QUIC ELF digest prefix, WIFI_PS_NONE requested/returned 0, assigned IP 192.168.137.212, QUIC/TLS/MQTT/subscription. Preserved QUIC profile flashed with all three artifact write hashes verified. Plan hash: 6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be.

Persistent collector PID 33972, monitor launcher PID 1776. Logging and the monotonic timer continue independently after the agent replies. The recording window will not be extended to obtain 415 values.

[Serial raw log](./serial.raw.log), [server stdout raw log](./server.stdout.raw.log), [server stderr raw log](./server.stderr.raw.log), [full persistent monitor stream](./monitor_stream.log), [reset/start/deadline](./reset_event.json), [startup checks](./startup_checks.json), [live heartbeat](./heartbeat.json), [run metadata](./metadata.json), [preflight/provenance](./preflight.json), [register update evidence](./register_running_update.json).

At the fixed deadline the collector preserves the complete raw interval, excludes ESP uptime below 60000 ms, selects the first 415 eligible initial-boot RTTs or records the shortfall, retains all outliers and extra/raw records, saves CSVs/statistics/errors/gaps/resets/provenance/hashes, and updates only HBPSN-01. It leaves the monitor and server running afterward. Any missing required post-recording settings evidence is explicitly flagged, never assumed passed; the data window remains fixed regardless of that evidence.

The earlier failed-preflight report and frozen plan are preserved. The other 17 register rows are unchanged and NOT_RUN. No pings, builds, firmware edits or other tests are scheduled during recording. Clumsy capture remains running with the exact QUIC-only filter and all effects off, as observed before the designated reset.
