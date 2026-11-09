You are helping me run my thesis experiment (ESP32-C6, QUIC vs TCP/TLS 1.3). Work in:
C:\Users\newsh\Desktop\ESP32_QUIC_Trial
Python: .quic-venv\Scripts\python.exe
Experiment profile: results\experiments\HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED

This is formal thesis evidence. Rules for the whole session:
- Never invent, estimate or pre-fill a value. Every number must come from the files or the log.
- Never send a reset to the ESP32-C6 on COM6. Do not open COM6 at all unless I approve it.
- Back up every file before changing it (copy to <name>.bak_<UTC timestamp>).
- STOP and ask me at each point marked [ASK]. Wait for my answer before continuing.
- If anything doesn't match what I describe below, stop and report it rather than working around it.

GOAL: Close run HBPSN-08 (QUIC, LAG100_OUT), fix the collector overrun, then stage HBPSN-09 (TCP_TLS, CONTROL).

STEP 1: Free COM6
1. Check whether PID 15980 exists and show its command line. The collector has been running about 12 hours, so the PID may have been reused.
2. List any python or other processes that could be holding COM6, with their command lines.
3. [ASK] Show me what you would stop. Only after I say yes: Stop-Process on the confirmed collector process(es).
4. Confirm COM6 is free by checking that no process holds it. Do not open the port to test it.

STEP 2: Evidence audit
1. Find runs\HBPSN-08\attempt_20261109T013410Z\ and its mirror under the experiment profile's runs\ folder. Report whether the two copies match (compare file lists and SHA-256).
2. Look for clumsy_post_manual.png in the attempt folder, the project root and runs\HBPSN-08\.
   - If found: compute SHA-256, record LastWriteTimeUtc and the Europe/Helsinki time, and append an entry to SHA256SUMS.json in the attempt folder (keep the existing entry format).
   - If not found: note the retained flag POST_SCREENSHOT_MISSING_DAEMON_OVERRUN for step 4.

STEP 3: Parse the log. Report before computing anything.
1. Open serial_raw.log (or serial.raw.log) read-only. Show me the first 40 lines, the lines around the boot/reset release, and the lines around the 37:00 mark, so I can confirm the timestamp and sample format.
2. Find the boot reset release timestamp in the log itself. My notes say 2026-11-09 03:34:15.271420 Helsinki, but the UTC version I wrote (01:34:15.271402Z) has different microseconds. Report what the log actually says.
3. The cutoff is the release timestamp + 2,220.000 s exactly. Ignore every line after it. Report the exact cutoff you used.
4. Exclude pre-reset lines and warm-up samples (uptime_ms < 60,000, seq 1–10).
5. Take the first 415 eligible samples inside the window. Check for missing, duplicate or out-of-order seq numbers and for any second reset inside the window.
   - If seq 11–425 are all present and in order, use them.
   - If not, [ASK] and show me exactly what is wrong. Never pad, interpolate or combine runs.
6. Compute on APP_RTT (ms): N, shortfall, mean, sample SD (n−1), min, median, nearest-rank P95 (rank = ceil(0.95 × N), which is 395 for N=415) and max. Use the same decimal places as the existing rows in run_register.csv.
7. Save the selected samples to hbpsn08_selected_samples.csv and the stats plus cutoff details to hbpsn08_stats.json in the attempt folder. Add both to SHA256SUMS.json.
8. [ASK] Show me the stats and the cutoff details before writing any records.

STEP 4: Write the audit records (only after my approval in step 3)
1. operator_confirmation.json: [ASK] Ask me directly whether the Clumsy filter
   udp and (udp.SrcPort == 14567 or udp.DstPort == 14567) with Lag 100 ms outbound
   was active for the entire collection window. Write the file only with my answer, word for word, and the actual time I gave it (Helsinki and UTC). Set "relayed": false, because I am the operator answering directly.
2. manual_review.json: disposition, sample_count and shortfall come from the step 3 results, not from my notes. retained_flags must include COLLECTOR_DAEMON_OVERRUN_POST_WINDOW_KILLED and WINDOW_CUTOFF_ENFORCED_AT_<actual cutoff time>, plus POST_SCREENSHOT_MISSING_DAEMON_OVERRUN if the screenshot was missing. If N < 415, the disposition must not be COMPLETE; [ASK] me instead.
3. Update the HBPSN-08 row in run_register.csv and in outputs\HOME_BOARD_WIFI_PS_NONE_20261104\run_register.xlsx (status, N, shortfall, mean, SD, min, median, P95, max).
   - CSV: hash rows 1–7 and every other row before and after the edit, and prove they are byte-identical.
   - XLSX: preserve the formatting. Compare every cell outside row 8 before and after and prove nothing else changed. If the library would drop formatting, formulas or other sheets, [ASK] first.
4. Add the new and changed files to SHA256SUMS.json.

STEP 5: Fix the collector overrun
1. Find the collector script (likely tools\run_recorder\hbpsn08_collector.py) and explain why it did not stop at 2,220 s.
2. Propose a fix: a hard stop at release + 2,220 s that closes the port cleanly without resetting the device, and writes a clean end-of-run marker.
3. [ASK] Show me the diff. Do not change any frozen file listed in freeze_manifest.json without telling me. If the collector is frozen, tell me how changing it affects the freeze before doing anything.

STEP 6: Preflight for HBPSN-09 (TCP_TLS, CONTROL)
1. Confirm from the plan and the register that row 9 is HBPSN-09, TCP_TLS, CONTROL (0 ms lag, 0% drop, all Clumsy functions off).
2. Compute the SHA-256 of profiles\wifi_ps_none_20261103\build\tcp_tls.bin and compare it with freeze_manifest.json. If it doesn't match, stop.
3. Check whether tcp_tls_server.py is already listening on TCP 14568. If not, show me the launch command.
4. Read EXPERIMENT_PLAN_PROPOSED_V1.md and tell me what it says about replacing failed runs (HBPSN-01 QUIC CONTROL and HBPSN-03 QUIC DROP1_OUT): numbering, order and when they should happen. Quote the relevant section only; don't decide anything.
5. [ASK] Flashing and launching the server: show me the exact commands and wait for my go. I will set Clumsy and take the pre-run screenshot myself.

FINAL REPORT
- HBPSN-08 stats table and disposition
- Files created or changed, with SHA-256
- Any discrepancies found (timestamps, mirror mismatch, seq gaps)
- HBPSN-09 readiness: ready / not ready, and why
