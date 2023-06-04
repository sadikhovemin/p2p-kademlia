import struct
import message_codes
import dht


class Api:
    def __init__(self, host, port):
        self.dht = dht.DHT()
        self.host = host
        self.port = port

    def process_message(self, data):
        msg_type = self.extract_message_type(data)

        if msg_type == message_codes.DHT_PUT:
            return self.put_service(data[4:])
        elif msg_type == message_codes.DHT_GET:
            return self.put_service(data[4:])
        else:
            raise Exception(f"Invalid message type. Received {msg_type}")

    @staticmethod
    def extract_message_type(data):
        # Getting bits from 16 to 32 -> 2:4 (message type)
        # >H -> unsigned short integer
        return struct.unpack(">H", data[2:4])

    def get_service(self, data):
        key = data[0]  # Need to perform parsing
        return self.dht.get(key)

    def put_service(self, data):
        key, value = data[0], data[1]  # Need to perform parsing
        return self.dht.put(key, value)

    def failure(self):
        pass

    def success(self):
        pass
