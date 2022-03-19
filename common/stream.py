import asyncio
from asyncio.exceptions import IncompleteReadError

from . import HEADER_SIZE
from .events import PubSub
from .data import StreamData


class DataStream:
    """High-level facade to asyncio StreamReader and StreamWriter.
    Handles sending and receiving json to a paired stream. (server or client)"""
    def __init__(self, parent, reader, writer):
        self.parent = parent

        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        self.peername = self.writer.get_extra_info('peername')

        asyncio.create_task(self._listen())

    def __repr__(self):
        return f"{self.__class__}: {self.peername}"

    async def _listen(self):
        """Listen for json messages and use parent functions to handle them"""
        async def read() -> StreamData:
            """parse the json data from stream into a StreamData object"""
            read_length = int.from_bytes(
                bytes=await self.reader.readexactly(HEADER_SIZE),
                byteorder='big'
            )
            data: bytes = await self.reader.readexactly(read_length)
            return StreamData.from_json(data)

        try:
            while True:
                self.parent.publish_data(await read())
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            print(f"Handling error while reading from {self} ({e})")
        finally:
            await self.close_connection()

    async def write(self, data: StreamData):
        """Send the json as a bytestring to stream"""
        data = bytes(data.to_json(), 'utf-8')
        header_bytes = len(data).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header_bytes, data])
        await self.writer.drain()

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")


class NetworkInterface:
    """Base class for client or server to subclass to define functions for
    sending and receiving data to a DataStream"""
    def __init__(self, reader, writer):
        self.stream = DataStream(self, reader, writer)
        self.data_pubsub = PubSub()

    def __repr__(self):
        return f"{self.__class__} {self.stream.peername}"

    async def send_data(self, data: StreamData):
        await self.stream.write(data)
        print(f"{self} >>> {data}")

    def publish_data(self, data: StreamData):
        self.data_pubsub.publish(data, pass_attrs=False)
