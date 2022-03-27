import asyncio
from cryptography.fernet import Fernet
from typing import Optional

from encryption import DHKeyGenerator, create_fernet
from common.events import PubSub
from common.stream import DataStream
from common.data import (
    StreamData, MessageData, DHPublicKey, DHPublicKeyRequest, EncryptedData
)

backend_events = PubSub()
ChannelId = str


class ChatChannel:
    def __init__(self, app, uid):
        self.app: 'ChatApp' = app
        self.uid = uid

        self.dh_key = DHKeyGenerator()
        self.fernet: Optional[Fernet] = None

    def __repr__(self):
        return f"{self.__class__.__name__} '{self.uid}'"

    def roll_encryption(self, shared_secret: int):
        """Get a new message encryption context"""
        self.fernet = create_fernet(shared_secret)
        print(f"Updated encryption for {self}")

        asyncio.create_task(
            self.app.stream.write(
                MessageData(self.uid, self.app.username, 'Ayy its encrypted lmao'),
                encrypt=True,
                channel_id=self.uid
            )
        )


class ChatApp:
    """Controls backend app logic"""
    def __init__(self, reader, writer):
        self.username = 'Pychat User'
        self.curr_channel_id = 'DEFAULTCHANNEL'
        self.chat_channels: dict[ChannelId, ChatChannel] = {
            'DEFAULTCHANNEL': ChatChannel(self, 'DEFAULTCHANNEL'),
        }

        self.stream = EncryptedStream(self.chat_channels, reader, writer)

        asyncio.create_task(self._listen())

    def __repr__(self):
        return f"{self.__class__.__name__}({self.username})"

    async def _listen(self):
        self.stream.data_subscribe(MessageData, self.receive_msg)
        self.stream.data_subscribe(DHPublicKeyRequest, self.send_dh_key)
        self.stream.data_subscribe(DHPublicKey, self.receive_dh_key)
        await self.stream.listen()

    def receive_msg(self, msg: MessageData):
        print(f"{self} <<< {msg}")

    async def send_dh_key(self, request: DHPublicKeyRequest):
        channel = self.chat_channels[request.channel_id]
        await self.stream.write(
            DHPublicKey(
                channel_id=request.channel_id,
                is_final=False,
                key=channel.dh_key.public
            )
        )

    async def receive_dh_key(self, key: DHPublicKey):
        """Mix the chat channel secret and either roll encryption or send
        partial key back to server"""
        chat_channel: ChatChannel = self.chat_channels[key.channel_id]

        mixed_key: int = chat_channel.dh_key.mix_other(key.key)

        if key.is_final:
            chat_channel.roll_encryption(mixed_key)
        else:
            key.key = mixed_key
            await self.stream.write(key)


class EncryptedStream(DataStream):
    def __init__(self, channels: dict, reader, writer):
        super().__init__(reader, writer)

        # keep track of channels for encryption
        self.channels: dict = channels

    async def read(self) -> StreamData:
        data: StreamData = await super().read()

        if isinstance(data, EncryptedData):
            fernet = self.channels[data.channel_id].fernet
            data = data.decrypt(fernet)

        return data

    async def write(self, data: StreamData, encrypt=False, channel_id=None):
        if encrypt:
            fernet = self.channels[channel_id].fernet
            data = data.encrypted(fernet, channel_id)

        await super().write(data)
