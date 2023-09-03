## Code Reference for `Node` Class

### Introduction

The `Node` class represents a node in a Distributed Hash Table (DHT) network. This class is crucial for the creation and maintenance of individual nodes in the DHT.

---

### Constructor

#### `__init__(ip: str, port: int, ping: bool)`

Initializes a Node instance with optional IP address, port, and ping settings.

- **Parameters**:
  - `ip` (str, optional): IP address of the node. Defaults to None.
  - `port` (int, optional): Port number of the node. Defaults to None.
  - `ping` (bool, optional): Whether the node should connect to bootstrap. Defaults to False.

---

### Methods

#### `generate_certificates(certs_dir: str) -> None`

**Description**: Generates certificates for the node.

- **Parameters**:
  - `certs_dir` (str): Directory where certificates will be stored.

---

#### `add_peer(node_id: str, ip: str, port: int) -> None`

**Description**: Adds a peer to the node's k-bucket.

- **Parameters**:
  - `node_id` (str): ID of the peer node.
  - `ip` (str): IP address of the peer.
  - `port` (int): Port number of the peer.

---

#### `remove_peer(ip: str, port: int) -> None`

**Description**: Removes a peer from the node's k-bucket.

- **Parameters**:
  - `ip` (str): IP address of the peer.
  - `port` (int): Port number of the peer.

---

#### `put(key: str, value: Any, ttl: int) -> None`

**Description**: Handles PUT requests for the node.

- **Parameters**:
  - `key` (str): Key for the data.
  - `value` (Any): Value to be stored.
  - `ttl` (int): Time-to-live for the data.

---

#### `get(key: str) -> Any`

**Description**: Handles GET requests for the node.

- **Parameters**:
  - `key` (str): Key for the data to be retrieved.

---

#### `get_closest_nodes(target_node_id: str, k: int) -> List[Node]`

**Description**: Finds the k closest nodes to a given target node ID.

- **Parameters**:
  - `target_node_id` (str): ID of the target node.
  - `k` (int, optional): Number of closest nodes to find. Defaults to value from `dht_config`.

---

#### `get_all_peers() -> List[Peer]`

**Description**: Returns a list of all peers in all k-buckets.

---

#### `generate_node_id(ip: str, port: int) -> str`

**Description**: Generates a unique node ID based on IP and port.

- **Parameters**:
  - `ip` (str, optional): IP address for the node. Defaults to the machine's IP address.
  - `port` (int, optional): Port number for the node. Defaults to None.

---

#### `from_ip_and_port(ip: str, port: int) -> Node`

**Description**: Constructs a Node instance using a given IP and port without generating a new ID.

- **Parameters**:
  - `ip` (str): IP address of the node.
  - `port` (int): Port number of the node.

---

### Special Methods

#### `__iter__() -> Iterator`

**Description**: Returns an iterator over the node's IP and port.

---

#### `__str__() -> str`

**Description**: Returns a string representation of the node.

---
