import asyncio
import hashlib
import struct
from loguru import logger
from message_codes import MessageCodes
from node import Node
from config.config import dht_config


class Service:
    """Service class handles incoming DHT messages and performs appropriate actions."""

    def __init__(self, node: Node, callback, put_connection, get_connection, load_ssl_context):
        self.node = node
        self.callback = callback
        self.put_connection = put_connection
        self.get_connection = get_connection
        self.load_ssl_context = load_ssl_context

    async def process_message(self, data):
        """Process incoming data and handle based on request type."""
        try:
            size = struct.unpack(">H", data[:2])[0]
            request_type = struct.unpack(">H", data[2:4])[0]
            logger.info(f"request_type {request_type}")
            if size == len(data):
                if request_type == MessageCodes.DHT_PING.value:
                    return self.pong_service(data[4:])
                elif request_type == MessageCodes.DHT_PONG.value:
                    ip_parts = struct.unpack(">BBBB", data[36:40])
                    ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
                    listening_port = struct.unpack(">H", data[40:42])[0]
                    self.node.add_peer(
                        self.node.generate_node_id(ip_address, listening_port),
                        ip_address,
                        listening_port
                    )
                    ip_parts = list(map(int, self.node.ip.split('.')))
                    return (struct.pack(">HH", 10, MessageCodes.DHT_FIND_NODE.value) +
                            struct.pack(">BBBBH",
                                        ip_parts[0],
                                        ip_parts[1],
                                        ip_parts[2],
                                        ip_parts[3],
                                        self.node.port
                                        )
                            )

                elif request_type == MessageCodes.DHT_PUT.value:
                    return await self.put_service(data)
                elif request_type == MessageCodes.DHT_GET.value:
                    return await self.get_service(data)
                elif request_type == MessageCodes.DHT_FIND_NODE.value:
                    return self.find_node_service(data[4:])
                elif request_type == MessageCodes.DHT_NODE_REPLY.value:
                    nodes_to_connect = self.extract_nodes(data[4:])
                    for n_c in nodes_to_connect:
                        print(n_c)
                        await asyncio.create_task(self.callback(n_c[0], n_c[1], initiator=True))

                    return "running".encode()

                elif request_type == MessageCodes.DHT_FIND_VALUE.value:
                    return await self.handle_find_value_request(data[4:])

                elif request_type == MessageCodes.DHT_SUCCESS.value:
                    return "get works".encode()
                else:
                    logger.warning(f"Invalid request type. Received {request_type}")
                    return False
            else:
                logger.warning("WRONG DATA SIZE")
        except Exception as e:
            logger.error(f"MALFORMED MESSAGE error {e}")

    async def put_service(self, data):
        ttl = int(struct.unpack(">H", data[4:6])[0])
        key = data[8:40]
        value = data[40:]
        replication = int(struct.unpack(">B", data[6:7])[0])
        reserved = int(struct.unpack(">B", data[7:8])[0])

        max_lookup = int(dht_config["max_lookup"])
        if reserved == 0 or reserved > max_lookup:
            reserved = max_lookup

        if reserved == 1:
            self.node.put(key, value, ttl)
            return "put works".encode()

        alpha = int(dht_config["alpha"])
        hashed_key = self.get_hashed_key(key)
        closest_nodes = self.node.get_closest_nodes(hashed_key)[:alpha]
        my_distance = self.node.calculate_distance(hashed_key, self.node.id)

        if len(closest_nodes) == 0:
            self.node.put(key, value, ttl)
            return "put works".encode()

        # Replication. In case I'm closer to key than one of nodes from alpha closest,
        # I can store value on myself as well
        flag = False
        for c_n in closest_nodes:
            local_distance = self.node.calculate_distance(c_n.id, hashed_key)
            if local_distance > my_distance:
                flag = True

        if flag:
            self.node.put(key, value, ttl)

        next_nodes_to_query = self.node.get_closest_nodes(hashed_key)[alpha:]
        index = 0

        reserved -= 1
        msg = None
        for node in closest_nodes:
            size = 8 + len(key) + len(value)
            msg = struct.pack(">HHHBB",
                              size,
                              MessageCodes.DHT_PUT.value,
                              ttl,
                              replication,
                              reserved) + key + value

            try:
                await asyncio.create_task(self.put_connection(node.ip, node.port, msg))
            except Exception:
                logger.error(f"Cannot connect to {node.ip}, {node.port}")
                if index < len(next_nodes_to_query):
                    closest_nodes.append(next_nodes_to_query[index])
                    logger.info(f"index {index}")
                    index += 1
        return msg

    async def get_service(self, data):
        key = data[4:]
        value = self.node.get(key)
        if value is not None:
            size = 4 + len(key) + len(value)
            msg = struct.pack(">HH", size, MessageCodes.DHT_SUCCESS.value) + key + value
            return msg
        else:
            # Start the iterative search
            logger.info("starting to search")
            result = await self.iterative_find_value(key)

            try:
                request_type = struct.unpack(">H", result[2:4])[0]
                if request_type == MessageCodes.DHT_FAILURE.value:
                    return result
            except Exception as e:
                logger.error(f"error occurred {e}")

            if result is not None:
                # Construct response with the found value
                size = 4 + len(key) + len(result)
                msg = struct.pack(">HH", size, MessageCodes.DHT_SUCCESS.value) + key + result
                return msg
            else:
                logger.warning("Value not found")
                return "Value not found".encode()

    async def iterative_find_value(self, key):
        hashed_key = self.get_hashed_key(key)
        alpha = int(dht_config["alpha"])
        closest_nodes = self.node.get_closest_nodes(hashed_key)[:alpha]
        closest_nodes = closest_nodes[::-1]
        logger.info(f"closest nodes {closest_nodes}")
        next_nodes_to_query = self.node.get_closest_nodes(hashed_key)[alpha:]
        index = 0
        queried_nodes = set()
        queried_nodes.add((self.node.ip, self.node.port))

        nodes_to_query = asyncio.LifoQueue()
        for node in closest_nodes:
            await nodes_to_query.put(node)

        while not nodes_to_query.empty():
            node = await nodes_to_query.get()
            if (node.ip, node.port) in queried_nodes:
                continue  # skip nodes that have already been queried

            queried_nodes.add((node.ip, node.port))
            response = await self.query_node_for_value(node, key)

            # Handling for case some of the peer fails/leaves
            if 'error' in response:
                if node in closest_nodes:
                    temp_stack = []

                    while not nodes_to_query.empty():
                        temp_stack.append(await nodes_to_query.get())

                    if index < len(next_nodes_to_query):
                        await nodes_to_query.put(next_nodes_to_query[index])
                        index += 1

                    while temp_stack:
                        await nodes_to_query.put(temp_stack.pop())

                continue

            if 'value' in response:
                logger.info(f"returning value from iterative_find_value {response['value']}")
                return response['value']

            new_closest_nodes = response.get('closest_nodes', [])
            new_closest_nodes = new_closest_nodes[::-1]  # reverse
            for new_node in new_closest_nodes:
                await nodes_to_query.put(new_node)

        size = 4 + len(key)
        msg = struct.pack(">HH", size, MessageCodes.DHT_FAILURE.value) + key
        return msg  # Value not found

    async def query_node_for_value(self, node, key):
        # Send a find_value request to the given node
        size = 4 + len(key)
        msg = struct.pack(">HH", size, MessageCodes.DHT_FIND_VALUE.value) + key

        try:
            ssl_context = self.load_ssl_context(node.ip, node.port)
            reader, writer = await asyncio.open_connection(node.ip, node.port, ssl=ssl_context)
            writer.write(msg)
            await writer.drain()

            # Read the response
            data = await reader.read(1000)  # Adjust the byte count as necessary

            # Close the connection
            writer.close()
            await writer.wait_closed()

            request_type = struct.unpack(">H", data[2:4])[0]

            if request_type == MessageCodes.DHT_SUCCESS.value:
                value = data[36:]  # Adjust as per actual format
                return {"value": value}
            elif request_type == MessageCodes.DHT_NODE_REPLY.value:
                nodes_list = self.extract_nodes_found_peers(data[4:])
                return {"closest_nodes": nodes_list}
            else:
                # Handle other response types or errors as needed
                logger.error("Invalid response type or error in communication")
                return {"error": "Invalid response type or error in communication"}
        except Exception as e:
            logger.error(f"Error occurred while connecting to {node.ip}, {node.port}")
            return {"error": "Invalid response type or error in communication"}

    async def handle_find_value_request(self, key):
        # Check if this node holds the value for the given key
        value = self.node.get(key)

        if value:
            # Return the value if it exists
            response = struct.pack(">HH",
                                   len(key) + len(value) + 4,
                                   MessageCodes.DHT_SUCCESS.value
                                   ) + key + value
            return response

        else:
            # If the node doesn't have the value, find the k closest nodes to the key
            hashed_key = self.get_hashed_key(key)
            alpha = int(dht_config["alpha"])
            closest_nodes = self.node.get_closest_nodes(hashed_key)[:alpha]
            header = struct.pack(">HHH",
                                 6 + len(closest_nodes) * 6,
                                 MessageCodes.DHT_NODE_REPLY.value,
                                 len(closest_nodes)
                                 )
            packed_nodes = b''
            for n in closest_nodes:
                # pack each node
                ip_parts = [int(part) for part in n.ip.split('.')]
                node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], n.port)
                packed_nodes += node_data

            # combine header and nodes
            node_reply = header + packed_nodes

            return node_reply

    def ping_service(self):
        unique_str = f"{self.node.ip}:{self.node.port}"
        ip_parts = list(map(int, self.node.ip.split('.')))
        message = (struct.pack(">HH", 42, MessageCodes.DHT_PING.value) +
                   hashlib.sha256(unique_str.encode()).digest() +
                   struct.pack(">BBBBH",
                               ip_parts[0],
                               ip_parts[1],
                               ip_parts[2],
                               ip_parts[3],
                               self.node.port)
                   )
        return message

    def pong_service(self, data):
        node_id = data[0:32]
        integer_representation = int.from_bytes(node_id, 'big')
        ip_parts = struct.unpack(">BBBB", data[32:36])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        listening_port = struct.unpack(">H", data[36:38])[0]

        self.node.add_peer(integer_representation, ip_address, listening_port)
        ip_parts = list(map(int, self.node.ip.split('.')))

        return (struct.pack(">HH", 42, MessageCodes.DHT_PONG.value) +
                node_id +
                struct.pack(">BBBBH",
                            ip_parts[0],
                            ip_parts[1],
                            ip_parts[2],
                            ip_parts[3],
                            self.node.port
                            )
                )

    def find_node_service(self, data):
        """Processes the received data and returns a reply with closest nodes."""
        ip_parts = struct.unpack(">BBBB", data[0:4])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        port = struct.unpack(">H", data[4:6])[0]

        node_id = self.node.generate_node_id(ip_address, port)
        closest_nodes = self.node.get_closest_nodes(node_id)

        closest_nodes = self.filter_nodes(closest_nodes, node_id)

        header = struct.pack(">HHH",
                             6 + len(closest_nodes) * 6,
                             MessageCodes.DHT_NODE_REPLY.value,
                             len(closest_nodes)
                             )
        packed_nodes = b''
        for n in closest_nodes:
            # pack each node
            ip_parts = [int(part) for part in n.ip.split('.')]
            node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], n.port)
            packed_nodes += node_data

        # combine header and nodes
        node_reply = header + packed_nodes
        return node_reply

    async def check_liveness(self, ip, port, timeout=3):
        """
        Check if a node is alive by attempting to establish a connection.

        :param ip: IP address of the node.
        :param port: Port number of the node.
        :param timeout: Time to wait before considering the node unreachable.
        :return: True if the node is alive, False otherwise.
        """
        logger.info(f"Checking liveness for {ip}:{port}")
        try:
            ssl_context = self.load_ssl_context(ip, port)
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=ssl_context),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False

    async def check_all_liveness(self):
        """ Check the liveness of all peers in the k-buckets and remove any that are not alive. """
        peers_on_buckets = self.node.get_all_peers()  # assuming this returns a list of (ip, port) tuples
        liveness_checks = [self.check_liveness(ip, port) for ip, port in peers_on_buckets]
        results = await asyncio.gather(*liveness_checks)

        for (ip, port), is_alive in zip(peers_on_buckets, results):
            if not is_alive:
                self.node.remove_peer(ip, port)

    async def periodic_liveness_check(self, interval=10):
        """
        Periodically check the liveness of all peers in the k-buckets.

        :param interval: Time interval (in seconds) between consecutive checks.
        """
        while True:
            await self.check_all_liveness()
            await asyncio.sleep(interval)

    def extract_nodes(self, data):
        """
        Extract nodes from the given binary data.

        :param data: Binary data representing nodes.
        :return: List of nodes extracted from the data.
        """
        num_nodes = struct.unpack(">H", data[:2])[0]
        nodes_to_connect = []
        offset = 2

        # Iterate and extract each node's IP and port
        for _ in range(num_nodes):
            ip_parts = struct.unpack(">BBBB", data[offset:offset + 4])
            ip_address = ".".join(map(str, ip_parts))
            port = struct.unpack(">H", data[offset + 4:offset + 6])[0]
            nodes_to_connect.append((ip_address, port))
            offset += 6

        nodes_to_connect = self.filter_nodes_1(nodes_to_connect)
        return nodes_to_connect

    @staticmethod
    def extract_nodes_found_peers(data):
        """
        Extract nodes from the given binary data.

        :param data: Binary data representing nodes.
        :return: List of nodes extracted from the data.
        """
        num_nodes = struct.unpack(">H", data[:2])[0]
        nodes_to_connect = []
        offset = 2

        # Iterate and extract each node's IP and port
        for _ in range(num_nodes):
            # Extract IP
            ip_parts = struct.unpack(">BBBB", data[offset:offset + 4])
            ip_address = ".".join(map(str, ip_parts))

            # Extract Port
            port = struct.unpack(">H", data[offset + 4:offset + 6])[0]

            # Append to nodes_to_connect list
            nodes_to_connect.append(Node(ip=ip_address, port=port))

            # Move to next node's data
            offset += 6

        return nodes_to_connect

    def filter_nodes(self, closest_nodes, node_id):
        """
        Filter out nodes based on their ID and whether they're already in the k-buckets.

        :param closest_nodes: List of nodes to filter.
        :param node_id: Node ID to exclude.
        :return: Filtered list of nodes.
        """
        return [node for node in closest_nodes if node.id != node_id and node not in self.node.k_buckets]

    def filter_nodes_1(self, nodes):
        """
        Filter out nodes that are already present in the k-buckets.

        :param nodes: List of nodes to filter.
        :return: Filtered list of nodes.
        """
        # Create a set of nodes from k-buckets for efficient look-up
        k_bucket_nodes = {(node.ip, node.port) for bucket in self.node.k_buckets for node in bucket.nodes}

        # Filter out nodes present in the set
        return [n for n in nodes if n not in k_bucket_nodes]

    @staticmethod
    def get_hashed_key(key):
        """
        Computes the SHA-256 hash of the key.

        :param key: Key to be hashed.
        :return: Hashed key value.
        """
        return int(hashlib.sha256(key).hexdigest(), 16)
