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

    def get_nodes(self):
        """Return all nodes in the k-bucket."""
        return list(self.nodes)
