## Code Reference for `Storage` Class

### Introduction

The `Storage` class provides methods for storing key-value pairs with expiration times. This class is an essential component in the Kademlia DHT for managing data storage in a decentralized manner.

---

### Constructor

#### `Storage()`

Initializes an empty data dictionary, a tag dictionary, and sets the Time-to-Live (`ttl`) for stored entries based on the configuration.

---

### Methods

#### `put_(key: str, value: Any, ttl: int) -> None`

**Description**: Stores a key-value pair along with a timestamp and its hashed value. 

- **Parameters**:
  - `key` (str): The key under which the value will be stored.
  - `value` (Any): The value to be stored.
  - `ttl` (int): Time-to-live for the key-value pair.

---

#### `get_(key: str) -> Any`

**Description**: Retrieves the value associated with a given key if it exists and hasn't expired.

- **Parameters**:
  - `key` (str): The key for which the value needs to be retrieved.
- **Returns**:
  - `value` (Any): The value associated with the key, or `None` if not found or expired.

---

#### `_is_expired(key: str, expiry: int) -> bool`

**Description**: Checks if a key-value pair has expired and extends its lifetime if necessary.

- **Parameters**:
  - `key` (str): The key to be checked.
  - `expiry` (int): The current expiry time for the key.
- **Returns**:
  - `bool`: `True` if the key is expired, `False` otherwise.

---

#### `cleanup_expired() -> None`

**Description**: Removes all expired entries from the storage.

- **Parameters**: None
- **Returns**: None

---

