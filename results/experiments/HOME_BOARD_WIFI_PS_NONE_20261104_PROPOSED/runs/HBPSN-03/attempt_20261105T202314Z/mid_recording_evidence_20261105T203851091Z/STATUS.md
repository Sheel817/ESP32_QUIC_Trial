# HBPSN-03 actual image captured before deadline

At actual UTC **2026-11-05T20:38:51.091Z?2026-11-05T20:38:51.879Z**, the [image](./HBPSN-03_Clumsy_MID_RECORDING.jpg) shows matching required UDP filter/capture/Drop1% outbound-only settings and all other main effects off. SHA256 **ee6e631987be2d4dd4ba7bf34fed70a5a650a284581f81b274a2dd3e030a7050**. Actual image acquisition was **1383.322525 seconds before** the original deadline; it cannot satisfy post-recording evidence and is never backdated.

At check UTC 2026-11-05T20:40:17.819479+00:00, the collector has not finalized because the original recording ends at **2026-11-05 23:01:54.413525 Helsinki** (UTC21:01:54.413525). Its heartbeat and monitor remain active. [Status check](./recording_status_check.json) preserves file-presence checks and actual timing. Collector heartbeat label STARTUP_PENDING is an implementation label after fatal startup; authoritative run status remains FAILED_STARTUP.

[Initial-boot snapshot](./initial_boot_snapshot.raw.log), [separate post-reboot raw snapshot](./post_reboot_snapshot.raw.log), and [all post-reboot RTTs observed so far](./post_reboot_rtts_snapshot.json) are partial snapshots only. Initial-boot RTT count0, post-reboot observed180; post-reboot primary eligibility is false. Original full logs and prior crash diagnostics remain intact. No final counts or duration completion are claimed early.

Missing: actual post-deadline screenshot, operator stability confirmation covering recording through that image, and finalization outputs still awaiting the scheduled deadline. Settings review cannot override FAILED_STARTUP. HBPSN-01 FAILED_SETTINGS and HBPSN-02 COMPLETE with retained flags are unchanged; no registers modified.
