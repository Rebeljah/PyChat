import asyncio
from asyncio.exceptions import IncompleteReadError
import json
from typing import Iterable, Type, Callable

from . import HEADER_SIZE


class StreamData:
    def __repr__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"

    def to_dict(self):
        return {'type': self.__class__.__name__, **self.__dict__}

    @classmethod
    def from_dict(cls, data: dict):
        """Determine which stream data class to use then new it up w/ input dict"""
        data_class = type_name_to_class[data['type']]
        return data_class(**data)


class ClientInfo(StreamData):
    def __init__(self, uid: str, chat_channels: Iterable[str], **kwargs):
        super().__init__()

        self.uid = uid
        self.chat_channels = chat_channels


class ChatMessage(StreamData):
    def __init__(self, channel_id, sender_id, text, **kwargs):
        super().__init__()

        self.channel_id = channel_id
        self.sender_id = sender_id
        self.text = text


type_name_to_class: dict[str, Type[StreamData]] = {
    cls.__name__: cls for cls in [ChatMessage, ClientInfo]
}


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
            data: dict = json.loads(await self.reader.readexactly(read_length))
            return StreamData.from_dict(data)

        try:
            while True:
                await self.parent.handle_data(await read())
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            print(f"Handling error while reading from {self} ({e})")
        finally:
            await self.cleanup()

    async def write(self, data: StreamData):
        """Send the json as a bytestring to stream"""
        data = bytes(
            json.dumps(data.to_dict(), indent=None, separators=(',', ':')),
            'utf-8'
        )
        header_bytes = len(data).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header_bytes, data])
        await self.writer.drain()

    async def cleanup(self):
        await self.close_connection()
        self.parent.cleanup()
        print(f"Cleaned up {self}")

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")


class NetworkInterface:
    """Base class for client or server to subclass to define functions for
    sending and receiving data to a DataStream"""
    def __init__(self, reader, writer):
        self.stream = DataStream(self, reader, writer)
        self.data_handlers: dict[Type[StreamData], Callable] = {}

    def __repr__(self):
        return f"{self.__class__} {self.stream.peername}"

    async def handle_data(self, data: StreamData):
        callback = self.data_handlers[data.__class__]
        await callback(data)

    def cleanup(self):
        print(f"Cleaned up {self} (WARNING! NOT IMPLEMENTED)")
