import asyncio

from client_network import ServerInterface
from secrets import token_urlsafe

from common.events import GuiSentMessage
from common.data import ClientData
from client import events


class Client:
    def __init__(self, app):
        self.app = app

        self.id = token_urlsafe(16)
        self.channel_id = 'default'

    def get_info(self) -> ClientData:
        return ClientData(id=self.id)


class ChatApp:
    """Controls backend app logic"""
    def __init__(self, reader, writer):
        self.client = Client(self)

        # create a server interface and send client info to server
        self.server = ServerInterface(self, reader, writer)
        asyncio.create_task(self.server.send_data(self.client.get_info()))

        events.subscribe(GuiSentMessage, self.send_chat_message)

    async def send_chat_message(self, text):
        channel_id, sender_id = self.client.channel_id, self.client.id
        await self.server.send_chat_msg(text, sender_id, channel_id)
