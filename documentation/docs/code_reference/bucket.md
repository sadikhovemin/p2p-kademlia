## Code Reference for `KBucket` Class

### Introduction

The `KBucket` class is responsible for managing a k-bucket with a defined maximum size. A k-bucket is a list of nodes sorted by their last seen time.

---

### Constructor

#### `KBucket(k_size: int)`

- **Parameters**:
  - `k_size` (int): Maximum size of the k-bucket.

---

### Methods

#### `add(node: Node) -> None`

**Description**: Adds a node to the k-bucket. If the node already exists in the k-bucket, it is moved to the front of the list.

- **Parameters**:
  - `node` (Node): The node to be added to the k-bucket.

---

#### `remove(node: Node) -> None`

**Description**: Removes a node from the k-bucket.

- **Parameters**:
  - `node` (Node): The node to be removed from the k-bucket.

---

#### `visualize_k_buckets() -> None`

**Description**: Visualizes the current state of the k-bucket. This function outputs the Node ID, IP address, and port for each node currently in the k-bucket.

---

