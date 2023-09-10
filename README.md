# Kademlia DHT
## Description
This project for the Peer-to-Peer-Systems and Security (IN2194) [TUM]  is a Distributed Hash Table (DHT) implementing the Kademlia protocol. It provides a secure and efficient way to perform DHT operations. Written in Python and leveraging the Asyncio library, the system supports multi-client connections and offers robust exception handling.

## Features
- Implements the Kademlia protocol
- Supports DHT operations
- Multi-client connections
- Robust exception handling


## Prerequisites

Ensure that you have the following installed on your system:

- Python 3.11
- [Poetry](https://python-poetry.org/docs/#installation)


## Installation
Open your terminal and run the following command:

```bash
git clone https://github.com/SadikhovEmin/p2p-kademlia.git
```

Navigate to the project directory:
```bash
cd project-name
```

Install the required packages:
```bash
poetry install
```

Open shell:
```bash
poetry shell
```

Usage
Run the server:
```bash
python server.py
```

Run the client:
```bash
python client.py
```

### Tests

To run the test suite, execute:
```bash
pytest test/
```

## Contributors
Emin Sadikhov
Dogan Can Hasanoglu


## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For more details, please refer to the project's [documentation](reports/).
