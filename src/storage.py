import hashlib
import time
from config.config import dht_config
from loguru import logger

class Storage:
    def __init__(self):
        self.data = {}
        self.tag = {}
        self.ttl = int(dht_config["ttl"])  # Time-to-live in seconds (1 hour in this case)

    def put_(self, key, value, ttl):
        """Stores the key-value pair along with a timestamp."""

        hashed_value = hashlib.sha1(value).hexdigest()
        expiry = time.time() + ttl
        self.data[key] = (value, expiry)
        self.tag[key] = hashed_value
        print("successfully stored on storage")
        # logger.info("successfully stored on storage")

    def get_(self, key):
        """Retrieves the value for a given key if it exists and hasn't expired."""
        logger.info("on line 22")
        value, expiry = self.data.get(key, (None, None))
        hashed_value = self.tag.get(key)
        logger.info("on line 24")
        if value is None or expiry is None:
            return None

        if hashed_value != hashlib.sha1(value).hexdigest():
            logger.error(f"HMAC failed. hashed_value: {hashed_value}, hashlib.sha1{hashlib.sha1(value).hexdigest()}")
            return None

        current_time = time.time()
        if time.time() > expiry:
            del self.data[key]
            return None

        # UPDATE THE LOGIC FOR GET
        if expiry < current_time + self.ttl:
            new_expiry = current_time + self.ttl
            self.data[key] = (value, new_expiry)

        return value

    def cleanup_expired(self):
        """Removes expired entries."""
        current_time = time.time()
        keys_to_delete = [key for key, (_, expiry) in self.data.items() if current_time > expiry]
        for key in keys_to_delete:
            del self.data[key]
