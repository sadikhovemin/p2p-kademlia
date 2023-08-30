import asyncio

from dht_service import Service
from loguru import logger
import struct


class Handler(asyncio.Protocol):
    def __init__(self, ip, port, node, initiator=False, data=None, put=False, get=False):
        self.ip = ip
        self.port = port
        self.node = node
        self.service = Service(node, self.connect_node_callback, self.put_connection, self.get_connection)
        self.transport = None
        self.initiator = initiator
        self.data = data
        self.put = put
        self.get = get
        self.buffer = None

    def connection_made(self, transport):
        # print("connection made executed")
        logger.info("connection made executed")
        self.transport = transport

        if self.node.ping and self.initiator:
            # print("sending ping")
            logger.info("sending ping")
            # if self.connect_ip and self.connect_port:
            message = self.service.ping_service()
            self.transport.write(message)

        if self.put:
            logger.info("connection_made put'a geldim")
            self.transport.write(self.data)
            self.close_connection()

        if self.get:
            if self.data is not None:
                self.transport.write(self.data)
            else:
                logger.error("Error: Result is None")

    def data_received(self, data):
        self.buffer = b''
        self.buffer += data  # Buffer the incoming data

        size = struct.unpack(">H", self.buffer[:2])[0]
        if len(data) == 0 or len(self.buffer) < size:
            return

        complete_message = self.buffer[:size]
        self.buffer = self.buffer[size:]

        logger.info("data received called")

        if data == "ok".encode():
            logger.info("so far works")
            return

        if data == "Data stored successfully".encode():
            logger.info("successfully stored the put request")
            return

        if data == "put calisti".encode():
            logger.info("put works. no problems")
            return

        if data == "get calisti".encode():
            logger.info("get works.")
            return

        if data == "Key not found".encode():
            logger.info("Key not found")
            return

        if data == "find_value_service calisti".encode():
            logger.info("find_value_service calisti")
            return

        asyncio.create_task(self.handle_response(complete_message))

    async def handle_response(self, data):
        result = await self.service.process_message(data)
        print("result", result)
        self.transport.write(result)

    def close_connection(self):
        """
        Disconnect the current connection.
        """
        # print("closing connection")
        logger.info("closing connection")
        if self.transport:
            self.transport.close()
            self.transport = None

    def start_periodic_check(self):
        asyncio.create_task(self.service.periodic_liveness_check())

    async def connect_node(self, host, port, initiator):
        loop = asyncio.get_event_loop()
        await loop.create_connection(lambda: Handler(self.ip, self.port, self.node, initiator), host, port)

    async def connect_node_callback(self, host, port, initiator=False):
        await self.connect_node(host, port, initiator)

    async def put_connection(self, host, port, msg):
        loop = asyncio.get_event_loop()
        await loop.create_connection(
            lambda: Handler(self.ip, self.port, self.node, initiator=False, data=msg, put=True), host, port)

    async def get_connection(self, host, port, msg):
        loop = asyncio.get_event_loop()
        await loop.create_connection(
            lambda: Handler(self.ip, self.port, self.node, initiator=False, data=msg, get=True), host, port)
