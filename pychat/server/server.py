import asyncio
from asyncio import StreamReader, StreamWriter

from pychat.common import request as req
from pychat.common.stream import SERVER_IP, PORT, DataStream
from pychat.server.rooms import ChatRooms
from pychat.server import users


class PychatServer:
    def __init__(self):
        self._server: asyncio.Server|None = None
        self.rooms = ChatRooms()
        self.users: set[users.User] = set()
    
    async def run(self):
        """Start accepting connection and cleanup when done"""
        self._server = await asyncio.start_server(
            self._handle_user,
            host=SERVER_IP, port=PORT
        )

        # start serving then cleanup
        async with self._server:
            try:
                await self._server.serve_forever()
            finally:
                await self._cleanup()

    async def _handle_user(self, r: StreamReader, w: StreamWriter):
        """Create a new user and start listening for data"""
        user = users.User(DataStream(r, w))
        self.users.add(user)

        self.rooms.register_user(user)

        try:
            await user.listen()
        finally:
            self.rooms.purge_user(user)
            self.users.remove(user)

    async def _cleanup(self):
        coros = [user.cleanup() for user in self.users]
        await asyncio.gather(*coros)
