import asyncio

from server_network import ClientInterface
from common import SERVER_IP, PORT


async def main():
    server = await asyncio.start_server(
        client_connected_cb=lambda r, w: ClientInterface(r, w).make_active(),
        host=SERVER_IP,
        port=PORT
    )

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
