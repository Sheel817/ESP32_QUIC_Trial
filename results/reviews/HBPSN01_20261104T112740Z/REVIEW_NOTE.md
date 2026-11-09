# HBPSN-01 separate operator review note

Recorded UTC: **2026-11-04T11:29:18.164461+00:00**. This is the time this review note was saved, not the time of the experiment or of any screenshot.

Operator statement, supplied by the user in this session:

> The operator cannot confirm whether Clumsy remained unchanged during and after HBPSN-01.

Disposition: **FAILED_SETTINGS retained, validity NOT APPROVED**. The operator cannot confirm stability during the original fixed recording or afterwards. No stability confirmation is inferred from a pair of screenshots, unchanged-looking later GUI state, recovered RTTs or absence of logged connection errors. No current/late material is backdated. No original report, log, screenshot, recovery result, register row or frozen plan has been altered. This note is separate review evidence and does not classify the run as valid.

Original window: 4 November 2026, 02:38:26.327–03:15:26.327 Helsinki (UTC+02). HBPSN-01 remains the original QUIC CONTROL failed scheduled session. The earlier failed preflight and measured attempt remain preserved; neither is replaced or rerun by this note.

## Retry/replacement policy

The [unchanged frozen plan](../../experiments/HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED/EXPERIMENT_PLAN_PROPOSED_V1.md), under Reporting and failed-run policy, states exactly:

> No automatic replacement or extra run to improve results. Any later approved replacement gets a new ID and a deviation record and never overwrites the original or silently becomes the primary scheduled session.

It also distinguishes preflight-only failed attempts from a measured run: once a measured reset starts, retain the run even when startup/settings/connection checks fail. HBPSN-01 had a measured reset and therefore is not a preflight-only retry.

**Next scheduled run ID: HBPSN-02 — TCP_TLS — LAG100_OUT**, block 1, boot replicate 1, HOME_BOARD, WIFI_PS_NONE; configured 100 ms outbound Lag, other effects off, capture running. Its current status remains NOT_RUN. This identifies the next frozen-order session only; it does not authorize starting it now or changing settings now.

**No replacement attempt ID is currently approved or specified by the plan.** A replacement of HBPSN-01 would require later explicit approval, a genuinely new unique run ID and a dated deviation record. Do not reuse HBPSN-01, quietly add another measured attempt beneath it, overwrite the original attempt, assign HBPSN-02 as its replacement, or silently count replacement data as the original primary session. No replacement ID has been reserved or added to the 18-row register.

## Future evidence review gate

Use the [manual evidence checklist](./MANUAL_EVIDENCE_CHECKLIST.md). Automatic fixed-deadline processing remains enabled and unchanged. It can preserve raw logs and compute statistics even when evidence is missing. Processing completion is not evidence approval.

The successor recorder now reports automatic success candidates as PENDING_EVIDENCE_REVIEW, validity_status NOT_APPROVED, evidence_review_status PENDING_MANUAL_REVIEW. FINALIZED.json means processing finished. It does not emit an automatic COMPLETE.json or apply a positive register status. The register-update request omits status while review is pending; frozen register status vocabulary is unchanged. Operator confirmation must be considered by the reviewer, not inferred by the program.

No future run is to be called valid until required screenshots, timing/order, settings, operator stability confirmation and the rest of the frozen run checks have been reviewed. Missing, uncertain or contradictory confirmation remains flagged. Neither a screenshot-only PASS nor successful automatic analysis bypasses that review. The local pending-review label does not modify the frozen plan or retroactively change HBPSN-01.

Five focused tests passed, including automatic finalization with nominally passing machine checks staying NOT_APPROVED and omitting positive register status. See [test log](./review_gate_tests.log) and [preservation verification](./verification.json). No new 60-second or formal recording was needed for this review-gate change.

No board reset, firmware build/flash, Clumsy setting change, server/monitor reconfiguration or new formal run was performed.
