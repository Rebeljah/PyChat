import asyncio

from pychat.client.rooms import ChatRooms
from pychat.common.stream import DataStream, SERVER_IP, PORT
from pychat.common import models


USER = models.User(name='', uid='')


async def start_client():
    r, w = await asyncio.open_connection(host=SERVER_IP, port=PORT)
    stream: DataStream = DataStream(r, w)
    rooms = ChatRooms(stream)
    asyncio.create_task(stream.listen())
