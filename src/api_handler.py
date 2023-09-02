import asyncio
import ssl
import struct
from loguru import logger
from dht_service import Service


class Handler(asyncio.Protocol):
    """This class handles asynchronous communication for a node."""

    def __init__(self, ip_address, port, node, initiator=False, ssl_context=None, data=None, put=False, get=False):
        self.ip = ip_address
        self.port = port
        self.node = node
        self.data = data
        self.put = put
        self.get = get
        self.initiator = initiator
        self.ssl_context = ssl_context
        self.buffer = None
        self.transport = None

        self.service = Service(
            node,
            self.connect_node_callback,
            self.put_connection,
            self.get_connection,
            self.load_ssl_context
        )

    def connection_made(self, transport):
        """Called when a connection is made."""
        logger.info("connection made executed")
        self.transport = transport

        if self.node.ping and self.initiator:
            logger.info("sending ping")
            message = self.service.ping_service()
            self.transport.write(message)

        if self.put:
            self.transport.write(self.data)
            self.close_connection()

        if self.get:
            if self.data:
                self.transport.write(self.data)
            else:
                logger.error("Error: Result is None")

    def data_received(self, data):
        """Handle incoming data and check against TCP streaming issues."""
        self.buffer = b''
        self.buffer += data
        size = struct.unpack(">H", self.buffer[:2])[0]

        if len(data) == 0 or len(self.buffer) < size:
            return

        complete_message = self.buffer[:size]
        self.buffer = self.buffer[size:]

        if data in [
            b"ok",
            b"Data stored successfully",
            b"put calisti",
            b"get calisti",
            b"Key not found",
            b"find_value_service calisti"
        ]:
            logger.info(data.decode())
            return

        asyncio.create_task(self.handle_response(complete_message))

    async def handle_response(self, data):
        """Handle the response message."""
        result = await self.service.process_message(data)
        self.transport.write(result)

    def close_connection(self):
        """Disconnect the current connection."""
        logger.info("closing connection")
        if self.transport:
            self.transport.close()
            self.transport = None

    def start_periodic_check(self):
        """Start periodic checks for node liveness."""
        asyncio.create_task(self.service.periodic_liveness_check())

    async def connect_node(self, host, port, initiator):
        """Connect to a node."""
        loop = asyncio.get_event_loop()
        ssl_context = self.load_ssl_context(host, port)
        await loop.create_connection(
            lambda: Handler(self.ip, self.port, self.node, initiator),
            host, port,
            ssl=ssl_context
        )

    async def connect_node_callback(self, host, port, initiator=False):
        """Callback to connect to a node."""
        await self.connect_node(host, port, initiator)

    async def put_connection(self, host, port, msg):
        """Establish a put connection."""
        loop = asyncio.get_event_loop()
        ssl_context = self.load_ssl_context(host, port)
        await loop.create_connection(
            lambda: Handler(self.ip, self.port, self.node, initiator=False, data=msg, put=True),
            host, port,
            ssl=ssl_context
        )

    async def get_connection(self, host, port, msg):
        """Establish a get connection."""
        loop = asyncio.get_event_loop()
        ssl_context = self.load_ssl_context(host, port)
        await loop.create_connection(
            lambda: Handler(self.ip, self.port, self.node, initiator=False, data=msg, get=True),
            host, port,
            ssl=ssl_context
        )

    def load_ssl_context(self, host, port):
        """Load the SSL context."""
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.load_cert_chain(
            certfile=f"../certificates/{host}_{port}/{host}_{port}.crt",
            keyfile=f"../certificates/{host}_{port}/{host}_{port}.key"
        )
        ssl_context.load_verify_locations(cafile="../certificates/CA/ca.pem")
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False
        return ssl_context
