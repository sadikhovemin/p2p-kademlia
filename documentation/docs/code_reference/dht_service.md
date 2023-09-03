# Service Class

---

## Table of Contents

- [Constructor](#constructor)
- [Methods](#methods)
  - [process_message](#process_message)
  - [put_service](#put_service)
  - [get_service](#get_service)
  - [iterative_find_value](#iterative_find_value)
  - [query_node_for_value](#query_node_for_value)
  - [handle_find_value_request](#handle_find_value_request)
  - [ping_service](#ping_service)
  - [pong_service](#pong_service)
  - [find_node_service](#find_node_service)
  - [check_liveness](#check_liveness)
  - [check_all_liveness](#check_all_liveness)
  - [periodic_liveness_check](#periodic_liveness_check)
  - [extract_nodes](#extract_nodes)
  - [extract_nodes_found_peers](#extract_nodes_found_peers)
  - [filter_nodes](#filter_nodes)
  - [filter_nodes_tuple](#filter_nodes_1)
  - [get_hashed_key](#get_hashed_key)

---

## Constructor

\`\`\`python
def __init__(self, node: Node, callback, put_connection, get_connection, load_ssl_context):
\`\`\`

**Parameters:**

- **node (Node):** The node instance associated with the service.
- **callback:** A callback function.
- **put_connection:** A function to establish a put connection.
- **get_connection:** A function to establish a get connection.
- **load_ssl_context:** A function to load the SSL context.

---

## Methods

### process_message

```bash
async def process_message(self, data):
```

**Parameters:**

- **data:** Incoming data.

---

### put_service


```bash
async def put_service(self, data):
```

**Parameters:**

- **data:** Incoming data.

---

### get_service

```bash
async def get_service(self, data):
```

**Parameters:**

- **data:** Incoming data.

---

### iterative_find_value

```bash
async def iterative_find_value(self, key):
```

**Parameters:**

- **key:** The key to find.

---

### query_node_for_value

```bash
async def query_node_for_value(self, node, key):
```

**Parameters:**

- **node:** The node to query.
- **key:** The key to find.

---

### handle_find_value_request

```bash
async def handle_find_value_request(self, key):
```

**Parameters:**

- **key:** The key to find.

---

### ping_service

```bash
def ping_service(self):
```

---

### pong_service

```bash
def pong_service(self, data):
```

**Parameters:**

- **data:** Incoming data.

---

### find_node_service

```bash
def find_node_service(self, data):
```

**Parameters:**

- **data:** Incoming data.

---

### check_liveness

```bash
async def check_liveness(self, ip, port, timeout=3):
```

**Parameters:**

- **ip:** IP address of the node.
- **port:** Port number of the node.
- **timeout (default 3):** Time to wait before considering the node unreachable.

---

### check_all_liveness

```bash
async def check_all_liveness(self):
```

---

### periodic_liveness_check

```bash
async def periodic_liveness_check(self, interval=10):
```

**Parameters:**

- **interval (default 10):** Time interval (in seconds) between consecutive checks.

---

### extract_nodes

```bash
def extract_nodes(self, data):
```

**Parameters:**

- **data:** Binary data representing nodes.

---

### extract_nodes_found_peers

```bash
def extract_nodes_found_peers(self, data):
```

**Parameters:**

- **data:** Binary data representing nodes.

---

### filter_nodes

```bash
def filter_nodes(self, closest_nodes, node_id):
```

**Parameters:**

- **closest_nodes:** List of nodes to filter.
- **node_id:** Node ID to exclude.

---

### filter_nodes_tuple

```bash
def filter_nodes_1(self, nodes):
```

**Parameters:**

- **nodes:** List of nodes to filter.

---

### get_hashed_key

```bash
def get_hashed_key(self, key):
```

**Parameters:**

- **key:** Key to be hashed.

---
