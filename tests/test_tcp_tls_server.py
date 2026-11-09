import asyncio
import contextlib
import csv
import io
import json
import ssl
import unittest
from pathlib import Path

import tcp_tls_server
from quic_server import SensorCsvLog, mqtt_frame

ROOT = Path(__file__).resolve().parents[1]


def text(value):
    value = value.encode()
    return len(value).to_bytes(2, 'big') + value


async def packet(reader):
    header = (await reader.readexactly(1))[0]
    remaining = 0
    for index in range(4):
        digit = (await reader.readexactly(1))[0]
        remaining |= (digit & 127) << (index * 7)
        if not digit & 128:
            return header, await reader.readexactly(remaining)
    raise AssertionError('Invalid MQTT remaining length')


class TcpTlsIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_local_tls_mqtt_and_csv(self):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            server = asyncio.create_task(tcp_tls_server.main())
            writer = None
            try:
                async with asyncio.timeout(10):
                    while 'READY | TCP+TLS port 14568 | ALPN=mqtt' not in output.getvalue():
                        if server.done():
                            await server
                        await asyncio.sleep(0.01)
                log_path = Path(next(line.removeprefix('CSV log: ') for line in output.getvalue().splitlines() if line.startswith('CSV log: ')))
                self.assertEqual(log_path.parent, ROOT / 'logs')
                self.assertTrue(log_path.name.startswith('sensor_tcp_tls_'))
                client_context = ssl.create_default_context(cafile=str(ROOT / 'server-cert.pem'))
                client_context.minimum_version = ssl.TLSVersion.TLSv1_3
                client_context.maximum_version = ssl.TLSVersion.TLSv1_3
                client_context.set_alpn_protocols(['mqtt'])
                reader, writer = await asyncio.open_connection('127.0.0.1', 14568, ssl=client_context, server_hostname='localhost')
                tls = writer.get_extra_info('ssl_object')
                self.assertEqual(tls.version(), 'TLSv1.3')
                self.assertEqual(tls.selected_alpn_protocol(), 'mqtt')
                self.assertIsNotNone(tls.cipher())
                connect = mqtt_frame(0x10, b'\x00\x04MQTT\x04\x02\x00\x3c' + text('local_tcp_tls_test'))
                # Split CONNECT across TLS writes, including a partial header.
                for chunk in [connect[:1], connect[1:6], connect[6:]]:
                    writer.write(chunk)
                    await writer.drain()
                    await asyncio.sleep(0.02)
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0x20, b'\x00\x00'))
                topic = 'esp32/quic/test'
                good = dict(seq=1, sensor='DHT11', uptime_ms=5000, temperature_c=26.0, humidity_pct=33.0, sensor_error=0, padding='x'*150)
                body = text(topic) + json.dumps(good).encode()
                subscribe = mqtt_frame(0x82, b'\x00\x02' + text(topic) + b'\x00')
                # Combined SUBSCRIBE + PUBLISH; PUBLISH has multi-byte length.
                writer.write(subscribe + mqtt_frame(0x30, body))
                await writer.drain()
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0x90, b'\x00\x02\x00'))
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0x30, body))
                failed = dict(seq=2, sensor='DHT11', uptime_ms=10000, temperature_c=None, humidity_pct=None, sensor_error=263)
                bad_body = text(topic) + json.dumps(failed).encode()
                publication = mqtt_frame(0x30, bad_body)
                writer.write(publication[:3])
                await writer.drain()
                await asyncio.sleep(0.02)
                writer.write(publication[3:])
                await writer.drain()
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0x30, bad_body))
                malformed = text(topic) + b'{bad json'
                writer.write(mqtt_frame(0x30, malformed))
                await writer.drain()
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0x30, malformed))
                self.assertIn('CSV JSON ERROR', errors.getvalue())
                # Reopen before shutdown: validates header and immediate row flush.
                with log_path.open(encoding='utf-8', newline='') as file:
                    csv_reader = csv.DictReader(file)
                    self.assertEqual(csv_reader.fieldnames, list(SensorCsvLog.fields))
                    rows = list(csv_reader)
                self.assertEqual([row['seq'] for row in rows], ['1', '2'])
                self.assertEqual([row['sensor_error'] for row in rows], ['0', '263'])
                self.assertEqual(rows[1]['temperature_c'], '')
                self.assertTrue(all(row['client_id'] == 'local_tcp_tls_test' for row in rows))
                self.assertTrue(all(row['server_receive_utc'].endswith('Z') for row in rows))
                writer.write(mqtt_frame(0xC0, b'') + mqtt_frame(0xE0, b''))
                await writer.drain()
                self.assertEqual(await asyncio.wait_for(packet(reader), 5), (0xD0, b''))
                self.assertEqual(await asyncio.wait_for(reader.read(1), 5), b'')
                writer.close()
                await writer.wait_closed()
                writer = None
                # Missing mqtt ALPN must not be allowed to send MQTT traffic.
                no_alpn = ssl.create_default_context(cafile=str(ROOT / 'server-cert.pem'))
                no_alpn.minimum_version = ssl.TLSVersion.TLSv1_3
                r, w = await asyncio.open_connection('127.0.0.1', 14568, ssl=no_alpn, server_hostname='localhost')
                self.assertEqual(await asyncio.wait_for(r.read(1), 5), b'')
                w.close()
                await w.wait_closed()
                # TLS 1.2 cannot negotiate with the TLS 1.3-only listener.
                tls12 = ssl.create_default_context(cafile=str(ROOT / 'server-cert.pem'))
                tls12.minimum_version = ssl.TLSVersion.TLSv1_2
                tls12.maximum_version = ssl.TLSVersion.TLSv1_2
                tls12.set_alpn_protocols(['mqtt'])
                with self.assertRaises((ssl.SSLError, ConnectionError)):
                    await asyncio.wait_for(asyncio.open_connection('127.0.0.1', 14568, ssl=tls12, server_hostname='localhost'), 5)
                self.assertIn('TLS=TLSv1.3 | cipher=', output.getvalue())
                self.assertIn('ALPN=mqtt', output.getvalue())
                # Shutdown must also complete with an idle TLS client attached.
                reader, writer = await asyncio.open_connection('127.0.0.1', 14568, ssl=client_context, server_hostname='localhost')
                await asyncio.sleep(0.02)
                server.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(server, 5)
                self.assertEqual(await asyncio.wait_for(reader.read(1), 5), b'')
            finally:
                if writer is not None:
                    writer.close()
                    with contextlib.suppress(OSError):
                        await writer.wait_closed()
                server.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await server
                (ROOT / 'build/tcp_tls_server_test.log').write_text(output.getvalue() + errors.getvalue(), encoding='utf-8')
        # The test listener must be stopped, and the port released.
        with self.assertRaises(OSError):
            await asyncio.wait_for(asyncio.open_connection('127.0.0.1', 14568), 2)


if __name__ == '__main__':
    unittest.main()
