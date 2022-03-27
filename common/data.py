from dataclasses import dataclass, asdict, field
from cryptography.fernet import Fernet
import json


@dataclass
class StreamData:
    __dataclass__: str = field(init=False, repr=False)

    def __post_init__(self):
        self.__dataclass__ = self.__class__.__name__

    def as_dict(self) -> dict:
        return asdict(self)

    def as_string(self) -> str:
        return json.dumps(self.as_dict(), indent=None, separators=(',', ':'))

    def encrypted(self, fernet: Fernet, channel_id) -> 'EncryptedData':
        data = self.as_string()

        data = fernet.encrypt(bytes(data, 'utf-8'))

        data = data.decode('utf-8')

        return EncryptedData(channel_id, data)

    @classmethod
    def from_dict(cls, d: dict):
        """Load the dict as StreamData. If any dict contained in d
        has a '__dataclass__' key, it is recursively converted into StreamData"""
        data_class = DATA_CLASSES[d['__dataclass__']]
        del d['__dataclass__']

        for key, val in d.items():
            if isinstance(val, dict) and '__dataclass__' in val:
                d[key] = StreamData.from_dict(val)

        return data_class(**d)


@dataclass
class EncryptedData(StreamData):
    channel_id: str
    data: str

    def decrypt(self, fernet: Fernet) -> StreamData:
        data = self.data.encode('utf-8')

        data = fernet.decrypt(data)

        data = json.loads(data)

        return StreamData.from_dict(data)


@dataclass
class MessageData(StreamData):
    channel_id: str
    username: str
    text: str


@dataclass
class DHPublicKey(StreamData):
    channel_id: str  # chat channel where exchange is happening
    is_final: bool  # If True, receiving client will use to create secret
    key: int  # public key in the form g^a or g^a^b or g^a^b^c, etc...


@dataclass
class DHPublicKeyRequest(StreamData):
    """Send to client to request their public key for chat channel"""
    channel_id: str


DATA_CLASSES = {
    dc.__name__: dc for dc in (
        MessageData,
        DHPublicKey,
        DHPublicKeyRequest,
        EncryptedData
    )
}
