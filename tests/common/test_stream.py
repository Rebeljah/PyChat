import pytest
import asyncio
import random

from pychat.common.protocol import Request, PostFinalKey, GetDHKey


@pytest.fixture
def stream_pair(streams):
    server, client = random.choice(streams)
    return server, client


@pytest.mark.asyncio
async def test_can_make_request_without_response(stream_pair):
    server, client = stream_pair

    req_received = asyncio.Event()
    server.register_request_handler(
        request_type=PostFinalKey, callback=lambda req: req_received.set()
    )
    await client.write(PostFinalKey(fernet_id='fernid', key=777))
    await asyncio.sleep(0.1)

    assert req_received.is_set()

@pytest.mark.asyncio
async def test_can_make_request_with_response(stream_pair):
    server, client = stream_pair

    async def respond(req: Request):
        await server.write(req.Response(uid=req.uid, key=777))

    server.register_request_handler(request_type=GetDHKey, callback=respond)

    response = await client.write(GetDHKey(fernet_id='fernid'))

    assert response.key == 777

