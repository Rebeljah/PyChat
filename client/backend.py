import asyncio
from cryptography.fernet import Fernet
from typing import Optional

from client_network import ServerInterface
from encryption import DHKeyGenerator, create_fernet
from common.events import PubSub

backend_events = PubSub()


class ChatChannel:
    def __init__(self):
        self.dh_key = DHKeyGenerator()
        self.encryption: Optional[Fernet] = None

    def roll_encryption(self, shared_secret: int):
        """Get a new message encryption context"""
        self.encryption = create_fernet(shared_secret)


class ChatApp:
    """Controls backend app logic"""
    def __init__(self, reader, writer):
        self.username = 'Pychat User'
        self.channel_id = 'default'
        self.chat_channels: dict[str, ChatChannel] = {}

        self.server = ServerInterface(self, reader, writer)

        asyncio.create_task(self.server.send_chat_message('ayy lmao'))
