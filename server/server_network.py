import asyncio
from secrets import token_urlsafe

from common.stream import NetworkInterface
from common.data import MessageData

ChannelID = str


class ChatChannel(set['ClientInterface']):
    def __init__(self, uid=None):
        super().__init__()
        self.uid = uid or token_urlsafe(16)


class ChatChannels(dict[str, ChatChannel]):
    """Provides a way to quickly access and edit clients in chat channels"""
    def __init__(self):
        super().__init__(default=ChatChannel('default'))

    def handle_client(self, reader, writer):
        """Add a newly connected client to the default channel"""
        client = ClientInterface(self, reader, writer)
        self['default'].add(client)

    def purge_client(self, client):
        """Remove the client from all chat channels"""
        for channel in self.values():
            if client in channel:
                channel.remove(client)


class ClientInterface(NetworkInterface):
    """class to represent a connected client on the server side"""
    def __init__(self, chat_channels: ChatChannels, reader, writer):
        super().__init__(reader, writer)

        self.chat_channels = chat_channels
        self.stream.data_subscribe(MessageData, self.send_chat_message)

    def send_chat_message(self, message: MessageData):
        """Send the message data to all clients in the chat channel"""
        for client in self.chat_channels[message.channel_id]:
            asyncio.create_task(client.stream.write(message))

        print(f"{self} >>> forwarded {message}")

    def cleanup(self):
        self.chat_channels.purge_client(self)
