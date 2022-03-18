import asyncio

from common.stream import NetworkInterface, ChatMessage, StreamData


class ServerInterface(NetworkInterface):
    """Provides methods for communicating with the server"""
    def __init__(self, app, reader, writer):
        super().__init__(reader, writer)

        self.app = app

        self.data_handlers = {
            ChatMessage: self.receive_chat_msg,
        }

    async def send_data(self, data: StreamData):
        await self.stream.write(data)
        print(f"{self} >>> {data}")

    async def send_chat_msg(self, text, sender_id, channel_id):
        msg = ChatMessage(channel_id, sender_id, text)
        await self.stream.write(msg)

        print(f"{self} >>> chat message {msg}")

    async def receive_chat_msg(self, msg: ChatMessage):
        print(f"{self} <<< chat message {msg}")

