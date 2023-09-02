import asyncio
import hashlib
import struct

from message_codes import MessageCodes
from node import Node
from config.config import dht_config
from loguru import logger


class Service:
    def __init__(self, node: Node, callback, put_connection, get_connection, load_ssl_context):
        self.node = node
        self.callback = callback
        self.put_connection = put_connection
        self.get_connection = get_connection
        self.load_ssl_context = load_ssl_context

    async def process_message(self, data):
        try:
            size = struct.unpack(">H", data[:2])[0]
            request_type = struct.unpack(">H", data[2:4])[0]
            logger.info(f"request_type {request_type}")
            logger.info(f"size {size}")
            logger.info(len(data))
            if size == len(data):
                if request_type == MessageCodes.DHT_PING.value:
                    logger.info("PING ALDIM")
                    return self.pong_service(data[4:])
                elif request_type == MessageCodes.DHT_PONG.value:
                    logger.info("PONG ALDIM")
                    print(data)
                    ip_parts = struct.unpack(">BBBB", data[36:40])
                    ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
                    listening_port = struct.unpack(">H", data[40:42])[0]
                    self.node.add_peer(self.node.generate_node_id(ip_address, listening_port), ip_address,
                                       listening_port)
                    logger.info(f"adding peer with {ip_address}, {listening_port}", )
                    ip_parts = list(map(int, self.node.ip.split('.')))
                    return (struct.pack(">HH", 10, MessageCodes.DHT_FIND_NODE.value) +
                            struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))

                elif request_type == MessageCodes.DHT_PUT.value:
                    logger.info("DHT PUT geldim")
                    return await self.put_service(data)
                elif request_type == MessageCodes.DHT_GET.value:
                    logger.info("DHT GET geldim")
                    return await self.get_service(data)
                elif request_type == MessageCodes.DHT_FIND_NODE.value:
                    logger.info("find_node geldim")
                    return self.find_node_service(data[4:])
                elif request_type == MessageCodes.DHT_NODE_REPLY.value:
                    logger.info("node reply geldim")
                    nodes_to_connect = self.extract_nodes(data[4:])
                    logger.info("below printing nodes to connect")
                    for n_c in nodes_to_connect:
                        print(n_c)
                        await asyncio.create_task(self.callback(n_c[0], n_c[1], initiator=True))

                    return "ok".encode()

                elif request_type == MessageCodes.DHT_FIND_VALUE.value:
                    logger.info("find_value geldim")
                    return await self.handle_find_value_request(data[4:])

                elif request_type == MessageCodes.DHT_SUCCESS.value:
                    logger.info("received success")
                    return "get calisti".encode()
                else:
                    logger.warning(f"Invalid request type. Received {request_type}")
                    return False
            else:
                logger.warning("WRONG DATA SIZE")
        except Exception as e:
            logger.error(f"MALFORMED MESSAGE error {e}")

    async def put_service(self, data):
        logger.info("put_service called")
        ttl = int(struct.unpack(">H", data[4:6])[0])
        key = data[8:40]
        value = data[40:]
        replication = int(struct.unpack(">B", data[6:7])[0])
        reserved = int(struct.unpack(">B", data[7:8])[0])
        logger.info(f"reserved {reserved}")
        logger.info(f"key {key}")
        logger.info(f"value {value}")

        max_lookup = int(dht_config["max_lookup"])
        if reserved == 0 or reserved > max_lookup:
            reserved = max_lookup

        if reserved == 1:
            self.node.put(key, value, ttl)
            return "put calisti".encode()

        alpha = int(dht_config["alpha"])
        hashed_key = self.get_hashed_key(key)
        closest_nodes = self.node.get_closest_nodes(hashed_key)[:alpha]
        my_distance = self.node.calculate_distance(hashed_key, self.node.id)

        if len(closest_nodes) == 0:
            self.node.put(key, value, ttl)
            return "put calisti".encode()

        '''
        Replication
        In case I'm closer to key than one of nodes from alpha closest, I can store value on myself as well
        '''
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
            logger.info(f"target_node {node}")
            size = 8 + len(key) + len(value)
            msg = struct.pack(">HHHBB", size, MessageCodes.DHT_PUT.value, ttl, replication, reserved) + key + value

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
        logger.info(f"dht_key {key}")
        value = self.node.get(key)
        logger.info(f"retrieved value {value}")
        if value is not None:
            size = 4 + len(key) + len(value)
            msg = struct.pack(">HH", size, MessageCodes.DHT_SUCCESS.value) + key + value
            logger.info("returning msg")
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
                logger.warning("result = none -- inside get_service else clause")
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
            logger.info(f"nodes to query {nodes_to_query}")

            logger.info(f"queue size {nodes_to_query.qsize()}")
            print("node = await nodes_to_query.get() - ", node)
            print("queried_nodes", queried_nodes)
            if (node.ip, node.port) in queried_nodes:
                continue  # skip nodes that have already been queried

            logger.info("on line 234")
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
            print("new_closest_nodes", new_closest_nodes)
            for new_node in new_closest_nodes:
                logger.info("iterative_find_value new_node in new_closest_nodes")
                await nodes_to_query.put(new_node)

        size = 4 + len(key)
        msg = struct.pack(">HH", size, MessageCodes.DHT_FAILURE.value) + key
        return msg  # Value not found

    async def query_node_for_value(self, node, key):
        # Send a find_value request to the given node
        logger.info(f"trying to query node {node.ip}, {node.port}")
        size = 4 + len(key)
        msg = struct.pack(">HH", size, MessageCodes.DHT_FIND_VALUE.value) + key

        try:
            ssl_context = self.load_ssl_context(node.ip, node.port)
            reader, writer = await asyncio.open_connection(node.ip, node.port, ssl=ssl_context)
            # Send the message
            writer.write(msg)
            await writer.drain()

            # Read the response
            logger.info("reading before reader")
            data = await reader.read(1000)  # Adjust the byte count as necessary

            # Close the connection
            writer.close()
            await writer.wait_closed()

            request_type = struct.unpack(">H", data[2:4])[0]
            logger.info("reading after reader")

            if request_type == MessageCodes.DHT_SUCCESS.value:
                value = data[36:]  # Adjust as per actual format
                logger.info("return value from query_node_for_value")
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
        logger.info("handle_find_value_request geldim")
        value = self.node.get(
            key)  # Assuming this function retrieves the value for the given key from the node's local store

        if value:
            # Return the value if it exists
            response = struct.pack(">HH", len(key) + len(value) + 4, MessageCodes.DHT_SUCCESS.value) + key + value
            return response

        else:
            logger.info("handle_find_value_request else clause girdim")
            # If the node doesn't have the value, find the k closest nodes to the key
            hashed_key = self.get_hashed_key(key)
            alpha = int(dht_config["alpha"])
            closest_nodes = self.node.get_closest_nodes(hashed_key)[:alpha]
            print("handle_find_value_request else clause success entry")
            # logger.info("handle_find_value_request else clause success entry")
            header = struct.pack(">HHH", 6 + len(closest_nodes) * 6, MessageCodes.DHT_NODE_REPLY.value,
                                 len(closest_nodes))
            packed_nodes = b''
            for n in closest_nodes:
                print("inner node", n)
                # logger.info(f"inner node {n}")
                # pack each node
                ip_parts = [int(part) for part in n.ip.split('.')]

                node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], n.port)
                packed_nodes += node_data

            # combine header and nodes
            node_reply = header + packed_nodes
            print("local size", struct.unpack(">H", node_reply[:2])[0])
            print("handle_find_value_request else clause success exit")

            return node_reply

    def ping_service(self):
        unique_str = f"{self.node.ip}:{self.node.port}"
        ip_parts = list(map(int, self.node.ip.split('.')))
        message = (struct.pack(">HH", 42, MessageCodes.DHT_PING.value) +
                   hashlib.sha256(unique_str.encode()).digest() +
                   struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))
        print("sending ping message")
        return message

    def pong_service(self, data):
        node_id = data[0:32]
        integer_representation = int.from_bytes(node_id, 'big')
        print(integer_representation)
        ip_parts = struct.unpack(">BBBB", data[32:36])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        listening_port = struct.unpack(">H", data[36:38])[0]

        print(ip_address, listening_port)
        self.node.add_peer(integer_representation, ip_address, listening_port)
        ip_parts = list(map(int, self.node.ip.split('.')))

        return (struct.pack(">HH", 42, MessageCodes.DHT_PONG.value) +
                node_id +
                struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], self.node.port))

    def find_node_service(self, data):
        print("find_node_service called")
        ip_parts = struct.unpack(">BBBB", data[0:4])
        ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
        port = struct.unpack(">H", data[4:6])[0]
        print(ip_address, port)

        node_id = self.node.generate_node_id(ip_address, port)
        closest_nodes = self.node.get_closest_nodes(node_id)

        closest_nodes = self.filter_nodes(closest_nodes, node_id)
        """
        2 - size
        2 - message type
        2 - number of nodes
        len(closest_nodes) * 6 (ip, port) - Nodes
        """
        header = struct.pack(">HHH", 6 + len(closest_nodes) * 6, MessageCodes.DHT_NODE_REPLY.value, len(closest_nodes))
        packed_nodes = b''
        for n in closest_nodes:
            print("inner node", n)
            # pack each node
            ip_parts = [int(part) for part in n.ip.split('.')]
            # packed_ip = struct.pack(">BBBB", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3])

            node_data = struct.pack(">BBBBH", ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3], n.port)
            packed_nodes += node_data

        # combine header and nodes
        node_reply = header + packed_nodes
        print("local size", struct.unpack(">H", node_reply[:2])[0])
        return node_reply

    async def check_liveness(self, ip, port, timeout=3):
        """
        Attempt to establish a connection to the given IP and port.
        If successful, close the connection and return True, otherwise return False.
        """
        logger.info(f"Checking liveness for {ip}, {port} peers")
        try:
            ssl_context = self.load_ssl_context(ip, port)
            _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port, ssl=ssl_context), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False

    async def check_all_liveness(self):
        """
        Check the liveness of all peers in the k-buckets.
        """
        peers_on_buckets = self.node.get_all_peers()  # assuming this returns a list of (ip, port) tuples
        liveness_checks = [self.check_liveness(ip, port) for ip, port in peers_on_buckets]
        results = await asyncio.gather(*liveness_checks)

        for (ip, port), is_alive in zip(peers_on_buckets, results):
            if not is_alive:
                self.node.remove_peer(ip, port)

    async def periodic_liveness_check(self, interval=10):
        checked = set()
        while True:
            await self.check_all_liveness()
            checked.clear()  # clear after each full round of checks
            await asyncio.sleep(interval)

    def extract_nodes(self, data):
        num_nodes = struct.unpack(">H", data[:2])[0]
        print("num_nodes", num_nodes)
        nodes_to_connect = []
        prev, next = 2, 8

        for i in range(num_nodes):
            ip_parts = struct.unpack(">BBBB", data[prev:(next - 2)])
            ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
            port = struct.unpack(">H", data[(next - 2):next])[0]
            print("ip_address", ip_address)
            print("port", port)
            prev = next
            next += 6
            nodes_to_connect.append((ip_address, port))

        nodes_to_connect = self.filter_nodes_1(nodes_to_connect)

        return nodes_to_connect

    def extract_nodes_found_peers(self, data):
        num_nodes = struct.unpack(">H", data[:2])[0]
        print("num_nodes", num_nodes)
        nodes_to_connect = []
        prev, next = 2, 8

        for i in range(num_nodes):
            ip_parts = struct.unpack(">BBBB", data[prev:(next - 2)])
            ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
            port = struct.unpack(">H", data[(next - 2):next])[0]
            print("ip_address", ip_address)
            print("port", port)
            prev = next
            next += 6
            nodes_to_connect.append(
                Node(
                    ip=ip_address,
                    port=port
                )
            )

        return nodes_to_connect

    def filter_nodes(self, closest_nodes, node_id):
        print("to remove", node_id)
        return [node for node in closest_nodes if node.id != node_id and node not in self.node.k_buckets]

    def filter_nodes_1(self, nodes):
        print("my k bucket")

        k_bucket_nodes = set()

        for bucket in self.node.k_buckets:
            for node in bucket.nodes:
                k_bucket_nodes.add((node.ip, node.port))
                print(node)

        # Use a list comprehension to filter out any nodes that are in the k_bucket_nodes set
        # filtered_nodes = [node for node in nodes if node not in k_bucket_nodes]
        filtered_nodes = []
        for n in nodes:
            if n not in k_bucket_nodes:
                filtered_nodes.append(n)

        return filtered_nodes

    @staticmethod
    def get_hashed_key(key):
        return int(hashlib.sha256(key).hexdigest(), 16)
