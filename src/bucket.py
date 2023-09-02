from collections import deque
from loguru import logger


class KBucket:
    """Initialize the k-bucket with a given size."""
    def __init__(self, k_size: int):
        """
        :param k_size: Maximum size of the bucket.
        """
        self.k_size = k_size
        self.nodes = deque(maxlen=self.k_size)

    def add(self, node):
        """
        Add a node to the k-bucket or move it to the front if it exists.

        :param node: The node to be added.
        """
        if node in self.nodes:
            self.nodes.remove(node)
        elif len(self.nodes) >= self.k_size:
            self.nodes.pop()
        self.nodes.appendleft(node)

    def remove(self, node):
        """
        Remove a node from the k-bucket.

        :param node: The node to be removed.
        """
        if node in self.nodes:
            self.nodes.remove(node)

    def visualize_k_buckets(self):
        """Visualize the k-bucket structure."""
        for _, node in enumerate(self.nodes):
            logger.info(f"\tNode ID: {node.id}, IP: {node.ip}, Port: {node.port}")
