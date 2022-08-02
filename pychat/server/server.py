import asyncio
from asyncio import StreamReader, StreamWriter

from pychat.common.stream import SERVER_IP, PORT
from .user import User, ClientStream
from .rooms import ChatRooms


class PychatServer:
    def __init__(self):
        self.connected: dict[str, User] = {}
        self.rooms = ChatRooms()

        self._server: asyncio.Server|None = None
        self.shutdown = asyncio.Future()
    
    async def serve_forever(self):
        self._server = await asyncio.start_server(
            self._handle_user,
            host=SERVER_IP, port=PORT
        )
        
        async with self._server:
            try:
                await self._server.serve_forever()
            finally:
                coros = [user.disconnect() for user in self.connected.values()]
                asyncio.gather(*coros)
        
    async def _handle_user(self, r: StreamReader, w: StreamWriter):
        user = User(stream=ClientStream(r, w))
        self.connected[user.id] = user

        try:
            await user.stream.listen()
        finally:
            self.purge_user(user.id)
    
    def purge_user(self, user_id: str):
        del self.connected[user_id]
        self.rooms.purge_user(user_id)
