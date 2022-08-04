from pychat.common.stream import ClientStream
from pychat.common.identity import make_uid


class User:
    def __init__(self, stream: ClientStream):
        self.uid = make_uid()
        self.stream = stream

    async def disconnect(self):
        await self.stream.close_connection()
