import hashlib
import socket
from bucket import KBucket


class Node:
    def __init__(self, ip=None, port=None, ping = False):
        self.id = self.generate_node_id(ip, port) if (ip and port) else None
        self.ip = ip
        self.port = port
        self.ping = ping    # not a bootstrap
        self.k_buckets = [KBucket(k_size=8) for _ in range(5)]
        if self.id:
            print("Node is created with ", ip, " and a port ", port)
            print("Node id is ", self.id)

    def add_peer(self, node_id, ip, port):
        print("add peer function called for ", node_id)
        distance = self.calculate_distance(self.cut_node_id(self.id), self.cut_node_id(node_id))
        print("distance ", distance)
        bucket_index = self.get_bucket_index(distance)
        node_instance = Node(ip=ip, port=port)
        node_instance.id = node_id  # Manually set the ID without generating a new one

        # Check if the peer is already in the bucket
        existing_nodes = self.k_buckets[bucket_index].nodes
        if any(n.id == node_id for n in existing_nodes):
            print(f"Peer with ID {node_id}, IP {ip}, Port {port} already in the bucket")
        else:
            self.k_buckets[bucket_index].add(node_instance)

        i = 0
        for k in self.k_buckets:
            print("BUCKET", i)
            i += 1
            k.visualize_k_buckets()

    @staticmethod
    def cut_node_id(node_id):
        binary_representation = bin(node_id)[2:]  # [2:] to skip the "0b" prefix

        # temp = ""
        # for i in range(0, 256, 12):
        #     temp += binary_representation[i:i+1]

        last_five_bits = binary_representation[-5:]
        cut_node_id = int(last_five_bits, 2)
        # cut_node_id = int(temp, 2)

        print("cut node id", cut_node_id)
        return cut_node_id

    @staticmethod
    def calculate_distance(id1, id2):
        return id1 ^ id2

    @staticmethod
    def get_bucket_index(distance):
        if distance == 0:
            return 0
        return distance.bit_length() - 1

    def get_closest_nodes(self, target_node_id, k=8):
        distance_to_nodes = [(self.calculate_distance(self.cut_node_id(node.id), self.cut_node_id(target_node_id)), node)
                             for bucket in self.k_buckets for
                             node in bucket.nodes]
        distance_to_nodes.sort(key=lambda x: x[0])
        return [node for _, node in distance_to_nodes[:k]]

    @staticmethod
    def generate_node_id(ip=None, port=None):
        if ip is None:
            ip = socket.gethostbyname(socket.gethostname())
        unique_str = f"{ip}:{port}"
        # unique_str = f"{port}"
        return int(hashlib.sha256(unique_str.encode()).hexdigest(), 16)  # Convert to integer

    @classmethod
    def from_ip_and_port(cls, ip, port):
        """Constructs a Node instance using given IP and port without generating a new ID."""
        instance = cls(ip=ip, port=port)
        instance.id = None
        return instance

    def __str__(self):
        return f"Node(id={self.id}, ip={self.ip}, port={self.port})"