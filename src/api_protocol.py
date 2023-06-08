from dht_service import Service
import asyncio


class ApiProtocol(asyncio.Protocol):
    def __init__(self):
        """
        Initialize API protocol with a Service instance and a placeholder for transport.
        """
        self.service_handler = Service()
        self.data_transport = None

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
