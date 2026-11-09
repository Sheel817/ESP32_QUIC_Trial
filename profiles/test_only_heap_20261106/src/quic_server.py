import asyncio
import csv
import ipaddress
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import (
    ConnectionTerminated,
    HandshakeCompleted,
    StreamDataReceived,
)
from aioquic.tls import CipherSuite
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


class SensorCsvLog:
    fields = (
        "server_receive_utc", "client_id", "topic", "seq", "sensor",
        "uptime_ms", "temperature_c", "humidity_pct", "sensor_error",
    )

    def __init__(self, folder, prefix="sensor"):
        logs = folder.resolve() / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        self.file = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", delete=False,
            prefix=f"{prefix}_{stamp}_", suffix=".csv", dir=logs,
        )
        self.path = Path(self.file.name).resolve()
        self.writer = csv.DictWriter(self.file, fieldnames=self.fields)
        try:
            self.writer.writeheader()
            self.file.flush()
        except (OSError, csv.Error, ValueError):
            self.close()
            raise
        print(f"CSV log: {self.path}", flush=True)

    def record(self, received_utc, client_id, topic, payload):
        try:
            reading = json.loads(payload)
            if not isinstance(reading, dict):
                raise ValueError("publication JSON must be an object")
        except (ValueError, UnicodeError) as error:
            print(
                f"CSV JSON ERROR [client={client_id!r}, topic={topic!r}]: {error}",
                file=sys.stderr, flush=True,
            )
            return

        if "sensor" not in reading:
            return  # Other JSON publications still use the existing echo.

        # Keep laptop UTC and ESP32 uptime as independent clock values.
        row = {field: reading.get(field) for field in self.fields}
        row.update(server_receive_utc=received_utc, client_id=client_id, topic=topic)
        try:
            self.writer.writerow(row)
            self.file.flush()
        except (OSError, csv.Error, ValueError) as error:
            print(f"CSV WRITE ERROR [{self.path}]: {error}", file=sys.stderr, flush=True)

    def close(self):
        try:
            self.file.close()
        except OSError as error:
            print(f"CSV CLOSE ERROR [{self.path}]: {error}", file=sys.stderr, flush=True)


def server_config(folder):
    cert_path = folder / "server-cert.pem"
    key_path = folder / "server-key.pem"

    if cert_path.exists() != key_path.exists():
        raise ValueError("Certificate and key must both be present")

    if not cert_path.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
        ])
        now = datetime.now(timezone.utc)

        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=90))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                    x509.IPAddress(ipaddress.ip_address("192.168.137.1")),
                ]),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )

        key_path.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        cert_path.write_bytes(
            cert.public_bytes(serialization.Encoding.PEM)
        )
        print("Created local test certificate and key", flush=True)

    config = QuicConfiguration(
        is_client=False,
        alpn_protocols=["mqtt"],
        idle_timeout=60,
        max_data=16384,
        max_stream_data=8192,
        cipher_suites=[CipherSuite.AES_128_GCM_SHA256],
    )
    config.load_cert_chain(str(cert_path), str(key_path))
    return config


def mqtt_frame(header, body):
    remaining = len(body)
    encoded = bytearray()

    while True:
        digit = remaining % 128
        remaining //= 128
        encoded.append(digit | (128 if remaining else 0))
        if not remaining:
            return bytes([header]) + bytes(encoded) + body


def take_packet(buffer):
    remaining = 0

    for index in range(1, 5):
        if len(buffer) <= index:
            return None

        remaining += (buffer[index] & 127) << (7 * (index - 1))

        if remaining > 4096:
            raise ValueError("Demo packet exceeds 4096 bytes")

        if not buffer[index] & 128:
            end = index + 1 + remaining
            if len(buffer) < end:
                return None

            result = buffer[0], bytes(buffer[index + 1:end])
            del buffer[:end]
            return result

    raise ValueError("Invalid MQTT remaining length")


def read_text(body, offset):
    if len(body) < offset + 2:
        raise ValueError("Truncated MQTT string")

    size = int.from_bytes(body[offset:offset + 2], "big")
    end = offset + 2 + size

    if not size or end > len(body):
        raise ValueError("Invalid MQTT string length")

    return body[offset + 2:end].decode("utf-8"), end


