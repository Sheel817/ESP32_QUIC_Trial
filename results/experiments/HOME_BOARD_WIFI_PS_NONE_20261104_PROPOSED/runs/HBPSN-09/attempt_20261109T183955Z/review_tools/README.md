# HBPSN-09 review tools

Copies of the scripts and dry-run outputs used to set up and close HBPSN-09 on 2026-11-09 and 2026-11-10 Helsinki time. Preserved as a record; they are not part of the measurement.

- `preflight_hbpsn09.py`: TLS probe and setup flash.
- `prepare_hbpsn09_attempt.py`: created the attempt folder.
- `test_helper_contract.py`: tested `operator_settings_helper.py` against `reliability.py` with a stubbed screen grab.
- `inspect_hbpsn09_close.py`: read-only inspection for the review.
- `close_hbpsn09.py`: wrote `manual_review.json`, the register row 9 update and the manifest entries. This is the patched version that performed the write.
- `patch_close_hbpsn09.py`: added the two final operator statements to `close_hbpsn09.py`.
- `hbpsn09_dry_run.txt`: first dry-run output, with the earlier statement. Superseded.
- `hbpsn09_dry_run_2.txt`: dry-run output with the final statements.
- `close_hbpsn09_monitor.py`: closed the collector and monitor through the control file.

Source: `C:\Users\newsh\AppData\Local\Temp\claude\4e9dcdad4cec88bf\81c86969-987a-4405-be76-342318332c9d\scratchpad` (Claude Code session scratchpad, outside the project).
Copied: 2026-11-09T22:09:08.714691+00:00. The originals were left in place.

The closure and monitor scripts check hashes and state from before they ran, so they will stop if run again.
