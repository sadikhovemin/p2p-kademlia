from dht_service import Service
import asyncio
import struct


class ApiProtocol(asyncio.Protocol):
    def init(self):
        """
        Initialize API protocol with a Service instance and a placeholder for transport.
        """
        self.service_handler = Service()
        self.data_transport = None

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

    def establish_connection(self, transport):
        """
        Connect to a transport endpoint.

        Args:
            transport: The transport endpoint to connect to.
        """
        self.data_transport = transport

    def process_incoming_data(self, data):
        """
        Process incoming data and respond accordingly.

        Args:
            data: The incoming data to process.
        """
        processed_data = self.service_handler.process_message(data)

        # If the processed data is None or False, disconnect.
        if not processed_data:
            return self.terminate_connection()

        self.data_transport.write(processed_data)

    def terminate_connection(self):
        """
        Disconnect the current connection.
        """
        if self.data_transport:
            self.data_transport.close()
            self.data_transport = None