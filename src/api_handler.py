import asyncio
import hashlib
import struct

from message_codes import MessageCodes
from dht_service import Service


class Handler(asyncio.Protocol):
    def __init__(self, ip, port, node):
        self.ip = ip
        self.port = port
        self.node = node
        self.service = Service(node)
        self.transport = None

    def connection_made(self, transport):
        print("connection made executed")
        self.transport = transport

    def data_received(self, data):
        print("calistim")
        asyncio.ensure_future(self.process_incoming_data(data))

    async def process_incoming_data(self, data):
        """
        Process incoming data and respond accordingly.
        """
        print("calistim")
        processed_data = await self.service.process_message(data)

        if not processed_data:
            return self.close_connection()

        if isinstance(processed_data, str):
            processed_data = processed_data.encode("utf-8")

        if self.transport:
            self.transport.write(processed_data)

        return processed_data

    # def connection_lost(self, exc):
    #     pass

    def close_connection(self):
        """
        Disconnect the current connection.
        """
        if self.transport:
            self.transport.close()
            self.transport = None

    async def send_ping(self, host, port):
        unique_str = f"{self.ip}:{self.port}"

        ip_parts = list(map(int, self.ip.split('.')))
        message = (struct.pack(">HH", 36, MessageCodes.DHT_PING.value) +
                   hashlib.sha256(unique_str.encode()).digest() +
                   struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.port))

        reader, writer = await asyncio.open_connection(host, port)
        writer.write(message)
        await writer.drain()
        data = await reader.read(1024)  # Read the PONG response from the bootstrap node

        print("PRINTING DATA ", data, host, port)

        from_bytes = int.from_bytes(data, 'big')
        print("from_bytes", from_bytes)
        # self.node.add_peer(from_bytes, host, port)

        writer.close()

        self.service.ping_service(host, port)

        return data
