import asyncio

from backend import ChatApp
from common import SERVER_IP, PORT


async def main():
    reader, writer = await asyncio.open_connection(SERVER_IP, PORT)
    backend = ChatApp(reader, writer)

    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
