import asyncio

from gui import GUIRoot
from chat import ChatApp
from common import SERVER_IP, PORT


async def main():
    reader, writer = await asyncio.open_connection(SERVER_IP, PORT)
    app_backend = ChatApp(reader, writer)

    # init gui and begin tkinter loop
    gui = GUIRoot(app_backend)
    await gui.loop()


if __name__ == '__main__':
    asyncio.run(main())
