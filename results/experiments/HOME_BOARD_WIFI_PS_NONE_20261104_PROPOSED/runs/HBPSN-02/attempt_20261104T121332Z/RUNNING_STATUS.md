# HBPSN-02 TCP_TLS LAG100_OUT — RUNNING

Actual measured start **2026-11-04T14:17:27.280042+02:00**. Fixed finish **2026-11-04T14:54:27.280042+02:00**, exactly 2,220 monotonic seconds after designated reset release. UTC 2026-11-04T12:17:27.280042+00:00–2026-11-04T12:54:27.280042+00:00. No extension or automatic measured-start retry.

HOME_BOARD MAC 40:4c:ca:56:bb:b0, COM6, WIFI_PS_NONE, TCP_TLS, configured Lag 100 ms outbound only, all other main effects off. Actual IP **192.168.137.212**. Startup gates all PASS: firmware/ELF prefix 1f661a4f7, TLS1.3 / TLS_AES_128_GCM_SHA256 / suite0x1301 / ALPNmqtt / certificate modeNONE, TCP_NODELAY=1, MQTT connection and subscription, requested/returned WIFI_PS_NONE(0). These refer to the new controlled boot, not flash setup boots.

Flash verification PASS for all three matching preserved images; no rebuild or firmware edits. [Flash output](./flash.log), [identification/setup resets](./identification_reset.json), [flash result](./flash_result.json). Setup-only resets precede measurement. Initial close-helper pipe-name query stalled; its helper alone was stopped before any hardware action. Pipe metadata then identified one collector-created client-end write pipe, and the SDK exit command gracefully closed only the old COM6 monitor. This setup issue and the no-command ambiguous-handle guard are preserved; no identification, flash or measured-start failure was retried. Original HBPSN-01 results/status remain unchanged; closing its live monitor added a separate monitor-exit event without rewriting its historical result files.

## Collector and persistent output

Version **repaired-v2-manual-review-gate**, collector SHA-256 `381f8c1561ac5137a2412a02baa95b82a27897972996737a1e29a98c114da91a`. Runtime source copied into this attempt before launch; [all runtime hashes](./collector_version.json). Collector PID 35072; monitor launcher PID 30024. It continues after this agent reply. Deadline worker is independent of heartbeat/report writes; bounded report retries and error journal remain active.

- [Serial fixed-window raw log](./serial.raw.log), [serial receipts](./serial_receipts.jsonl), [complete monitor stream](./monitor_stream.log).
- [Server stdout fixed-window log](./server.stdout.raw.log), [server stderr fixed-window log](./server.stderr.raw.log), [server sensor CSV raw tail](./server.sensor_csv.raw.log); matching receipt indexes remain alongside them.
- [Exact reset/start anchor and fresh boundaries](./reset_event.json), [startup checks](./startup_checks.json), [heartbeat](./heartbeat.json), [running metadata](./RUNNING.json), [preflight and firmware/configuration hashes](./preflight.json).

At the actual reset release, new source offsets were captured: stdout **63395**, stderr **51**, sensor CSV **33644**. Exact source paths, prefix hashes and snapshots are in [historical-prefix provenance](./historical_prefix_boundaries.json). All previous bare TCP errors lie before stderr byte51 and remain historical/unattributed. Every new error line is retained with a host receipt; unidentified peers cannot be inferred merely from an unlabelled error.

## Actual image evidence and validity

The previously verified [pre-reset image copy](./verified_prior_pre_reset.jpg) is preserved unchanged: 2026-11-04T11:59:26.536Z–11:59:26.994Z; SHA-256 7c376f1aeab829828f5687cc3fe2d00cf379315b847bf4e260108e817a453517.

A fresh actual [image](./clumsy_actual_pre_reset.jpg), not a request, was acquired 2026-11-04T12:17:11.463Z–2026-11-04T12:17:11.943Z, before this measured reset. SHA-256 **338fe985dccaca6cd3e03b6b9cdaa51ed000636424438bca2ea4b8d1a08af829**. Visually verified exact TCP14568 filter, capture running, Lag enabled100ms, Inbound off, Outbound on, and all seven other main effects off. No Clumsy setting was changed. [Nonce-linked actual-image evidence](./pre_run_settings_check.json).

At the fixed deadline, preserve the whole window; exclude initial-boot ESP log uptime below60,000ms and at/above2,220,000ms; select the first415 eligible APP_RTTs, retain extras/outliers, and report actual shortfalls, resets/gaps/errors. Do not extend recording. Automatic finalization writes CSV/statistics/provenance with validity **NOT_APPROVED / PENDING_MANUAL_REVIEW**. A missing post-run screenshot remains missing, even if a screenshot request exists. An actual post-recording image must be captured before any settings change, and reviewed with the operator's stability confirmation before any positive validity decision. No later evidence is backdated. The collector does not itself operate the GUI; an active read-only observer or operator must supply the actual post image. This status report does not claim a post image already exists.

Frozen plan/order unchanged; HBPSN-01 stays FAILED_SETTINGS. Only HBPSN-02's RUNNING row was applied to both registers; all other CSV rows remain byte-identical and the workbook guard confirmed other rows unchanged. No other tests, pings, builds or setting changes are to occur during recording.
