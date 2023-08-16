# import asyncio
# import struct
#
# from message_codes import MessageCodes
#
#
# class Handler(asyncio.Protocol):
#     def __init__(self, ip, port, node, dht_service):
#         self.ip = ip
#         self.port = port
#         self.node = node
#         self.dht_service = dht_service
#
#     def connection_made(self, transport):
#         self.transport = transport
#
#     def data_received(self, data):
#         print("Received:", data)
#
#         # Handle PING and PONG messages
#         if struct.unpack(">H", data[:2])[0] == MessageCodes.DHT_PING.value:
#             self.transport.write(struct.pack(">H", MessageCodes.DHT_PONG.value))
#             print(f"Sent: {MessageCodes.DHT_PONG.value}")
#
#             # Add the connecting peer to the bootstrap node's k-bucket
#             peer_host, peer_port = self.transport.get_extra_info('peername')
#             peer_id = self.node.generate_node_id(peer_host, peer_port)
#             self.node.add_contact(peer_id, peer_host, peer_port)
#
#         # Handle other messages using the Service instance
#         else:
#             try:
#                 response = self.service.process_message(data)
#                 self.transport.write(response)
#             except ValueError as e:
#                 print(f"Invalid request: {e}")
#
#     def connection_lost(self, exc):
#         pass


import asyncio
import hashlib
import struct

from message_codes import MessageCodes


class Handler(asyncio.Protocol):
    def __init__(self, ip, port, node, dht_service):
        self.ip = ip
        self.port = port
        self.node = node
        self.service = dht_service
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

        message = (struct.pack(">HH", 36, MessageCodes.DHT_PING.value) +
                   hashlib.sha256(unique_str.encode()).digest())

        reader, writer = await asyncio.open_connection(host, port)
        writer.write(message)
        await writer.drain()
        data = await reader.read(1024)  # Read the PONG response from the bootstrap node

        writer.close()

        return data
