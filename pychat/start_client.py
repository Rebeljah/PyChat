import asyncio

from pychat.client.client import PychatClient
from pychat.client.gui.root import GUIRoot


async def main():
    async with PychatClient():
        gui = GUIRoot()
        await gui.closed.wait()


if __name__ == '__main__':
    asyncio.run(main())
