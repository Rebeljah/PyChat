import asyncio
from typing import Type, Callable

from common.stream import NetworkInterface, ClientInfo, ChatMessage


class ClientInterface(NetworkInterface):
    ALL_CLIENTS = set()

    """class to represent a connected client on the server side"""
    def __init__(self, reader, writer):
        super().__init__(reader, writer)

        self.client_info = None

        self.data_handlers = {
            ClientInfo: self.receive_client_info,
            ChatMessage: self.forward_chat_message,
        }

    async def receive_client_info(self, client_info: ClientInfo):
        """receive and copy client info"""
        self.client_info = client_info

        print(f"{self} <<< client info {client_info}")

    async def forward_chat_message(self, message: ChatMessage):
        """After receiving message data, the server sends the same message
        data to all clients who are in the same channel"""
        client: ClientInterface
        for client in self.ALL_CLIENTS:
            if message.channel_id in client.client_info.chat_channels:
                asyncio.create_task(client.stream.write(message))

        print(f"{self} >>> chat message {message}")

    def make_active(self):
        self.ALL_CLIENTS.add(self)

    def cleanup(self):
        self.ALL_CLIENTS.remove(self)
        super().cleanup()
