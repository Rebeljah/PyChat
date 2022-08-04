import asyncio
from asyncio.exceptions import IncompleteReadError
import json
from inspect import iscoroutinefunction
from typing import Callable, Type, Optional

from pychat.common.protocol import json_to_model, StreamData, Request, Response

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

        self.request_waiters: dict[str, asyncio.Future] = {}
        self.request_handlers: dict[type[Request], Callable] = {}

        self.peername = self.writer.get_extra_info('peername')

    def __repr__(self):
        return f"{self.__class__.__name__}{self.peername}"

    async def _read(self) -> StreamData:
        """parse the json data from stream into a StreamData object"""
        read_length = int.from_bytes(
            bytes=await self.reader.readexactly(HEADER_SIZE),
            byteorder='big'
        )
        data: bytes = await self.reader.readexactly(read_length)

        data: StreamData = json_to_model(data)

        print(f"{self} <<< {data}")
        return data

    async def write(self, data: StreamData) -> Optional[Response]:
        """Send the StreamData to the paired stream. If the StreamData is
        an instance of Request and the Request expects a response, await the
        Response object"""

        body: bytes = data.json().encode()
        header: bytes = len(body).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header, body])
        await self.writer.drain()

        print(f"{self} >>> {data}")

        if not isinstance(data, Request) or not data.needs_response():
            return
        
        request: Request = data

        # return response data when a response with matching id is received
        response = asyncio.Future()
        self.request_waiters[request.uid] = response

        try:
            await response
        finally:
            del self.request_waiters[request.uid]

        return response.result()

    async def listen(self):
        """Read and handle Request and Responses"""
        try:
            while True:
                data: StreamData = await self._read()
                if isinstance(data, Response):
                    self._handle_response(data)
                elif isinstance(data, Request):
                    await self._handle_request(data)
        except (OSError, IncompleteReadError, ConnectionResetError) as e:
            pass
        finally:
            await self.close_connection()
    
    def register_request_handler(self, request_type: Type[Request], callback: Callable):
        """Configure a callback to use when receiving Requests of the specified
        type. The callback can be sync or async"""
        self.request_handlers[request_type] = callback

    async def _handle_request(self, request: Request):
        """React to the received Request using the registed callback."""
        cb = self.request_handlers[type(request)]
        if iscoroutinefunction(cb):
            await cb(request)
        else:
            cb(request)
    
    def _handle_response(self, response: Response):
        """Handle a response to a specific Request by setting the awaiting
        Request waiter Future with the Response StreamData"""
        self.request_waiters[response.uid].set_result(response)

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")


class ClientStream(DataStream):
    """DataStream for communication with a client"""
    def __init__(self, reader, writer):
        super().__init__(reader, writer)


class ServerStream(DataStream):
    """DataStream for communication with the server"""
    def __init__(self, reader, writer):
        super().__init__(reader, writer)
