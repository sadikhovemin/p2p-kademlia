import hashlib
import time
from loguru import logger
from config.config import dht_config


class Storage:
    """This class provides methods for storing key-value pairs with expiration."""

    def __init__(self):
        self.data = {}
        self.tag = {}
        self.ttl = int(dht_config["ttl"])  # Time-to-live in seconds

    def put_(self, key, value, ttl):
        """
        Store the key-value pair along with a timestamp and its hashed value.

        :param key: The key to store the value.
        :param value: The value to be stored.
        :param ttl: Time-to-live for the key-value pair.
        """
        hashed_value = hashlib.sha1(value).hexdigest()
        expiry = time.time() + ttl
        self.data[key] = (value, expiry)
        self.tag[key] = hashed_value
        logger.info("Successfully stored on storage")

    def get_(self, key):
        """
        Retrieve the value for a given key if it exists and hasn't expired.

        :param key: The key for which the value needs to be retrieved.
        :return: The retrieved value or None if not found or expired.
        """
        value, expiry = self.data.get(key, (None, None))
        hashed_value = self.tag.get(key)

        if value is None or expiry is None:
            return None

        if hashed_value != hashlib.sha1(value).hexdigest():
            logger.error(
                f"HMAC failed. hashed_value: {hashed_value}, "
                f"hashlib.sha1: {hashlib.sha1(value).hexdigest()}"
            )
            return None

        if self._is_expired(key, expiry):
            return None

        return value

    def _is_expired(self, key, expiry):
        """
        Check if a key is expired and extend its lifetime if needed.

        :param key: The key to be checked.
        :param expiry: The current expiry time of the key.
        :return: True if the key is expired, False otherwise.
        """
        current_time = time.time()

        if current_time > expiry:
            del self.data[key]
            return True

        if expiry < current_time + self.ttl:
            new_expiry = current_time + self.ttl
            self.data[key] = (self.data[key][0], new_expiry)

        return False

    def cleanup_expired(self):
        """Remove expired entries from the storage."""
        current_time = time.time()
        keys_to_delete = [key for key, (_, expiry) in self.data.items() if current_time > expiry]

        for key in keys_to_delete:
            del self.data[key]
