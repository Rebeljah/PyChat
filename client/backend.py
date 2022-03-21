import asyncio

from client import EVENTS
from common.events import GuiSentMessage, ReceivedMessage
from common.data import MessageData, ClientData
from common.stream import NetworkInterface


class ServerInterface(NetworkInterface):
    """Provides methods for communicating with the server"""
    def __init__(self, app, reader, writer):
        super().__init__(reader, writer)

        self.app = app

        self.stream.subscribe(MessageData, self.receive_chat_msg)

    def receive_chat_msg(self, msg: MessageData):
        EVENTS.publish(ReceivedMessage(msg))
        print(f"{self} <<< chat message {msg}")

    async def send_chat_message(self, text):
        client_data = ClientData(
            self.app.client.channel_id, self.app.client.username
        )
        await self.send_data(MessageData(client_data, text))


class Client:
    def __init__(self, app, username):
        self.app = app

        self.username = username
        self.channels = {'default'}
        self.channel_id = 'default'


class ChatApp:
    """Controls backend app logic"""
    def __init__(self, reader, writer):
        # create a server interface and send client info to server
        self.server = ServerInterface(self, reader, writer)

        self.client = Client(self, username='NEW USERNAME')

        EVENTS.subscribe(GuiSentMessage, self.server.send_chat_message)

        asyncio.create_task(self.server.send_chat_message('ayy lmao'))
