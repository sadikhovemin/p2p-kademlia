import time


# TODO: HMAC integrity after TLS

class Storage:
    def __init__(self):
        self.data = {}
        self.ttl = 3600  # Time-to-live in seconds (1 hour in this case)

    def put_(self, key, value):
        """Stores the key-value pair along with a timestamp."""
        expiry = time.time() + self.ttl
        self.data[key] = (value, expiry)
        print("successfully stored on storage")

    def get_(self, key):
        """Retrieves the value for a given key if it exists and hasn't expired."""
        value, expiry = self.data.get(key, (None, None))
        if value is None:
            return None

        if time.time() > expiry:
            del self.data[key]
            return None

        return value

    def cleanup_expired(self):
        """Removes expired entries."""
        current_time = time.time()
        keys_to_delete = [key for key, (_, expiry) in self.data.items() if current_time > expiry]
        for key in keys_to_delete:
            del self.data[key]
