from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a)
    s = s.replace(a, b)
rep("STATEMENT = 'I did not change any Clumsy setting during the HBPSN-09 run.'",
    "STATEMENT = 'I did not change any Clumsy setting from when I confirmed the declaration until after the HBPSN-09 run ended.'\n"
    "HOST_STATEMENT = 'Nothing was streaming or downloading on the laptop during the run.'\n"
    "RECEIPT_UTC, RECEIPT_HEL = '2026-11-09T21:56:15.0385818Z', '2026-11-09T23:56:15.0427938+02:00'\n"
    "CLOCK = 'First local clock observation while processing the operator message; original message send time unavailable'")
rep("         'OPERATOR_STATEMENT_COVERS_RUN_ONLY_NOT_PRE_RESET', 'SUPPLEMENTARY_IMAGE_TIMES_OPERATOR_STATED',", "         'SUPPLEMENTARY_IMAGE_TIMES_OPERATOR_STATED',")
rep("""'local receipt 2026-11-09T21:47:30Z, original send time unavailable. Settings evidence is operator-reported: the pre-run image does not show Clumsy and the '
             'pre-reset state rests on the declaration confirmed 75.94 s before reset release. """,
    """f'local receipt {RECEIPT_UTC}, original send time unavailable. Operator exact statement "{HOST_STATEMENT}" not relayed, same receipt. Settings evidence is operator-reported: the pre-run image does not show Clumsy and the '
             'pre-reset state rests on the declaration confirmed 75.94 s before reset release and the operator statement. """)
rep("""'exact_statement': STATEMENT, 'relayed': False, 'receipt_utc': '2026-11-09T21:47:30Z', 'receipt_helsinki': '2026-11-09T23:47:30+02:00',
        'receipt_clock_source': 'First local clock observation while processing the operator message, second precision; original message send time unavailable',
        'scope_as_worded': 'During the HBPSN-09 run. The reviewer has not extended it to the interval before the measured reset.', 'not_backdated': True},""",
    """'exact_statement': STATEMENT, 'relayed': False, 'receipt_utc': RECEIPT_UTC, 'receipt_helsinki': RECEIPT_HEL,
        'receipt_clock_source': CLOCK,
        'scope_as_worded': 'From operator confirmation of the declaration (receipt 2026-11-09T18:56:50.3253449Z) until after the run ended (fixed deadline 2026-11-09T19:35:06.268682Z).', 'not_backdated': True},
    'operator_host_activity_statement': {'exact_statement': HOST_STATEMENT, 'relayed': False, 'receipt_utc': RECEIPT_UTC, 'receipt_helsinki': RECEIPT_HEL, 'receipt_clock_source': CLOCK, 'not_backdated': True,
                                         'limit': 'Operator-reported; host network use was not measured.'},""")
rep("'finding': 'Only evidence of the Clumsy state before the measured reset.'", "'finding': 'Only evidence of the Clumsy setting values before the measured reset; the operator statement reports no change after this confirmation.'")
rep("Network use by them was not measured.'", "Network use was not measured; see operator_host_activity_statement.'")
p.write_text(s, encoding='utf-8')
