import argparse
import asyncio
from api_handler import Handler
from config.config import dht_config
from node import Node


async def main(host, port, bootstrap=False):
    loop = asyncio.get_running_loop()

    my_node = Node(ip=host, port=port)
    # dht_service = Service()
    handler_instance = Handler(host, port, my_node)

    server = await loop.create_server(lambda: handler_instance, host, port)
    print(f"Node started at {host} : {port}")

    if bootstrap:
        api_address = dht_config["api_address"]

        api_host = api_address.split(":")[0]
        api_port = api_address.split(":")[1]

        pong_msg = await handler_instance.send_ping(api_host, api_port)  # Bootstrap logic
        print(pong_msg)
        await handler_instance.process_incoming_data(pong_msg)

        # handler_instance.transport.write(ping_msg)

        # Now you can safely send the ping message
        # handler_instance.transport.write(ping_msg)


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