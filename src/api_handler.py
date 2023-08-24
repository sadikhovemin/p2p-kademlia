import asyncio

from dht_service import Service


class Handler(asyncio.Protocol):
    def __init__(self, ip, port, node, initiator=False, data=None):
        self.ip = ip
        self.port = port
        self.node = node
        self.service = Service(node, self.connect_node_callback, self.put_connection)
        self.transport = None
        self.initiator = initiator
        self.data = data

    def connection_made(self, transport):
        print("connection made executed")
        self.transport = transport

        if self.node.ping and self.initiator:
            print("sending ping")
            # if self.connect_ip and self.connect_port:
            message = self.service.ping_service()
            self.transport.write(message)

        if self.data:
            print("data'ya geldim")
            self.transport.write(self.data)
            self.close_connection()


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

        if data == "Data stored successfully".encode():
            print("successfully stored the put request")
            return

        if data == "put calisti".encode():
            print("put works. no problems")
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

    async def connect_node(self, host, port, initiator):
        loop = asyncio.get_event_loop()
        await loop.create_connection(lambda: Handler(self.ip, self.port, self.node, initiator), host, port)

    async def connect_node_callback(self, host, port, initiator=False):
        await self.connect_node(host, port, initiator)

    async def put_connection(self, host, port, msg):
        loop = asyncio.get_event_loop()
        await loop.create_connection(lambda: Handler(self.ip, self.port, self.node, initiator=False, data=msg), host, port)
