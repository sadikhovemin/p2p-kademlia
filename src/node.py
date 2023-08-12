# import asyncio
#
#
class Node:
    def __init__(self, node_id, ip=None, port=None):
        self.id = node_id
        self.ip = ip
        self.port = port
        print("Node is created with ", ip, " and a port ", port)
# #
# #     async def connect_to_server(self, server_ip, server_port):
# #         reader, writer = await asyncio.open_connection(server_ip, server_port)
# #
# #         # Send a message to the server. For this example, I'm just sending the node's ID.
# #         message = f"Node {self.id} connected\n"
# #         writer.write(message.encode())
# #
# #         # Wait for a response from the server (if any)
# #         data = await reader.read(100)  # read up to 100 bytes
# #         print(f"Received from server: {data.decode()}")
# #
# #         writer.close()
# #         await writer.wait_closed()
# #
# #
# #
# # # Example usage:
# #
# # async def main_node_operation():
# #     node1 = Node("Node1", "127.0.0.1", 7403)
# #     await node1.connect_to_server("127.0.0.1", 7401)
# #
# #
# # if __name__ == "__main__":
# #     asyncio.run(main_node_operation())
#
#
# import asyncio
# from dht_service import Service
# from api_handler import Handler  # assuming the code you provided is in handler.py
#
#
# class Node:
#     def __init__(self, node_id, ip="127.0.0.1", port=7400):
#         self.id = node_id
#         self.ip = ip
#         self.port = port
#         self.server = None
#         self.handler = Handler()  # instantiate your server handler
#
#     async def start_server(self):
#         loop = asyncio.get_event_loop()
#         server_coro = loop.create_server(lambda: self.handler, self.ip, self.port)
#         self.server = await server_coro
#         print(f"{self.id} Server started at {self.ip}:{self.port}")
#         await self.server.serve_forever()
#
#     async def connect_to_peer(self, peer_ip, peer_port):
#         try:
#             reader, writer = await asyncio.open_connection(peer_ip, peer_port)
#             print(f"{self.id} connected to peer at {peer_ip}:{peer_port}")
#
#             # here you can define your protocol to communicate with the peer
#
#             writer.close()
#             await writer.wait_closed()
#         except Exception as e:
#             print(f"{self.id} failed to connect to {peer_ip}:{peer_port}. Reason: {e}")
#
#     async def run_node(self, peer_ips=None, peer_ports=None):
#         tasks = [self.start_server()]
#
#         if peer_ips and peer_ports:
#             for ip, port in zip(peer_ips, peer_ports):
#                 tasks.append(self.connect_to_peer(ip, port))
#
#         await asyncio.gather(*tasks)
#
#
# async def run():
#     node1 = Node("Node1", port=7400)
#     node2 = Node("Node2", port=7401)
#
#     # Here node1 tries to connect to node2, and node2 tries to connect to node1
#     # Normally in a real-world P2P, nodes might be aware of a few peers and would try connecting to them
#     await asyncio.gather(node1.run_node(peer_ips=["127.0.0.1"], peer_ports=[7401]),
#                          node2.run_node(peer_ips=["127.0.0.1"], peer_ports=[7400]))
#
#
if __name__ == "__main__":
    print('salem')
#     asyncio.run(run())
