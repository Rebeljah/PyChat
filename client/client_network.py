import asyncio

from client import backend_events
from common.data import MessageData, DHPublicKey
from common.stream import NetworkInterface
from common.events import ReceivedMessage


class ServerInterface(NetworkInterface):
    """Provides methods for communicating with the server"""
    def __init__(self, app, reader, writer):
        super().__init__(reader, writer)

        self.app = app

        self.stream.data_subscribe(MessageData, self.receive_chat_msg)
        self.stream.data_subscribe(DHPublicKey, self.receive_dh_key)

    def receive_chat_msg(self, msg: MessageData):
        backend_events.publish(ReceivedMessage(msg))
        print(f"{self} <<< chat message {msg}")

    async def send_chat_message(self, text):
        await self.send_data(
            MessageData(
                self.app.channel_id,
                self.app.username,
                text
            )
        )

    def receive_dh_key(self, key: DHPublicKey):
        """Mix the chat channel secret and either roll encryption or send
        partial key back to server"""
        from client.backend import ChatChannel
        chat_channel: ChatChannel = self.app.chat_channels[key.channel_id]

        mixed_key: int = chat_channel.dh_key.mix_other(key.key)
        if key.is_final:
            chat_channel.roll_encryption(mixed_key)
        else:
            key.key = mixed_key
            asyncio.create_task(self.send_data(key))
