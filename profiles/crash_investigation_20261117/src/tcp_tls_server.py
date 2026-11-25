"""MQTT demo over TCP/TLS, sharing the QUIC demo's MQTT and CSV behavior."""

import asyncio
import csv
import ssl
import sys
from pathlib import Path

from quic_server import DemoServer, SensorCsvLog, mqtt_frame, take_packet


def tls_context(folder):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.set_alpn_protocols(["mqtt"])
    context.load_cert_chain(folder / "server-cert.pem", folder / "server-key.pem")
    return context


class TcpMqttSession:
    # This method uses only MQTT session state, reply(), and close(). Reuse it
    # unchanged so validation, subscriptions, echo, PING and CSV match QUIC.
    process_packet = DemoServer.process_packet

    def __init__(self, writer, sensor_log):
        self.writer = writer
        self.sensor_log = sensor_log
        self.client_id = None
        self.connected = False
        self.subscriptions = set()
        self.closed = False

    def reply(self, header, body=b""):
        self.writer.write(mqtt_frame(header, body))

    def close(self, *, reason_phrase):
        print(f"TCP+TLS CLOSED | {reason_phrase}", flush=True)
        self.closed = True
        self.writer.close()


async def handle_client(reader, writer, sensor_log):
    tls = writer.get_extra_info("ssl_object")
    session = TcpMqttSession(writer, sensor_log)
    try:
        version = tls.version() if tls else None
        cipher = tls.cipher() if tls else None
        alpn = tls.selected_alpn_protocol() if tls else None
        print(
            f"TCP+TLS CONNECTED | TLS={version} | cipher={cipher} | ALPN={alpn}",
            flush=True,
        )
        if version != "TLSv1.3" or alpn != "mqtt":
            raise ValueError("TLS 1.3 and negotiated ALPN mqtt are required")

        buffer = bytearray()
        while not session.closed:
            data = await asyncio.wait_for(reader.read(4096), timeout=60)
            if not data:
                if buffer:
                    raise ValueError("Connection ended with an incomplete MQTT packet")
                break
            buffer.extend(data)
            if len(buffer) > 8192:
                raise ValueError("Demo receive buffer exceeded")
            while not session.closed:
                packet = take_packet(buffer)
                if packet is None:
                    break
                session.process_packet(*packet)
            if not session.closed:
                await writer.drain()
    except (ValueError, OSError, asyncio.TimeoutError) as error:
        print(f"TCP+TLS ERROR: {error}", file=sys.stderr, flush=True)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass


async def main():
    folder = Path(__file__).resolve().parent
    context = tls_context(folder)
    sensor_log = None
    clients = set()

    async def connected(reader, writer):
        task = asyncio.current_task()
        clients.add(task)
        try:
            await handle_client(reader, writer, sensor_log)
        finally:
            clients.discard(task)

    try:
        try:
            sensor_log = SensorCsvLog(folder, prefix="sensor_tcp_tls")
        except (OSError, csv.Error, ValueError) as error:
            print(
                f"CSV FILE ERROR [{folder / 'logs'}]: {error}; logging unavailable",
                file=sys.stderr, flush=True,
            )
        server = await asyncio.start_server(
            connected, "0.0.0.0", 14568, ssl=context, ssl_handshake_timeout=10,
        )
        async with server:
            print("READY | TCP+TLS port 14568 | ALPN=mqtt", flush=True)
            try:
                await server.serve_forever()
            finally:
                # Close the listener before cancelling clients and closing CSV.
                server.close()
                for task in tuple(clients):
                    task.cancel()
                await asyncio.gather(*tuple(clients), return_exceptions=True)
                await server.wait_closed()
    finally:
        if sensor_log is not None:
            sensor_log.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped", flush=True)
    except (OSError, ssl.SSLError) as error:
        print(f"TCP+TLS STARTUP ERROR: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
