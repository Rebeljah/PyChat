import asyncio
from collections import deque
from typing import Iterable, Sequence

from pychat.common.stream import DataStream
from pychat.common.request import GetDHKey, GetDHMixedKey, PostFinalKey


def dh_Key_exchange(fernet_uid: str, clients: Iterable[DataStream]):
    """Created a shared sescret between clients. Creates N orderings where N
    is the number of clients where each client gets a chance to be the end
    of the sequence and set their secret key"""

    clients = deque(clients)
    ctx = {'fernet_uid': fernet_uid}

    for _ in range(len(clients)):
        asyncio.create_task(_exchange(ctx, tuple(clients)))
        clients.rotate()


async def _exchange(ctx: dict, clients: Sequence[DataStream]):
    """Take a sequence of clients and create a shared secret for the last
    client in the sequence"""

    # get public key from first client
    first_client = clients[0]
    r: GetDHKey.Response = await first_client.write(GetDHKey(**ctx))
    key = r.key

    # Exchange between intermediate clients
    for client in clients[1:-1]:
        r: GetDHMixedKey.Response = await client.write(GetDHMixedKey(key=key, **ctx))
        key = r.key

    # send key to final client to make secret
    final_client = clients[-1]
    await final_client.write(PostFinalKey(key=key, **ctx))
