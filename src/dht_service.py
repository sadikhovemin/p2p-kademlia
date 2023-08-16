# import struct
# from message_codes import MessageCodes
#
#
# class Service:
#     def __init__(self):
#         self.data = {}
#
#     def put_value(self, key, value):
#         self.data[key] = value
#
#     def get_value(self, key):
#         return self.data.get(key)
#
#     def process_message(self, data):
#         request_type = struct.unpack(">H", data[0:2])[0]
#
#         if request_type == MessageCodes.DHT_PUT.value:
#             return self.put_service(data[2:])
#         elif request_type == MessageCodes.DHT_GET.value:
#             return self.get_service(data[2:])
#         elif request_type == MessageCodes.DHT_PING.value:
#             return self.ping_service()
#         else:
#             raise ValueError(f"Invalid request type. Received {request_type}")
#
#     def get_service(self, data):
#         key = data.decode()
#         value = self.get_value(key)
#         if value is not None:
#             return self.dht_response(True, key, value)
#         else:
#             return self.dht_response(False, key)
#
#     def put_service(self, data):
#         key_value = data.decode().split(" ")
#         if len(key_value) != 2:
#             raise ValueError("Invalid PUT request format.")
#         key, value = key_value
#         self.put_value(key, value)
#         return self.dht_response(True, key, value)
#
#     def ping_service(self):
#         return MessageCodes.DHT_PONG.value.to_bytes(2, 'big')
#
#     def pong_service(self):
#         return MessageCodes.DHT_PONG.value.to_bytes(2, 'big')
#
#     @staticmethod
#     def dht_response(is_success, key, value=None):
#         response_code = MessageCodes.DHT_SUCCESS.value if is_success else MessageCodes.DHT_FAILURE.value
#         message = f"{response_code} {key}"
#         if value is not None:
#             message += f" {value}"
#         return message.encode()


import struct

import aiomas

from message_codes import MessageCodes
import hashlib


class Service:
    def __init__(self):
        self.data = {}

    def put_value(self, key, value):
        self.data[key] = value

    def get_value(self, key):
        return self.data.get(key)

    # TODO: mesaj alıp verdikten sonra size check yap.

    async def process_message(self, data):
        request_type = struct.unpack(">H", data[2:4])[0]

        if request_type == MessageCodes.DHT_PING.value:
            print("PING ALDIM")
            node_id = data[4:]
            return self.pong_service(node_id)
        elif request_type == MessageCodes.DHT_PONG.value:
            print("PONG ALDIM")
            #return self.pong_service()
        elif request_type == MessageCodes.DHT_PUT.value:
            return self.put_service(data[2:])
        elif request_type == MessageCodes.DHT_GET.value:
            return self.get_service(data[2:])

        else:
            print(f"Invalid request type. Received {request_type}")
            return False

    def get_service(self, data):
        key = data.decode()
        value = self.get_value(key)
        if value is not None:
            return self.dht_response(True, key, value)
        else:
            return self.dht_response(False, key)

    def put_service(self, data):
        key_value = data.decode().split(" ")
        if len(key_value) != 2:
            raise ValueError("Invalid PUT request format.")
        key, value = key_value
        self.put_value(key, value)
        return self.dht_response(True, key, value)

    def ping_service(self, host, port):
        print("ping sent")
        unique_str = f"{host}:{port}"

        return (struct.pack(">HH", 36, MessageCodes.DHT_PING.value) + \
            hashlib.sha256(unique_str.encode()).digest())


    def pong_service(self, node_id):
        print("ping received")
        integer_representation = int.from_bytes(node_id, 'big')
        print(integer_representation)
        return struct.pack(">HH", 36, MessageCodes.DHT_PONG.value) + node_id

    @staticmethod
    def dht_response(is_success, key, value=None):
        response_code = MessageCodes.DHT_SUCCESS.value if is_success else MessageCodes.DHT_FAILURE.value
        message = f"{response_code} {key}"
        if value is not None:
            message += f" {value}"
        return message.encode()