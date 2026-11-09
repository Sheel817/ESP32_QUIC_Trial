# HBPSN-08 attempt_20261109T013239Z: aborted

Reset release 2026-11-09T01:32:39.970769Z (collector PID 32192). Last heartbeat 01:32:46.127979Z.
Last serial receipt 01:32:47.503820Z, 7.53 s after release. 145 serial lines, 0 APP_RTT, one ROM banner,
no panic, startup gates not verified, no finalization files. collector.stderr.log is empty.
The reason it stopped is not recorded.

This attempt set row 8 of run_register.csv and run_register.xlsx to RUNNING (logged 01:32:39.983212Z).
Attempt 013410Z overwrote those row 8 values at 01:34:15Z and set startup PASS at 01:34:32Z.

Deviation: this attempt issued a measured reset, and the plan has no rule for a second measured reset
under one run ID. Its log ends before the point where HBPSN-03 panicked, so it is not evidence of a crash-free boot.
