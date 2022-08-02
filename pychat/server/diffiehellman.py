from collections import deque
from typing import Iterable

from common.stream import DataStream
from common.data import Request
from pychat.common.data import DHPublicKey


async def dh_key_exchange(encryption_id: str, clients: Iterable[DataStream]):
    """Create a shared secret between clients"""

    key: DHPublicKey

    def next_client():
        clients.rotate()
        return clients[0]

    clients = deque(clients)
    ctx = {'encryption_id': encryption_id}

    for _ in range(len(clients)):
        # get public key from first client
        first_client = clients[0]
        key = await first_client.request(Request.Client.GetDHPublicKey, ctx)

        for _ in range(len(clients) - 2):
            ctx['other_key'] = key
            client = next_client()
            key = await client.request(Request.Client.GetDHMixedPublicKey, ctx)

        ctx['other_key'] = key
        final_client = next_client()
        await final_client.request(Request.Client.PostFinalDHMixedPublicKey, ctx)
