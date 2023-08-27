import argparse
import asyncio
from api_handler import Handler
from config.config import dht_config
from node import Node
from loguru import logger

logger.add("kademlia.log")


async def main(host, port, bootstrap=False):
    loop = asyncio.get_running_loop()

    my_node = Node(ip=host, port=port)
    handler_instance = Handler(host, port, my_node)

    server = await loop.create_server(lambda: handler_instance, host, port)
    print(f"Node started at {host} : {port}")
    logger.info(f"Node started at {host} : {port}")

    if bootstrap:
        print("buraya girdim")
        # logger.info("buraya girdim")
        my_node.ping = True
        api_address = dht_config["api_address"]

        api_host = api_address.split(":")[0]
        api_port = api_address.split(":")[1]

        pong_msg = await handler_instance.connect_node(api_host, api_port, initiator=True)  # Bootstrap logic
        # print(pong_msg)
        # await handler_instance.process_incoming_data(pong_msg)

    await server.serve_forever()


if __name__ == "__main__":
    api_address = dht_config["api_address"]

    api_host = api_address.split(":")[0]
    api_port = int(api_address.split(":")[1])  # Make sure to convert to integer

    cmd = argparse.ArgumentParser(description="Run a DHT client mockup.")
    cmd.add_argument("-p", "--port", type=int, help="Server port")
    cmd.add_argument("--bootstrap", action="store_true",
                     help="Connect to bootstrap node upon startup")

    args = cmd.parse_args()

    if args.port is not None:
        api_port = args.port

    bootstrap = args.bootstrap

    asyncio.run(main(api_host, api_port, bootstrap=bootstrap))