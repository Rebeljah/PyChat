import asyncio

from client_network import ServerInterface
from secrets import token_urlsafe

from common.events import GUISentMessage
from common.stream import ClientInfo
import gui


class CurrentUser:
    def __init__(self, app):
        self.app = app

        self.id = token_urlsafe(16)
        self.chat_channels = ['DEBUG']
        self.current_channel_id = self.chat_channels[0]

    def get_info(self) -> ClientInfo:
        return ClientInfo(self.id, self.chat_channels)


class ChatApp:
    """Controls backend app logic"""
    def __init__(self, reader, writer):
        self.user = CurrentUser(self)

        gui.pubsub.subscribe(GUISentMessage, self.send_chat_message)

        # create a server interface and send client info to server
        self.server = ServerInterface(self, reader, writer)
        asyncio.create_task(self.server.send_data(self.user.get_info()))

    async def send_chat_message(self, text):
        channel_id = self.user.current_channel_id
        sender_id = self.user.id
        await self.server.send_chat_msg(text, sender_id, channel_id)
