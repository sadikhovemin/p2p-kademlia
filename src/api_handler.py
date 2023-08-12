from dht_service import Service
import asyncio
import struct
from node import Node


class Handler(asyncio.Protocol):
    instances = set()

    def __init__(self, host, port):
        """
        Initialize API protocol with a Service instance and a placeholder for transport.
        """
        self.service_handler = Service()
        self.transport = None
        self.node = Node(node_id="", ip=host, port=port)
        self.connect_nodes = set()

        # Add the current instance to the instances set.
        Handler.instances.add(self)

    def connection_made(self, transport):
        print('hello world!')
        self.transport = transport
        peername = transport.get_extra_info('peername')
        print(f'Connection from {peername}')
        self.connect_nodes.add(peername)

    def connection_lost(self, exc):
        peername = self.transport.get_extra_info('peername')
        print(f'Connection lost from {peername}')
        self.connect_nodes.remove(peername)
        Handler.instances.remove(self)

    @classmethod
    def get_all_connected_nodes(cls):
        nodes = set()
        for instance in cls.instances:
            nodes |= instance.connect_nodes
        return nodes

    def data_received(self, data):
        header = data[:4]
        body = data[4:]

        msize = struct.unpack(">HH", header)[0]
        ttl, rep, res = struct.unpack(">HBB", data[4:8])
        print(msize, ttl, rep, res)

        key = data[8: int((256 / 8) + 8)]
        print("key length", len(key))
        val = data[int(8 + (256 / 8)):]

        print(f"DHT_PUT: ({key}:{val})")
        return True

    # def connection_made(self, transport):
    #     """
    #     Connect to a transport endpoint.
    #     """


    def process_incoming_data(self, data):
        """
        Process incoming data and respond accordingly.
        """
        processed_data = self.service_handler.process_message(data)

        # If the processed data is None or False, disconnect.
        if not processed_data:
            return self.close_connection()

        self.transport.write(processed_data)

    def close_connection(self):
        """
        Disconnect the current connection.
        """
        if self.transport:
            self.transport.close()
            self.transport = None
