import hashlib
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import time
import pytest
from src.storage import Storage


class TestStorage:
    @pytest.fixture
    def storage(self):
        storage = Storage()
        storage.ttl = 2
        return storage

    def test_put_(self, storage):
        # Test that the key-value pair is successfully added
        value = b'value1'
        key = hashlib.sha256(value).digest()

        storage.put_(key, value, ttl=2)
        assert key in storage.data  # Expected: Key should be in storage

    def test_get_existing(self, storage):
        # Test that an existing key returns the correct value
        value = b'value2'
        key = hashlib.sha256(value).digest()
        storage.put_(key, value, ttl=2)
        assert storage.get_(key) == value  # Expected: Retrieved value should be the same as the stored value

    def test_get_non_existing(self, storage):
        # Test that a non-existing key returns None
        assert storage.get_(b'non_existing_key') is None  # Expected: Should return None

    def test_get_expired(self, storage):
        # Test that an expired key returns None
        value = b'value3'
        key = hashlib.sha256(value).digest()
        storage.put_(key, value, ttl=1)
        value_retrieved = storage.get_(key)
        time.sleep(2)
        assert storage.get_(key) is None  # Expected: Should return None

    def test_is_expired(self, storage):
        # Test that _is_expired identifies an expired key
        value = b'value4'
        key = hashlib.sha256(value).digest()
        storage.put_(key, value, ttl=1)
        time.sleep(2)
        assert storage._is_expired(key, time.time() - 1)  # Expected: Should return True

    def test_not_expired(self, storage):
        # Test that _is_expired identifies a non-expired key
        key = b'key5'
        value = b'value5'
        storage.put_(key, value, ttl=4)
        assert not storage._is_expired(key, time.time() + 4)  # Expected: Should return False

    def test_cleanup_expired(self, storage):
        # Test that cleanup_expired removes expired keys and leaves others
        value1 = b'value6'
        key1= hashlib.sha256(value1).digest()
        storage.put_(key1, value1, ttl=1)

        value2 = b'value7'
        key2 = hashlib.sha256(value2).digest()
        storage.put_(key2, value2, ttl=5)

        time.sleep(2)
        storage.cleanup_expired()

        assert key1 not in storage.data  # Expected: key1 should be removed
        assert key2 in storage.data  # Expected: key2 should still be in storage
