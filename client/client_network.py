from common.stream import NetworkInterface
from common.events import ReceivedMessage
from common.data import MessageData
from client import events


class ServerInterface(NetworkInterface):
    """Provides methods for communicating with the server"""
    def __init__(self, app, reader, writer):
        super().__init__(reader, writer)

        self.app = app

        self.data_pubsub.subscribe(MessageData, self.receive_chat_msg)

    async def send_chat_msg(self, text, sender_id, channel_id):
        msg = MessageData(channel_id, sender_id, text)
        await self.stream.write(msg)
        print(f"{self} >>> chat message {msg}")

    def receive_chat_msg(self, msg: MessageData):
        events.publish(ReceivedMessage(msg))
        print(f"{self} <<< chat message {msg}")
