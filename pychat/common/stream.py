import asyncio
from asyncio.exceptions import IncompleteReadError
from inspect import iscoroutine
from typing import Callable, Type, Optional, Union, Coroutine

from pychat.common.models import json_to_model, StreamData
from pychat.common.request import Request, Response

# network settings
SERVER_IP = '127.0.0.1'
PORT = 8888
HEADER_SIZE = 6  # bytes

RequestType = Type[Request]
RequestHandler = Callable[[Request], None | Response]
RequestTypeAndHandler = tuple[RequestType, RequestHandler]
      

class DataStream:
    """High-level facade to asyncio StreamReader and StreamWriter.
    Handles sending and receiving json to a paired stream. (server or client)"""
    def __init__(self, reader, writer):

        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        self.request_waiters: dict[str, asyncio.Future] = {}
        self.request_handlers: dict[RequestType, RequestHandler] = {}

        self.peername = self.writer.get_extra_info('peername')

    def __repr__(self):
        return f"{self.__class__.__name__}{self.peername}"

    async def _handle_request(self, request: Request):
        """Call the request handler callback with the request as an argument.
        If the request handler returned a Response, write the response back to
        the paired stream."""
        cb = self.request_handlers[type(request)]
        resp: None | Response | Coroutine = cb(request)

        # if the handler returned a coroutine, await it
        if iscoroutine(resp):
            resp: None | Response = await resp
        
        # send any response back to the requester
        if isinstance(resp, Response):
            resp.uid = request.uid
            await self.write(resp)

    def _handle_response(self, resp: Response):
        """Handle a response to a specific Request by setting the awaiting
        Request waiter Future with the Response StreamData"""
        resp_future = self.request_waiters[resp.uid]
        resp_future.set_result(resp)

    async def _read(self) -> StreamData:
        """parse the json data from stream into a StreamData object"""
        # get body length from header
        body_length = int.from_bytes(
            bytes=await self.reader.readexactly(HEADER_SIZE),
            byteorder='big'
        )
        body: bytes = await self.reader.readexactly(body_length)

        return json_to_model(body)

    async def write(self, data: StreamData) -> Optional[Response]:
        """Send the StreamData to the paired stream. If the StreamData is
        an instance of Request and the Request expects a response, await the
        Response object"""

        body: bytes = data.json().encode()
        header: bytes = len(body).to_bytes(HEADER_SIZE, 'big')

        self.writer.writelines([header, body])
        await self.writer.drain()

        if not isinstance(data, Request) or not data.needs_response():
            return
        
        request: Request = data

        # add a future to request waiters to be set when a response is received
        response = asyncio.Future()
        self.request_waiters[request.uid] = response

        # wait for the response future to be set
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
    
    def register_request_handler(self, type_: RequestType, cb: RequestHandler):
        """Configure a callback to use when receiving Requests of the specified
        type. The callback can be sync or async"""
        self.request_handlers[type_] = cb
    
    def register_request_handlers(self, *handlers: tuple[RequestTypeAndHandler]):
        """Convencience function to multiple multiple request handlers with
        a single function call"""
        for type_, handler in handlers:
            self.register_request_handler(type_, handler)

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Closed connection to {self}")
