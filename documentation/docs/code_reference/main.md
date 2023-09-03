## Code Reference for `main.py`

### Introduction

The `main.py` file is the entry point for the Kademlia DHT project. It handles the initialization of nodes, SSL configuration, API server setup, and command-line argument parsing.

---

### Functions

#### `_start_api_server(host: str, port: str, node: Node) -> None`

This asynchronous function sets up and starts the API server.

- **Parameters**:
  - `host` (str): The host address for the API server.
  - `port` (str): The port for the API server.
  - `node` (Node): Instance of the Node class that the API server will interact with.

#### `main(host, port, bootstrap=False) -> None`

This asynchronous function is the primary execution loop for the DHT node. It initializes a node, starts it, and connects it to the network.

- **Parameters**:
  - `host` (str): The host address for the Node.
  - `port` (str): The port for the Node.
  - `bootstrap` (bool, optional): Whether or not to connect to a bootstrap node upon startup.

#### Command-line Arguments

The following command-line arguments are supported:

- `-a` or `--address` (str): Specifies the server IP address.
- `-p` or `--port` (int): Specifies the server port.
- `--bootstrap`: Flag to connect to the bootstrap node upon startup.

---

### Sample Code to Run Node

To start the node, use the following command:

```bash
python3 main.py -a 127.0.0.1 -p 6501 --bootstrap
```


### SSL Configuration
SSL is configured using the following files:

- Server certificate: ../certificates/{host}_{port}/{host}_{port}.crt
- Server private key: ../certificates/{host}_{port}/{host}_{port}.key
- CA certificate: ../certificates/CA/ca.pem