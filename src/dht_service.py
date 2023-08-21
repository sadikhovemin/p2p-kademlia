import asyncio
import hashlib
import struct

from message_codes import MessageCodes
from node import Node


class Service:
    def __init__(self, node: Node, callback):
        self.data = {}
        self.node = node
        self.callback = callback

    def put_value(self, key, value):
        self.data[key] = value

    def get_value(self, key):
        return self.data.get(key)

    # TODO: mesaj alıp verdikten sonra size check yap.
    # TODO: ping pong with some frequency (update buckets based on ping pong responses)

    async def process_message(self, data):
        try:
            size = struct.unpack(">H", data[:2])[0]
            request_type = struct.unpack(">H", data[2:4])[0]
            print("size", size)
            print(len(data))
            if size == len(data):
                if request_type == MessageCodes.DHT_PING.value:
                    print("PING ALDIM")
                    return self.pong_service(data[4:])
                elif request_type == MessageCodes.DHT_PONG.value:
                    print("PONG ALDIM")
                    print(data)
                    ip_parts = struct.unpack(">BBBB", data[36:40])
                    ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
                    listening_port = struct.unpack(">H", data[40:42])[0]
                    self.node.add_peer(self.node.generate_node_id(ip_address, listening_port), ip_address,
                                       listening_port)
                    print("adding peer with ", ip_address, listening_port)
                    ip_parts = list(map(int, self.node.ip.split('.')))
                    return (struct.pack(">HH", 10, MessageCodes.DHT_FIND_NODE.value) +
                            struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))
                    # return MessageCodes.DHT_FIND_NODE.value

                elif request_type == MessageCodes.DHT_PUT.value:
                    return self.put_service(data[2:])
                elif request_type == MessageCodes.DHT_GET.value:
                    return self.get_service(data[2:])
                elif request_type == MessageCodes.DHT_FIND_NODE.value:
                    print("find_node geldim")
                    return self.find_node_service(data[4:])
                elif request_type == MessageCodes.DHT_NODE_REPLY.value:
                    print("node reply geldim")
                    # return data
                    nodes_to_connect = self.extract_nodes(data[4:])
                    print("below printing nodes to connect")
                    for n_c in nodes_to_connect:
                        print(n_c)
                        await asyncio.create_task(self.callback(n_c[0], n_c[1]))

                    return "ok".encode()

                    # return self.ping_service("127.0.0.1", 7401)
                else:
                    print(f"Invalid request type. Received {request_type}")
                    return False
            else:
                print("WRONG DATA SIZE")
        except Exception as e:
            print("MALFORMED MESSAGE error", e)

    def ping_service(self):
        unique_str = f"{self.node.ip}:{self.node.port}"
        ip_parts = list(map(int, self.node.ip.split('.')))
        message = (struct.pack(">HH", 42, MessageCodes.DHT_PING.value) +
                   hashlib.sha256(unique_str.encode()).digest() +
                   struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))
        print("sending ping message")
        return message

    def pong_service(self, data):
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

    def find_node_service(self, data):
        print("find_node_service called")
        ip_parts = struct.unpack(">BBBB", data[0:4])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        port = struct.unpack(">H", data[4:6])[0]
        print(ip_address, port)

        node_id = self.node.generate_node_id(ip_address, port)
        closest_nodes = self.node.get_closest_nodes(node_id)

        closest_nodes = self.filter_nodes(closest_nodes, node_id)
        """
        2 - size
        2 - message type
        2 - number of nodes
        len(closest_nodes) * 6 (ip, port) - Nodes
        """
        header = struct.pack(">HHH", 6 + len(closest_nodes) * 6, MessageCodes.DHT_NODE_REPLY.value, len(closest_nodes))
        packed_nodes = b''
        for n in closest_nodes:
            print("inner node", n)
            # pack each node
            ip_parts = [int(part) for part in n.ip.split('.')]
            # packed_ip = struct.pack(">BBBB", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3])

            node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], n.port)
            packed_nodes += node_data

        # combine header and nodes
        node_reply = header + packed_nodes
        print("local size", struct.unpack(">H", node_reply[:2])[0])
        return node_reply

        # return "finding node"

    def extract_nodes(self, data):
        num_nodes = struct.unpack(">H", data[:2])[0]
        print("num_nodes", num_nodes)
        nodes_to_connect = []
        prev, next = 2, 8

        for i in range(num_nodes):
            ip_parts = struct.unpack(">BBBB", data[prev:(next - 2)])
            ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
            port = struct.unpack(">H", data[(next - 2):next])[0]
            print("ip_address", ip_address)
            print("port", port)
            prev = next
            next += 6
            nodes_to_connect.append((ip_address, port))

        nodes_to_connect = self.filter_nodes_1(nodes_to_connect)

        return nodes_to_connect

    def filter_nodes(self, closest_nodes, node_id):
        print("to remove", node_id)
        return [node for node in closest_nodes if node.id != node_id and node not in self.node.k_buckets]

    def filter_nodes_1(self, nodes):
        print("my k bucket")

        k_bucket_nodes = set() # Create a set to hold the nodes that are in the k-buckets

        for bucket in self.node.k_buckets:
            for node in bucket.nodes:
                k_bucket_nodes.add((node.ip, node.port)) # Add the node's ip and port as a tuple to the set
                print(node)

        # Use a list comprehension to filter out any nodes that are in the k_bucket_nodes set
        # filtered_nodes = [node for node in nodes if node not in k_bucket_nodes]
        filtered_nodes = []
        for n in nodes:
            if n not in k_bucket_nodes:
                filtered_nodes.append(n)

        return filtered_nodes

