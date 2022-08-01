import pytest, pytest_asyncio
import asyncio
import random

from pychat.common.stream import DataStream
from pychat.common.data import Request

IP, PORT = '127.0.0.1', 5000
N_CLIENTS = 3


@pytest_asyncio.fixture
async def streams() -> list[tuple[DataStream, DataStream]]:
    """Return server DataStreams and client DataStreams connected to them"""        
    ServerStream = ClientStream = DataStream
    streams: list[tuple[ServerStream, ClientStream]] = []

    server = await asyncio.start_server(
        lambda r, w: make_server_stream(fut, r, w),
         host=IP, port=PORT
    )
    await server.start_serving()

    def make_server_stream(fut, r, w):
        s = DataStream(r, w)
        asyncio.create_task(s.listen())
        fut.set_result(s)

    for _ in range(N_CLIENTS):
        fut = asyncio.Future()
        
        # create client stream
        reader, writer = await asyncio.open_connection(host=IP, port=PORT)
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
def client_stream(streams):
    return random.choice(streams)[1]


@pytest.fixture
def server_stream(streams):
    return random.choice(streams)[0]


@pytest.fixture
def stream_pair(streams):
    return random.choice(streams)


@pytest.mark.asyncio
async def test_clients_can_connect_to_server(streams):
    assert len(streams) == N_CLIENTS


@pytest.mark.asyncio
async def test_stream_can_make_sync_callback_on_trigger(stream_pair, stream_data):
    server, client = stream_pair

    callback_run = asyncio.Event()
    server.on(type(stream_data), lambda _: callback_run.set())

    await client.write(stream_data)
    await asyncio.sleep(0.05)

    assert callback_run.is_set()


@pytest.mark.asyncio
async def test_stream_can_make_async_callback_on_trigger(stream_pair, stream_data):
    server, client = stream_pair

    called = asyncio.Event()
    async def cb(trigger):
        called.set()
    
    server.on(type(stream_data), cb)
    await client.write(stream_data)
    await asyncio.sleep(0.05)

    assert called.is_set()


@pytest.mark.asyncio
async def test_can_make_request_without_response(stream_pair):
    server, client = stream_pair

    req_received = asyncio.Event()
    server.register_request_handler(type=1, callback=lambda req: req_received.set())

    await client.request(type=1, get_resp=False)
    await asyncio.sleep(0.05)

    assert req_received.is_set()

@pytest.mark.asyncio
async def test_can_make_request_with_response(stream_pair, stream_data):
    server, client = stream_pair

    async def respond(req: Request):
        await server.respond(req.id, stream_data)

    server.register_request_handler(type=1, callback=respond)

    resp_data = await client.request(type=1)

    assert resp_data == stream_data


@pytest.mark.asyncio
async def test_can_make_request_with_context_with_response(stream_pair, stream_data):
    server, client = stream_pair

    async def respond(req: Request):
        assert req.ctx == {'test': 'data'}
        await server.respond(req.id, stream_data)

    server.register_request_handler(type=1, callback=respond)

    resp_data = await client.request(type=1, ctx={'test': 'data'})

    assert resp_data == stream_data
