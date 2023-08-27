from collections import deque

class KBucket:
    def __init__(self, k_size):
        self.k_size = k_size
        self.nodes = deque(maxlen=self.k_size)

    def add(self, node):
        """Add a node to the k-bucket."""
        if node in self.nodes:
            self.nodes.remove(node)
        elif len(self.nodes) >= self.k_size:
            self.nodes.pop()  # Evict the oldest node if the bucket is full
        self.nodes.appendleft(node)

    def remove(self, node):
        """Remove a node from the k-bucket."""
        if node in self.nodes:
            self.nodes.remove(node)

    def visualize_k_buckets(self):
        """Visualize the k-bucket structure in a human-readable format."""
        for i, node in enumerate(self.nodes):
            print(f"\tNode ID: {node.id}, IP: {node.ip}, Port: {node.port}")
            # logger.info(f"\tNode ID: {node.id}, IP: {node.ip}, Port: {node.port}")