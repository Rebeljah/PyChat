import asyncio
from secrets import token_urlsafe
from collections import deque

from common.data import DHPublicKey, DHPublicKeyRequest, StreamData, EncryptedData
from common.stream import DataStream

ChannelID = str


class Client:
    def __init__(self, channels, reader, writer):
        self.channels = channels

        self.stream = DataStream(reader, writer)
        asyncio.create_task(self._listen())

    def __repr__(self):
        return f"{self.__class__.__name__}{self.stream.peername}"

    async def _listen(self):
        self.stream.data_subscribe(EncryptedData, lambda data: self.channels[data.channel_id].distribute_data(data))
        await self.stream.listen()
        self.channels.purge_client(self)


class ChatChannel(set[Client]):
    def __init__(self, channels: 'ChatChannels', uid=None):
        super().__init__()
        self.channels = channels
        self.uid = uid or token_urlsafe(16)

    def add(self, client: Client) -> None:
        super().add(client)
        asyncio.create_task(self.dh_key_exchange())

    def remove(self, client: Client) -> None:
        super().remove(client)
        asyncio.create_task(self.dh_key_exchange())

    def distribute_data(self, data: StreamData):
        asyncio.gather(*[
            client.stream.write(data) for client in self
        ])

    async def dh_key_exchange(self):
        """Create a shared secret between clients in the channel"""
        def next_client():
            clients.rotate()
            return clients[0]

        async def await_key(client_):
            return await client_.stream.wait_for(DHPublicKey)

        clients = deque(self)
        client: Client
        key: DHPublicKey

        for _ in range(len(clients)):
            # get public key from first client
            client = clients[0]
            await client.stream.write(
                DHPublicKeyRequest(channel_id=self.uid)
            )
            key = await await_key(client)

            for _ in range(len(clients) - 2):
                client = next_client()
                await client.stream.write(key)
                key = await await_key(client)
            else:
                client = next_client()
                key.is_final = True
                await client.stream.write(key)


class ChatChannels(dict[ChannelID, ChatChannel]):
    def __init__(self):
        super().__init__(DEFAULTCHANNEL=ChatChannel(self, 'DEFAULTCHANNEL'))

    def handle_client(self, reader, writer):
        """Add a newly connected client to the default channel"""
        self['DEFAULTCHANNEL'].add(
            Client(self, reader, writer)
        )

    def purge_client(self, client):
        for channel in self.values():
            if client in channel:
                channel.remove(client)
        print(f"Purged {client} from all chat channels")
