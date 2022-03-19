import asyncio
from collections import defaultdict

from common.stream import NetworkInterface
from common.data import ClientData, MessageData

ChannelID = str


class ChatChannels(defaultdict[str, set['ClientInterface']]):
    """Provides a way to quickly access and edit clients in chat channels"""
    def __init__(self):
        super().__init__(set)

    def add_new_client(self, reader, writer):
        """Add a newly connected client to the default channel"""
        client = ClientInterface(self, reader, writer)
        self['default'].add(client)

    def remove_client(self, channel_id, client):
        """Remove the client from a chat channel"""
        if client in self[channel_id]:
            self[channel_id].remove(client)
            print(f"{client} was removed from channel {channel_id}")

    def purge_client(self, client):
        """Remove the client from all chat channels"""
        for channel_id in self:
            self.remove_client(channel_id, client)
        print(f"Purged {client} from all chat channels")


class ClientInterface(NetworkInterface):
    """class to represent a connected client on the server side"""
    def __init__(self, client_dir: ChatChannels, reader, writer):
        super().__init__(reader, writer)

        self.client_dir = client_dir

        self.client_info: ClientData = None

        self.data_pubsub.subscribe(ClientData, self.receive_client_info)
        self.data_pubsub.subscribe(MessageData, self.forward_chat_message)

    async def receive_client_info(self, client_info: ClientData):
        """receive and copy client info"""
        self.client_info = client_info

        print(f"{self} <<< client info {client_info}")

    async def forward_chat_message(self, message: MessageData):
        """After receiving message data, the server sends the same message
        data to all clients who are in the same channel"""
        for client in self.client_dir[message.channel_id]:
            asyncio.create_task(client.stream.write(message))

        print(f"{self} >>> chat message {message}")

    def cleanup(self):
        self.client_dir.purge_client(self)
