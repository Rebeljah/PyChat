import asyncio

from pychat.client.rooms import ChatRooms
from pychat.common.stream import DataStream, SERVER_IP, PORT
from pychat.client import events
from pychat.common import request as req
from pychat.common import models


USER = models.User(name='', uid='')


class PychatClient:    
    async def __aenter__(self):
        r, w = await asyncio.open_connection(host=SERVER_IP, port=PORT)
        self.stream: DataStream = DataStream(r, w)
        self.rooms = ChatRooms(self.stream)
        asyncio.create_task(self.stream.listen())
    
    async def __aexit__(self, _, __, ___):
        pass
