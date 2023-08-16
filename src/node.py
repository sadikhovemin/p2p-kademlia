import hashlib
import socket
from bucket import KBucket
import asyncio

from message_codes import MessageCodes


class Node:
    def __init__(self, ip=None, port=None):
        self.id = self.generate_node_id(ip, port) if (ip and port) else None
        self.ip = ip
        self.port = port
        self.k_buckets = [KBucket(k_size=20) for _ in range(256)]
        if self.id:  # <-- Add this check
            print("Node is created with ", ip, " and a port ", port)
            print("Node id is ", self.id)

    def add_contact(self, node_id, ip, port):
        print("add contact function called for ", node_id)
        distance = self.calculate_distance(self.id, node_id)
        bucket_index = self.get_bucket_index(distance)
        node_instance = Node(ip=ip, port=port)
        node_instance.id = node_id  # Manually set the ID without generating a new one
        self.k_buckets[bucket_index].add(node_instance)

    @staticmethod
    def calculate_distance(id1, id2):
        return id1 ^ id2

    @staticmethod
    def get_bucket_index(distance):
        return distance.bit_length() - 1

    def bootstrappable_neighbors(self):
        neighbors = []
        for bucket in self.k_buckets:
            neighbors.extend([(node.ip, node.port) for node in bucket.get_nodes()])
        return neighbors

    @staticmethod
    def generate_node_id(ip=None, port=None):
        if ip is None:
            ip = socket.gethostbyname(socket.gethostname())
        unique_str = f"{ip}:{port}"
        return int(hashlib.sha256(unique_str.encode()).hexdigest(), 16)  # Convert to integer

    @classmethod
    def from_ip_and_port(cls, ip, port):
        """Constructs a Node instance using given IP and port without generating a new ID."""
        instance = cls(ip=ip, port=port)
        instance.id = None
        return instance

    async def bootstrap_from(self):
        bootstrap_ip = "localhost"
        bootstrap_port = 7401
        reader, writer = await asyncio.open_connection(bootstrap_ip, bootstrap_port)

        # Sending a 'ping' message to bootstrap node using DHT_PING code.
        ping_msg = MessageCodes.DHT_PING.value.to_bytes(2, 'big')
        writer.write(ping_msg)
        data = await reader.read(2)

        if data == MessageCodes.DHT_PONG.value.to_bytes(2, 'big'):
            print(f"Successfully bootstrapped from {bootstrap_ip}:{bootstrap_port}")

            # Add bootstrap node to k-bucket (since we don't have the bootstrap node's ID, we can't add it to the k-bucket)
        else:
            print(f"Failed to bootstrap from {bootstrap_ip}:{bootstrap_port}")

        writer.close()
        await writer.wait_closed()
