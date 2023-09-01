import argparse
import asyncio
import os
import ssl

from api_handler import Handler
from config.config import dht_config
from node import Node
from loguru import logger

logger.add("kademlia.log")


async def _start_api_server(host: str, port: str, node: Node):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: Handler(host, port, node), host, int(port))
    logger.info(f"API Server started: {host}:{port}")
    return server


async def main(host, port, bootstrap=False, use_ssl=False):
    loop = asyncio.get_running_loop()

    my_node = Node(ip=host, port=port)

    handler_instance = Handler(host, port, my_node)

    # SSL Configuration
    ssl_context = None
    if use_ssl:
        # ssl_context = handler_instance.load_ssl_context(host, port)
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=f"../certificates/{host}_{port}/{host}_{port}.crt",
                                    keyfile=f"../certificates/{host}_{port}/{host}_{port}.key")
        ssl_context.load_verify_locations(cafile="../certificates/CA/ca.pem")
        ssl_context.verify_mode = ssl.CERT_REQUIRED

    server = await loop.create_server(lambda: handler_instance, host, port, ssl=ssl_context)

    print(f"Node started at {host} : {port}")
    logger.info(f"Node started at {host} : {port}")

    handler_instance.start_periodic_check()

    if bootstrap:
        logger.info("buraya girdim")
        my_node.ping = True
        api_address = dht_config["listen_address"]

        api_host = api_address.split(":")[0]
        api_port = api_address.split(":")[1]

        try:
            logger.info("Trying to connect to a bootstrap node")
            await handler_instance.connect_node(api_host, api_port, initiator=True)  # Bootstrap logic
        except Exception as e:
            logger.error(f"Cannot connect to the bootstrap node {e}")

    # await server.serve_forever()

    api_address = dht_config["api_address"]
    api_host = api_address.split(":")[0]
    api_port = port + 1000
    api_server = await _start_api_server(api_host, str(api_port), my_node)
    async with api_server, server:
        return await asyncio.gather(
            api_server.serve_forever(),
            server.serve_forever(),
        )



if __name__ == "__main__":
    api_address = dht_config["listen_address"]

    api_host = api_address.split(":")[0]
    api_port = int(api_address.split(":")[1])  # Make sure to convert to integer

    cmd = argparse.ArgumentParser(description="Run a DHT client mockup.")
    cmd.add_argument("-p", "--port", type=int, help="Server port")
    cmd.add_argument("--bootstrap", action="store_true",
                     help="Connect to bootstrap node upon startup")
    cmd.add_argument("--ssl", action="store_true", help="Enable SSL/TLS")

    args = cmd.parse_args()

    if args.port is not None:
        api_port = args.port

    bootstrap = args.bootstrap


    asyncio.run(main(api_host, api_port, bootstrap=bootstrap, use_ssl=args.ssl))
