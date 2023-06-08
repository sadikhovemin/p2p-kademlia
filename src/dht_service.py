import struct
from message_codes import MessageCodes


class Service:
    def __init__(self):
        self.data = {}

    def put_value(self, key, value):
        self.data[key] = value

    def get_value(self, key):
        return self.data.get(key)

    def process_message(self, data):
        """
        Process the incoming request.

        Check the data size and perform the required action (PUT or GET).
        If the request is not valid, an error is raised.
        """
        if not self.validate_size(data):
            raise ValueError("Size mismatch in request data.")

        request_type = self.extract_message_type(data)

        if request_type == MessageCodes.DHT_PUT.value:
            return self.put_service(data[4:])
        elif request_type == MessageCodes.DHT_GET.value:
            return self.get_service(data[4:])
        else:
            raise ValueError(f"Invalid request type. Received {request_type}")

    @staticmethod
    def extract_message_type(data):
        """
        Getting bits from 16 to 32 -> 2:4 (message type)
        >H -> unsigned short integer
        """

        return struct.unpack(">H", data[2:4])

    @staticmethod
    def validate_size(data):
        """
        Check if the data size matches the expected size.

        The expected size is obtained from the first two bytes of the data.
        Returns True if sizes match, otherwise False.
        """
        expected_size = struct.unpack(">H", data[:2])[0]
        return expected_size == len(data)

    def get_service(self, data):
        key = data[0]  # Need to perform parsing
        return self.get_value(key)

    def put_service(self, data):
        key, value = data[0], data[1]  # Need to perform parsing
        return self.put_value(key, value)

    @staticmethod
    def dht_response(is_success, key, value=None):
        length = (4 + len(value) + len(key)) if is_success else (4 + len(key))
        message_code = MessageCodes.DHT_SUCCESS.value if is_success else MessageCodes.DHT_FAILURE.value
        return struct.pack(">HH", length, message_code) + key + (value if is_success else b'')
