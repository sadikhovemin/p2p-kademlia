import hashlib
import os
import socket
import ssl
import subprocess

from bucket import KBucket
from storage import Storage
from loguru import logger
from config.config import dht_config


class Node:
    def __init__(self, ip=None, port=None, ping=False):
        self.id = self.generate_node_id(ip, port) if (ip and port) else None
        self.ip = ip
        self.port = port
        self.ping = ping  # not a bootstrap
        self.storage = Storage()
        self.k_buckets = [KBucket(k_size=int(dht_config["k"])) for _ in range(160)]
        if self.id:
            logger.info(f"Node is created with {ip} and a port {port}")
            logger.info(f"Node id is {self.id}")

        self.tls_dir = f"{ip}_{port}"
        certs_dir = os.path.join(os.path.dirname(__file__), f"../certificates/{self.tls_dir}")
        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir)
            self.generate_certificates(certs_dir)


    def generate_certificates(self, certs_dir):
        logger.info("Generating certificates...")
        try:
            key_file = f"{certs_dir}/{self.ip}_{self.port}.key"
            csr_file = f"{certs_dir}/{self.ip}_{self.port}.csr"
            cert_file = f"{certs_dir}/{self.ip}_{self.port}.crt"

            subprocess.run(
                ["openssl", "genpkey", "-algorithm", "RSA", "-out", key_file],
                check=True
            )

            # Generate CSR
            subprocess.run(
                ["openssl", "req", "-new", "-key", key_file, "-out", csr_file, "-subj", f"/CN={self.port}"],
                check=True
            )

            # Sign CSR
            ca_dir = os.path.join(os.path.dirname(__file__), "../certificates/CA")
            subprocess.run(
                ["openssl", "x509", "-req", "-in", csr_file, "-CA", f"{ca_dir}/ca.pem", "-CAkey",
                 f"{ca_dir}/ca.key", "-CAcreateserial", "-out", cert_file, "-days", "365"],
                check=True
            )

            logger.info("Certificates generated successfully.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate certificates: {str(e)}")

    def add_peer(self, node_id, ip, port):
        logger.info(f"add peer function called for {node_id}")
        distance = self.calculate_distance(self.cut_node_id(self.id), self.cut_node_id(node_id))
        logger.info(f"distance {distance}")
        bucket_index = self.get_bucket_index(distance)
        node_instance = Node(ip=ip, port=port)
        node_instance.id = node_id  # Manually set the ID without generating a new one

        # Check if the peer is already in the bucket
        existing_nodes = self.k_buckets[bucket_index].nodes
        if any(n.id == node_id for n in existing_nodes):
            logger.info(f"Peer with ID {node_id}, IP {ip}, Port {port} already in the bucket")
        elif len(self.k_buckets[bucket_index].nodes) == int(dht_config["k"]):
            logger.warning("Bucket is already full")
        else:
            self.k_buckets[bucket_index].add(node_instance)

        i = 0
        for k in self.k_buckets:
            logger.info(f"BUCKET {i}")
            i += 1
            k.visualize_k_buckets()

    def remove_peer(self, ip, port):
        """
        Remove a peer from the appropriate k-bucket based on its IP and port.
        """
        node_id = self.generate_node_id(ip, port)

        # Calculate the distance between the node IDs to determine the bucket index
        distance = self.calculate_distance(self.cut_node_id(self.id), self.cut_node_id(node_id))
        bucket_index = self.get_bucket_index(distance)

        # Find and remove the node from the bucket
        for node in self.k_buckets[bucket_index].nodes:
            if node.id == node_id:
                self.k_buckets[bucket_index].remove(node)
                logger.info(f"Removed peer with ID {node_id}, IP {ip}, Port {port}")
                return

        logger.error(f"Peer with IP {ip}, Port {port}, ID {node_id} not found in k-bucket.")

    def put(self, key, value, ttl):
        """Handles PUT requests."""
        # print("node put called")
        logger.info("node put called")
        self.storage.put_(key, value, ttl)

    def get(self, key):
        """Handles GET requests."""
        return self.storage.get_(key)

    @staticmethod
    def cut_node_id(node_id):
        binary_representation = bin(node_id)[2:]  # [2:] to skip the "0b" prefix

        # temp = ""
        # for i in range(0, 256, 12):
        #     temp += binary_representation[i:i+1]

        last_five_bits = binary_representation[-160:]
        cut_node_id = int(last_five_bits, 2)
        # cut_node_id = int(temp, 2)

        # logger.info(f"cut node id {cut_node_id}")
        return cut_node_id

    @staticmethod
    def calculate_distance(id1, id2):
        return id1 ^ id2

    @staticmethod
    def get_bucket_index(distance):
        if distance == 0:
            return 0
        return distance.bit_length() - 1

    def get_closest_nodes(self, target_node_id, k=int(dht_config["k"])):
        distance_to_nodes = [
            (self.calculate_distance(self.cut_node_id(node.id), self.cut_node_id(target_node_id)), node)
            for bucket in self.k_buckets for
            node in bucket.nodes]
        distance_to_nodes.sort(key=lambda x: x[0])
        return [node for _, node in distance_to_nodes[:k]]

    def get_all_peers(self):
        """Returns a list of all peers in all k-buckets."""
        all_peers = []
        for bucket in self.k_buckets:
            all_peers.extend(bucket.nodes)
        return all_peers

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

    def __iter__(self):
        return iter((self.ip, self.port))

    def __str__(self):
        return f"Node(id={self.id}, ip={self.ip}, port={self.port})"
