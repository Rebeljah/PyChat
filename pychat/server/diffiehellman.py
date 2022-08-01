from collections import deque
from typing import Iterable

from common.stream import DataStream
from common.data import Request


async def dh_key_exchange(encryption_id: str, clients: Iterable[DataStream]):
    """Create a shared secret between clients"""
    def next_client():
        clients.rotate()
        return clients[0]

    clients = deque(clients)

    for _ in range(len(clients)):
        # get public key from first client
        first_client = clients[0]
        ctx = {'encryption_id': encryption_id}
        key = await first_client.request(Request.Types.GetDHPublicKey, ctx)

        for _ in range(len(clients) - 2):
            client = next_client()
            ctx = {'key': key}
            key = await client.request(Request.Types.GetDHMixedPublicKey, ctx)

        final_client = next_client()
        key.is_final = True
        await final_client.write(key)