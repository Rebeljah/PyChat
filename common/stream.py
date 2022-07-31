import asyncio
from asyncio.exceptions import IncompleteReadError
import json

from . import HEADER_SIZE
from .pubsub import PubSub
from .data import StreamData
from typing import Optional, Type


class DataStream:
    """High-level facade to asyncio StreamReader and StreamWriter.
    Handles sending and receiving json to a paired stream. (server or client)"""
    def __init__(self, reader, writer):

        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        # used for directly awaiting data (precedence over pubsub)
        self.awaiting_data: Optional[asyncio.Event] = None
        self.awaited_dataclass: Optional[Type[StreamData]] = None
        self.awaited_data: Optional[StreamData] = None

        # for subscribing callbacks to data types
        self.data_pubsub = PubSub()

        self.peername = self.writer.get_extra_info('peername')

    def __repr__(self):
        return f"{self.__class__.__name__}{self.peername}"

    async def read(self) -> StreamData:
        """parse the json data from stream into a StreamData object"""
        read_length = int.from_bytes(
            bytes=await self.reader.readexactly(HEADER_SIZE),
            byteorder='big'
        )
        data: bytes = await self.reader.readexactly(read_length)

        data: dict = json.loads(data)
        data: StreamData = StreamData.from_dict(data)

        print(f"{self} <<< {data}")
        return data

    async def write(self, data: StreamData):
        """Send the json as a bytestring to stream"""
        data = bytes(data.as_string(), 'utf-8')

        header_bytes = len(data).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header_bytes, data])
        await self.writer.drain()

        print(f"{self} >>> {data}")

    async def listen(self):
        """Listen for json messages and use parent functions to handle them"""
        try:
            while True:
                # if stream is awaiting the dataclass, route to awaiting caller,
                # else publish the data to all subscribers of the dataclass
                data = await self.read()
                if self.awaiting_data and isinstance(data, self.awaited_dataclass):
                    self.awaited_data = data
                    self.awaiting_data.set()
                else:
                    self.data_pubsub.publish(data, pass_attrs=False)
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            print(f"Handling error while reading from {self} ({e})")
        finally:
            await self.close_connection()

    def data_subscribe(self, data_class: Type[StreamData], callback):
        """Run a callback when the specified dataclass is received. The received
        StreamData instance is sent as an argument"""
        self.data_pubsub.subscribe(data_class, callback)

    async def wait_for(self, data_class: Type[StreamData]) -> StreamData:
        """Only to be used by one coro at a time. The next time the stream
        receives the specified dataclass, it will be returned from this coro
        rather than being published in the stream data_pubsub"""
        assert not any([
            self.awaited_dataclass,
            self.awaiting_data,
            self.awaited_data
        ])

        self.awaited_dataclass = data_class
        self.awaiting_data = asyncio.Event()

        await self.awaiting_data.wait()
        stream_data = self.awaited_data

        self.awaited_dataclass = None
        self.awaiting_data = None
        self.awaited_data = None

        return stream_data

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")

