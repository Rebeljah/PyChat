import asyncio

from gui import GUIRoot
from chat import ChatApp
from common import SERVER_IP, PORT


async def main():
    reader, writer = await asyncio.open_connection(SERVER_IP, PORT)
    ChatApp(reader, writer)
    await GUIRoot().loop()


if __name__ == '__main__':
    asyncio.run(main())
