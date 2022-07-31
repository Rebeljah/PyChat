import asyncio

from chat_network import ChatChannels
from common.stream import SERVER_IP, PORT


async def main():
    chat_channels = ChatChannels()

    server = await asyncio.start_server(
        client_connected_cb=chat_channels.handle_client,
        host=SERVER_IP,
        port=PORT
    )

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
