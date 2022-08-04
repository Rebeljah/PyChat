import asyncio

from pychat.server.server import PychatServer


async def main():
    await PychatServer().run()


if __name__ == '__main__':
    asyncio.run(main())
