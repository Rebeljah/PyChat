import asyncio
from asyncio.exceptions import IncompleteReadError
import json
from typing import Type

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

        self.data_pubsub = PubSub()

        self.peername = self.writer.get_extra_info('peername')

        self.listen = asyncio.create_task(self._listen())

    def __repr__(self):
        return f"{self.__class__}: {self.peername}"

    async def _listen(self, decrypt=False):
        """Listen for json messages and use parent functions to handle them"""
        async def read() -> StreamData:
            """parse the json data from stream into a StreamData object"""
            read_length = int.from_bytes(
                bytes=await self.reader.readexactly(HEADER_SIZE),
                byteorder='big'
            )
            data: bytes = await self.reader.readexactly(read_length)

            if decrypt:  # TODO: implement encryption
                data = data

            data: dict = json.loads(data)
            return StreamData.from_dict(data)

        try:
            while True:
                self.data_pubsub.publish(await read(), pass_attrs=False)
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            print(f"Handling error while reading from {self} ({e})")
        finally:
            await self.close_connection()

    async def write(self, data: StreamData, encrypt=False):
        """Send the json as a bytestring to stream"""
        data = json.dumps(data.as_dict(), indent=None, separators=(',', ':'))
        data = bytes(data, 'utf-8')

        if encrypt:  # TODO: implement encryption
            data = data

        header_bytes = len(data).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header_bytes, data])
        await self.writer.drain()

    def subscribe(self, data_type: Type[StreamData], callback):
        self.data_pubsub.subscribe(data_type, callback)

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")


class NetworkInterface:
    """Base class for client or server to subclass to define functions for
    sending and receiving data to a DataStream"""
    def __init__(self, reader, writer):
        self.stream = DataStream(self, reader, writer)

    def __repr__(self):
        return f"{self.__class__} {self.stream.peername}"

    async def send_data(self, data: StreamData):
        await self.stream.write(data)
        print(f"{self} >>> {data}")
