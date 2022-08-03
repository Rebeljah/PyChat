import asyncio

from pychat.common.stream import ServerStream, SERVER_IP, PORT


class PychatClient:
    def __init__(self):
        self.stream: ServerStream|None = None
        asyncio.create_task(self.connect())

    async def connect(self):
        r, w = await asyncio.open_connection(host=SERVER_IP, port=PORT)
        self.stream = ServerStream(r, w)

        try:
            await self.stream.listen()
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        pass
