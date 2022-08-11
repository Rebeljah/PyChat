import asyncio

from pychat.client.client import start_client
from pychat.client.gui.root import GUIRoot


async def main():
    gui = GUIRoot()
    await start_client()
    await gui.closed.wait()


if __name__ == '__main__':
    asyncio.run(main())
