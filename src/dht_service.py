import asyncio
import struct

from message_codes import MessageCodes
import hashlib
from node import Node


# TODO: Add bootstrap and other peers for normal peers

class Service:
    def __init__(self, node: Node):
        self.data = {}
        self.node = node

    def put_value(self, key, value):
        self.data[key] = value

    def get_value(self, key):
        return self.data.get(key)

    # TODO: mesaj alıp verdikten sonra size check yap.

    async def process_message(self, data):
        request_type = struct.unpack(">H", data[2:4])[0]

        try:
            size = struct.unpack(">H", data[:2])[0]
            print("size", size)
            print(len(data))
            if size == len(data):
                if request_type == MessageCodes.DHT_PING.value:
                    print("PING ALDIM")
                    node_id = data[4:]
                    return self.pong_service(node_id)
                elif request_type == MessageCodes.DHT_PONG.value:
                    print("PONG ALDIM")
                    print(data)
                    ip_parts = list(map(int, self.node.ip.split('.')))
                    return (struct.pack(">HH", 10, MessageCodes.DHT_FIND_NODE.value) +
                            struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))
                    # return MessageCodes.DHT_FIND_NODE.value
                    # self.node.add_peer(integer_representation, ip_address, listening_port)
                elif request_type == MessageCodes.DHT_PUT.value:
                    return self.put_service(data[2:])
                elif request_type == MessageCodes.DHT_GET.value:
                    return self.get_service(data[2:])
                elif request_type == MessageCodes.DHT_FIND_NODE.value:
                    print("find_node geldim")
                    return self.find_node_service(data[4:])
                elif request_type == MessageCodes.DHT_NODE_REPLY.value:
                    print("node reply geldim")
                    return self.ping_service("127.0.0.1", 7401)
                else:
                    print(f"Invalid request type. Received {request_type}")
                    return False
            else:
                print("WRONG DATA SIZE")
        except Exception as e:
            print("MALFORMED MESSAGE error", e)

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
        # self.node.add_peer(self.node.generate_node_id(host, port), host, port)

        return struct.pack(">HH", 36, MessageCodes.DHT_PING.value) + hashlib.sha256(unique_str.encode()).digest()

    def pong_service(self, data):
        print("ping received")
        node_id = data[0:32]
        integer_representation = int.from_bytes(node_id, 'big')
        print(integer_representation)
        ip_parts = struct.unpack(">BBBB", data[32:36])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        listening_port = struct.unpack(">H", data[36:38])[0]

        print(ip_address, listening_port)
        self.node.add_peer(integer_representation, ip_address, listening_port)
        ip_parts = list(map(int, self.node.ip.split('.')))

        return (struct.pack(">HH", 42, MessageCodes.DHT_PONG.value) +
                node_id +
                struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))
        # return struct.pack(">HH", 36, MessageCodes.DHT_PONG.value) + node_id

    '''
    1. GET/PUT
    2. After bootstrap
    3. With some frequency to keep buckets fresh
    '''

    def find_node_service(self, data):
        print("find_node_service called")
        ip_parts = struct.unpack(">BBBB", data[0:4])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        port = struct.unpack(">H", data[4:6])[0]
        print(ip_address, port)

        node_id = self.node.generate_node_id(ip_address, port)
        closest_nodes = self.node.get_closest_nodes(node_id)

        header = struct.pack(">HH", 6 + len(closest_nodes) * 6, MessageCodes.DHT_NODE_REPLY.value)
        packed_nodes = b''
        for n in closest_nodes:
            """
            2 - size
            2 - message type
            2 - number of nodes
            len(closest_nodes) * 6 (ip, port)
            """
            # pack each node
            node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port)
            packed_nodes += node_data

        # combine header and nodes
        node_reply = header + packed_nodes
        return node_reply

    @staticmethod
    def dht_response(is_success, key, value=None):
        response_code = MessageCodes.DHT_SUCCESS.value if is_success else MessageCodes.DHT_FAILURE.value
        message = f"{response_code} {key}"
        if value is not None:
            message += f" {value}"
        return message.encode()
