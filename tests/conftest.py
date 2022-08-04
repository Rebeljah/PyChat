import pytest, pytest_asyncio
import asyncio

from pychat.client.diffiehellman import create_fernet
from pychat.common.stream import DataStream, SERVER_IP, PORT


N_CLIENTS = 3


@pytest_asyncio.fixture
async def streams() -> list[tuple[DataStream, DataStream]]:
    """Return server DataStreams and client DataStreams connected to them"""        
    ServerStream = ClientStream = DataStream
    streams: list[tuple[ServerStream, ClientStream]] = []

    server = await asyncio.start_server(
        lambda r, w: make_server_stream(fut, r, w),
         host=SERVER_IP, port=PORT
    )
    await server.start_serving()

    def make_server_stream(fut, r, w):
        s = DataStream(r, w)
        asyncio.create_task(s.listen())
        fut.set_result(s)

    for _ in range(N_CLIENTS):
        fut = asyncio.Future()
        
        # create client stream
        reader, writer = await asyncio.open_connection(host=SERVER_IP, port=PORT)
        client_stream = DataStream(reader, writer)
        asyncio.create_task(client_stream.listen())

        # wait for the server-stream to be connected to client
        await fut
        streams.append((fut.result(), client_stream))

    yield streams

    # cleanup client and server streams
    for s_stream, c_stream in streams:
        c_stream.writer.close()
        s_stream.writer.close()
        await c_stream.writer.wait_closed()
        await s_stream.writer.wait_closed()

    server.close()
    await server.wait_closed()


@pytest.fixture
def fernet():
    return create_fernet(123478686)