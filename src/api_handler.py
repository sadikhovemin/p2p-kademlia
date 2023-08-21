import asyncio

from dht_service import Service


class Handler(asyncio.Protocol):
    def __init__(self, ip, port, node, initiator=False):
        self.ip = ip
        self.port = port
        self.node = node
        self.service = Service(node, self.connect_node_callback)
        self.transport = None
        self.initiator = initiator

    def connection_made(self, transport):
        print("connection made executed")
        self.transport = transport

        if self.node.ping and self.initiator:
            print("sending ping")
            # if self.connect_ip and self.connect_port:
            message = self.service.ping_service()
            self.transport.write(message)

    def data_received(self, data):
        if len(data) == 0:
            print("No response")
            return

        print("data received called")

        # if data == "ok".encode():
        #     print("so far works")
        #     return
        #
        # result = self.service.process_message(data)
        # print("result", result)
        # self.transport.write(result)

        if data == "ok".encode():
            print("so far works")
            return

        asyncio.create_task(self.handle_response(data))

    async def handle_response(self, data):
        result = await self.service.process_message(data)
        print("result", result)
        self.transport.write(result)

    def close_connection(self):
        """
        Disconnect the current connection.
        """
        print("closing connection")
        if self.transport:
            self.transport.close()
            self.transport = None

    # async def connect_node(self, host, port):
    #     loop = asyncio.get_event_loop()
    #     await loop.create_connection(lambda: self, host, port)

    async def connect_node(self, host, port):
        loop = asyncio.get_event_loop()
        await loop.create_connection(lambda: Handler(self.ip, self.port, self.node, initiator=True), host, port)

    async def connect_node_callback(self, host, port):
        await self.connect_node(host, port)