import asyncio
from asyncio import StreamReader, StreamWriter

from pychat.common.stream import SERVER_IP, PORT
from pychat.server.user import User, ClientStream
from pychat.server.rooms import ChatRooms


class PychatServer:
    def __init__(self):
        self.connected: dict[str, User] = {}
        self.rooms = ChatRooms()

        self._server: asyncio.Server|None = None
    
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

    async def _cleanup(self):
        coros = [user.disconnect() for user in self.connected.values()]
        await asyncio.gather(*coros)
        
    async def _handle_user(self, r: StreamReader, w: StreamWriter):
        """Create a new user and start listening for data"""
        user = User(stream=ClientStream(r, w))
        self.connected[user.uid] = user

        # cleanup when done listening
        try:
            await user.stream.listen()
        finally:
            self.purge_user(user.uid)
    
    def purge_user(self, user_id: str):
        """Remove references to the user from the server"""
        del self.connected[user_id]
        self.rooms.purge_user(user_id)
