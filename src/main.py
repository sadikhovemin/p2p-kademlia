import argparse
import asyncio
from api_handler import Handler
from config.config import dht_config


async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: Handler(host, port), host, port)

    print(f"Server started at {host} : {port}")
    await server.serve_forever()


if __name__ == "__main__":
    api_address = dht_config["api_address"]

    api_host = api_address.split(":")[0]
    api_port = api_address.split(":")[1]

    #######################
    bootstrap = False
    usage_string = ("Run a DHT client mockup.\n\n")
    cmd = argparse.ArgumentParser(description=usage_string)
    cmd.add_argument("-p", "--port",
                     help="Server port")
    args = cmd.parse_args()
    if args.port is not None:
        api_port = int(args.port)

    #######################
    asyncio.run(main(api_host, api_port))
