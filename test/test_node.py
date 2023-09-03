import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from src.node import Node


class TestNode:

    @pytest.fixture
    def node(self):
        return Node(ip='192.168.0.1', port=8000)

    @pytest.fixture
    def another_node(self):
        return Node(ip='192.168.0.2', port=8001)

    def test_generate_node_id(self, node):
        node_id = node.generate_node_id(ip='192.168.0.1', port=8000)
        # Expected: Ensure that the node ID is generated properly and is an integer.
        assert isinstance(node_id, int)

    def test_add_peer(self, node, another_node):
        node.add_peer(another_node.id, another_node.ip, another_node.port)
        # Expected: Peer should be added to the appropriate k-bucket.
        closest_nodes = node.get_closest_nodes(another_node.id)
        assert any(n.id == another_node.id for n in closest_nodes)

    def test_remove_peer(self, node, another_node):
        node.add_peer(another_node.id, another_node.ip, another_node.port)
        node.remove_peer(another_node.ip, another_node.port)
        # Expected: Peer should be removed from the k-bucket.
        closest_nodes = node.get_closest_nodes(another_node.id)
        assert all(n.id != another_node.id for n in closest_nodes)

    def test_put(self, node):
        key = b'some_key'
        value = b'some_value'
        node.put(key, value, ttl=10)
        # Expected: The value should be stored.
        assert key in node.storage.data

    def test_get(self, node):
        key = b'some_key'
        value = b'some_value'
        node.put(key, value, ttl=10)
        # Expected: The value should be retrieved.
        assert node.get(key) == value

    def test_calculate_distance(self, node, another_node):
        distance = node.calculate_distance(node.id, another_node.id)
        # Expected: Distance should be an integer.
        assert isinstance(distance, int)
