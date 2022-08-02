import asyncio
from asyncio.exceptions import IncompleteReadError
import json
from inspect import iscoroutinefunction
from enum import IntEnum

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
        self.request_handlers: dict[IntEnum, Callable] = {}

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
        """Read and handle Request and Responses. If StreamData is passed
        not wrapped in a Request/Response publish it to the pubusb."""
        try:
            while True:
                data = await self.read()
                if isinstance(data, Response):
                    self.handle_response(data)
                elif isinstance(data, Request):
                    await self.handle_request(data)
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
    
    
    async def request(self, type: IntEnum, ctx=None, get_resp=True) -> StreamData|None:
        """Send a request to the paired DataStream and optionally await a
        response. The context dict ctx is passed in the Request object to the
        paired DataStream"""
        req = Request(type=type, ctx=ctx or {})
        asyncio.create_task(self.write(req))

        if not get_resp:
            return None

        # return response data when a response with matching id is received
        data_fut = asyncio.Future()
        self.request_waiters[req.id] = data_fut

        await data_fut

        data: StreamData = data_fut.result()
        del self.request_waiters[req.id]

        return data
    
    def register_request_handler(self, type: IntEnum, callback: Callable):
        """Configure a callback to use when receiving Requests of the specified
        type. The callback can be sync or async"""
        self.request_handlers[type.value] = callback

    async def handle_request(self, req: Request):
        """React to the received Request using the registed callback."""
        cb = self.request_handlers[req.type]
        if iscoroutinefunction(cb):
            await cb(req)
        else:
            cb(req)
    
    async def respond(self, request_id: str, data: StreamData):
        """Send StreamData in response to a specific request"""
        resp = Response(id=request_id, data=data)
        await self.write(resp)
    
    def handle_response(self, resp: Response):
        """Handle a response to a specific Request by setting the awaiting
        Request waiter Future with the Response StreamData"""
        self.request_waiters[resp.id].set_result(resp.data)

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")
