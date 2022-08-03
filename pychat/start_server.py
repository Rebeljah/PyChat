import asyncio

from pychat.server.server import PychatServer


async def main():
    await PychatServer().serve_forever()


if __name__ == '__main__':
    asyncio.run(main())