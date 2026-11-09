# HBPSN-01 QUIC CONTROL — blocked preflight

**NOT STARTED. Registered status remains NOT_RUN.** No controlled reset, recording start, deadline or formal sample exists for this attempt. The current TCP_TLS monitor and both servers remain untouched.

The frozen protocol `HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED_V1` requires this exact QUIC capture filter:

```text
udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)
```

The current GUI instead shows:

```text
(udp and (udp.SrcPort == 14567 or udp.DstPort == 14567)) or (tcp and (tcp.SrcPort == 14568 or tcp.DstPort == 14568))
```

Capture is running and all effects are unchecked. The additional TCP 14568 branch differs from the frozen transport-specific filter. Per the user's instruction to report failed checks rather than retry, no filter change, flash or reset was performed. The intended correction before a future start is the exact frozen UDP-only filter above; the run has not been silently adapted to the combined filter.

[GUI screenshot evidence](./preflight_clumsy_20261104T001824Z.jpg). The requested CONTROL/effects-off state is recorded as operator-reported; the actual filter/capture/effect-checkbox state was independently observed in the GUI.

Plan SHA-256: `6f6ff7f695581c293f9113498f460d1d0a2edd5f9c0d2ae3fd551cacb40947be`. Freeze-manifest SHA-256: `e37bf26c0701ab185ae2e03b1cd5e0c6e9f0f89a1abef5c50deafed6c385a60e`. Frozen-file checks and all four preserved QUIC firmware artifact checks match: **True**. Application SHA-256 is `6c20b3dbf72d6859997a70c39f27ae0dd42791437a98c9aba93d8c017bfce198`. Configuration/source/flash-argument hashes and absolute paths are in [preflight evidence](./preflight_attempt_20261104T001824Z.json).

COM6 enumerates as the expected CP210x adapter; the existing monitor's startup log contains the expected HOME_BOARD MAC. A fresh Espressif identification or profile startup was not attempted after the filter check failed. Both run-register files are unchanged and all 18 rows remain NOT_RUN.

No 37-minute timer or collection was started, and no RUNNING status or finish time is claimed. This is setup-failure evidence, not a failed measured boot or a replacement run.
