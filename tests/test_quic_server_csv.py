import contextlib
import asyncio
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from quic_server import DemoServer, SensorCsvLog, main


class SensorCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.output = io.StringIO()
        with contextlib.redirect_stdout(self.output):
            self.log = SensorCsvLog(self.folder)
        self.addCleanup(self.log.close)
        with patch('quic_server.QuicConnectionProtocol.__init__', return_value=None):
            self.server = DemoServer(sensor_log=self.log)
        self.server.reply = Mock()
        client = b'esp32_quic_client'
        self.server.process_packet(0x10, b'\x00\x04MQTT\x04\x02\x00\x00' + len(client).to_bytes(2, 'big') + client)
        self.server.subscriptions.add('esp32/quic/test')

    def publish(self, payload):
        topic = b'esp32/quic/test'
        body = len(topic).to_bytes(2, 'big') + topic + payload
        self.server.process_packet(0x30, body)
        self.server.reply.assert_called_with(0x30, body)

    def rows(self):
        with self.log.path.open(encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            self.assertEqual(reader.fieldnames, list(SensorCsvLog.fields))
            return list(reader)

    def test_readings_are_flushed_and_error_readings_echo(self):
        for seq, error in [(1, 0), (2, 263)]:
            reading = dict(seq=seq, sensor='DHT11', uptime_ms=seq * 5000,
                           temperature_c=26.0 if not error else None,
                           humidity_pct=33.0 if not error else None, sensor_error=error)
            self.publish(json.dumps(reading).encode())
            rows = self.rows()  # File remains open: verifies immediate flush.
            self.assertEqual(len(rows), seq)
            row = rows[-1]
            self.assertEqual(row['client_id'], 'esp32_quic_client')
            self.assertEqual(row['topic'], 'esp32/quic/test')
            self.assertEqual(row['uptime_ms'], str(seq * 5000))
            self.assertEqual(row['sensor_error'], str(error))
            self.assertTrue(row['server_receive_utc'].endswith('Z'))
            self.assertEqual(row['temperature_c'], '' if error else '26.0')

    def test_malformed_json_and_utf8_still_echo(self):
        for payload in [b'{broken', b'[]', b'\xff']:
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self.publish(payload)
            self.assertIn('CSV JSON ERROR', errors.getvalue())
        self.assertEqual(self.rows(), [])

    def test_write_and_flush_errors_still_echo(self):
        for target in ['writer', 'file']:
            replacement = Mock()
            if target == 'writer':
                replacement.writerow.side_effect = OSError('disk full')
            else:
                replacement.flush.side_effect = OSError('disk full')
            with patch.object(self.log, target, replacement):
                with contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.publish(b'{"sensor":"DHT11","sensor_error":0}')
                self.assertIn('CSV WRITE ERROR', errors.getvalue())
                self.assertIn(str(self.log.path), errors.getvalue())

    def test_new_file_for_every_run_and_startup_path(self):
        with contextlib.redirect_stdout(io.StringIO()):
            other = SensorCsvLog(self.folder)
        self.addCleanup(other.close)
        self.assertNotEqual(self.log.path, other.path)
        self.assertEqual(self.log.path.parent, self.folder / 'logs')
        self.assertIn(str(self.log.path), self.output.getvalue())
        self.assertTrue(self.log.path.is_absolute())

    def test_non_sensor_json_is_not_logged_but_echoes(self):
        self.publish(b'{"message":"hello"}')
        self.assertEqual(self.rows(), [])

    def test_startup_file_error_keeps_server_available(self):
        server = Mock()
        event = Mock(wait=AsyncMock(side_effect=asyncio.CancelledError))
        with patch('quic_server.server_config', return_value=Mock()):
            with patch('quic_server.SensorCsvLog', side_effect=OSError('permission denied')):
                with patch('quic_server.serve', new_callable=AsyncMock, return_value=server) as serve:
                    with patch('quic_server.asyncio.Event', return_value=event):
                        with contextlib.redirect_stderr(io.StringIO()) as errors:
                            with self.assertRaises(asyncio.CancelledError):
                                asyncio.run(main())
                    self.assertEqual(serve.call_args.args, ('0.0.0.0', 14567))
                    self.assertIsNone(serve.call_args.kwargs['create_protocol'].keywords['sensor_log'])
                    server.close.assert_called_once()
                    self.assertIn('CSV FILE ERROR', errors.getvalue())
                    self.assertIn('permission denied', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
