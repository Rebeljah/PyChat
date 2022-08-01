import asyncio
from asyncio.exceptions import IncompleteReadError
import json

from .pubsub import PubSub
from .data import StreamData, Request, Response
from typing import Callable, Type

# network settings
SERVER_IP = '127.0.0.1'
PORT = 8888
HEADER_SIZE = 6  # bytes
      

class DataStream:
    """High-level facade to asyncio StreamReader and StreamWriter.
    Handles sending and receiving json to a paired stream. (server or client)"""
    def __init__(self, reader, writer):

        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        self.pubsub = PubSub()
        self.request_waiters: dict[str, asyncio.Future] = {}
        self.request_handlers: dict[Request.Types, Callable] = {}

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
        data = bytes(data.as_json(), 'utf-8')

        header_bytes = len(data).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header_bytes, data])
        await self.writer.drain()

        print(f"{self} >>> {data}")

    async def listen(self):
        """Listen for json messages and use parent functions to handle them"""
        try:
            while True:
                data = await self.read()
                if isinstance(data, Response):
                    self.handle_response(data)
                elif isinstance(data, Request):
                    self.handle_request(data)
                else:
                    self.pubsub.publish(data)
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            print(f"Handling error while reading from {self} ({e})")
        finally:
            await self.close_connection()

    def on(self, data_class: Type[StreamData], callback):
        """Run a callback when the specified dataclass is received. The received
        StreamData instance is sent as an argument"""
        self.pubsub.subscribe(data_class, callback)
    
    def register_request_handler(self, type: Request.type, callback: Callable):
        self.request_handlers[int(type)] = callback
    
    async def request(self, type: Request.Types, ctx=None) -> StreamData:
        req = Request(type=type, ctx=ctx or {})

        fut = asyncio.Future()
        self.request_waiters[req.id] = fut

        await self.write(req)
        await fut

        del self.request_waiters[req.id]
        return fut.result()
    
    def handle_request(self, req: Request):
        cb = self.request_handlers[req.type]
    
    async def respond(self, request_id: str, data: StreamData):
        resp = Response(id=request_id, data=data)
        await self.write(resp)
    
    def handle_response(self, resp: Response):
        self.request_waiters[resp.id].set_result(resp.data)

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")
