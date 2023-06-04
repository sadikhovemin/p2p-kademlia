import asyncio
from api import Api
from config.config import dht_config


async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(Api, host, port)
    await server.serve_forever()


if __name__ == "__main__":
    api_address = dht_config["api_address"]

    api_host = api_address.split(":")[0]
    api_port = api_address.split(":")[1]

    asyncio.run(main(api_host, api_port))