class DemoServer(QuicConnectionProtocol):
    """Single-stream responder for this demo's MQTT 3.1.1 / QoS 0 traffic."""

    def __init__(self, *args, sensor_log=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_log = sensor_log
        self.client_id = None
        self.buffer = bytearray()
        self.stream_id = None
        self.connected = False
        self.subscriptions = set()

    def reply(self, header, body=b""):
        self._quic.send_stream_data(
            self.stream_id, mqtt_frame(header, body)
        )

    def process_packet(self, header, body):
        if header == 0x10 and not self.connected:
            if (
                len(body) < 12
                or body[:7] != b"\x00\x04MQTT\x04"
                or body[7] != 2
            ):
                raise ValueError(
                    "Demo requires MQTT 3.1.1 with a clean session"
                )

            client_id, end = read_text(body, 10)
            if end != len(body):
                raise ValueError("Unexpected CONNECT fields")

            self.connected = True
            self.client_id = client_id
            self.reply(0x20, b"\x00\x00")
            print(f"MQTT CONNECT accepted: {client_id}", flush=True)

        elif not self.connected:
            raise ValueError("CONNECT must be first")

        elif header in (0x82, 0xA2):
            if len(body) < 5 or body[:2] == b"\x00\x00":
                raise ValueError("Invalid subscription packet")

            position = 2
            grants = bytearray()

            while position < len(body):
                topic, position = read_text(body, position)

                if header == 0xA2:
                    self.subscriptions.discard(topic)
                    continue

                if position >= len(body):
                    raise ValueError("Missing subscription QoS")

                qos = body[position]
                position += 1

                if (
                    qos == 0
                    and "+" not in topic
                    and "#" not in topic
                    and len(self.subscriptions) < 16
                ):
                    self.subscriptions.add(topic)
                    grants.append(0)
                    print(f"SUBSCRIBED: {topic}", flush=True)
                else:
                    grants.append(0x80)

            self.reply(
                0x90 if header == 0x82 else 0xB0,
                body[:2] + bytes(grants),
            )

        elif header == 0x30:
            received_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            topic, position = read_text(body, 0)
            payload = body[position:].decode("utf-8", errors="backslashreplace")
            print(f"RECEIVED [{topic}]: {payload}", flush=True)

            if topic in self.subscriptions:
                self.reply(0x30, body)
                print("Demo publication returned to ESP32", flush=True)

            if self.sensor_log is not None:
                self.sensor_log.record(
                    received_utc, self.client_id, topic, body[position:]
                )

        elif header == 0xC0 and not body:
            self.reply(0xD0)

        elif header == 0xE0 and not body:
            self.connected = False
            self.close(reason_phrase="MQTT disconnect")

        else:
            raise ValueError(
                f"Unsupported demo packet: 0x{header:02x}"
            )

    def quic_event_received(self, event):
        if isinstance(event, HandshakeCompleted):
            print(
                f"QUIC CONNECTED | ALPN={event.alpn_protocol}",
                flush=True,
            )

        elif isinstance(event, ConnectionTerminated):
            self.buffer.clear()
            print(
                f"QUIC CLOSED | code={event.error_code} | "
                f"{event.reason_phrase}",
                flush=True,
            )

        elif isinstance(event, StreamDataReceived):
            try:
                if self.stream_id is None:
                    if event.stream_id % 4:
                        raise ValueError(
                            "Demo requires a client bidirectional stream"
                        )
                    self.stream_id = event.stream_id

                if event.stream_id != self.stream_id:
                    raise ValueError(
                        "Demo uses one stream per connection"
                    )

                self.buffer.extend(event.data)

                if len(self.buffer) > 8192:
                    raise ValueError("Demo receive buffer exceeded")

                while self.connected or self.buffer:
                    packet = take_packet(self.buffer)
                    if packet is None:
                        break
                    self.process_packet(*packet)

                if event.end_stream:
                    self.close(reason_phrase="Demo stream ended")

                self.transmit()

            except ValueError as error:
                print(f"DEMO ERROR: {error}", flush=True)
                self.close(
                    error_code=0x100,
                    reason_phrase=str(error),
                )


async def main():
    folder = Path(__file__).resolve().parent
    config = server_config(folder)
    sensor_log = None
    server = None
    try:
        try:
            sensor_log = SensorCsvLog(folder)
        except (OSError, csv.Error, ValueError) as error:
            print(
                f"CSV FILE ERROR [{folder / 'logs'}]: {error}; logging unavailable",
                file=sys.stderr, flush=True,
            )
        server = await serve(
            "0.0.0.0",
            14567,
            configuration=config,
            create_protocol=partial(DemoServer, sensor_log=sensor_log),
        )
        print("READY | QUIC UDP port 14567 | ALPN=mqtt", flush=True)
        await asyncio.Event().wait()
    finally:
        if server is not None:
            server.close()
        if sensor_log is not None:
            sensor_log.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")
