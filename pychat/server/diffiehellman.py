from collections import deque
from typing import Iterable

from pychat.common.stream import DataStream
from pychat.common.protocol import GetDHKey, GetDHMixedKey, PostFinalKey


async def dh_key_exchange(fernet_id: str, clients: Iterable[DataStream]):
    """Create a shared secret between clients"""

    key: int

    def next_client():
        clients.rotate()
        return clients[0]

    clients = deque(clients)
    ctx = {'fernet_id': fernet_id}

    for _ in range(len(clients)):
        # get public key from first client
        first_client = clients[0]
        key = await first_client.write(GetDHKey(**ctx))

        # Exchange between intermediate clients
        for _ in range(len(clients) - 2):
            client = next_client()
            key = await client.write(GetDHMixedKey(key=key, **ctx))

        # send key to final client to make secret
        final_client = next_client()
        await final_client.write(PostFinalKey(key=key, **ctx))
