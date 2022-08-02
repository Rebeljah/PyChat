from pychat.common.stream import ClientStream
from pychat.common.identity import make_id


class User:
    def __init__(self, stream: ClientStream):
        self.id = make_id()
        self.stream = stream

    async def disconnect(self):
        await self.stream.close_connection()
