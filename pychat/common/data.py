from dataclasses import dataclass, asdict, field
from cryptography.fernet import Fernet
import json
from enum import IntEnum, auto

from .identity import make_id


@dataclass
class StreamData:
    _data_type: str = field(init=False)

    def __post_init__(self):
        self._data_type = self.__class__.__name__

    def as_json(self) -> str:
        return json.dumps(asdict(self), indent=None, separators=(',', ':'))

    @classmethod
    def from_dict(cls, d: dict):
        """Load the dict as StreamData. If any dict contained in d
        has a '_data_type' key, it is recursively converted into StreamData"""
        data_class = DATA_CLASSES[d['_data_type']]
        del d['_data_type']

        for key, val in d.items():
            if isinstance(val, dict) and '_data_type' in val:
                d[key] = StreamData.from_dict(val)

        return data_class(**d)


@dataclass
class EncryptedData(StreamData):
    """Stores another StreamData instance as an encrypted json string. Provides a
    decrypt method which decrypts the json string and returns a StreamData
    instance equivalent to the oringal.

    Params:
    data - The StreamData object to be encrypted
    fernet - Fernet object used to encrypt, must use equal Fernet to decrypt
    encryption_id - Used for finding an equal Fernet for decryption
    """
    data: StreamData|None
    fernet: Fernet|None
    encryption_id: str
    _encrypted_data: str|None = None

    def __post_init__(self):
        fernet = self.fernet
        data = self.data
        self.fernet = self.data = None

        data = data.as_json().encode()
        self._encrypted_data = fernet.encrypt(data).decode()

        return super().__post_init__()
        
    def decrypt(self, fernet: Fernet) -> StreamData:
        """Decrypt the data using the Fernet and return a new StreamData instance
        equal to the orignal StreamData instance. The Fernet used for decryption
        must be created with the same key as the Fernet used for encryption"""
        data = self._encrypted_data.encode()
        data = json.loads(fernet.decrypt(data))
        return StreamData.from_dict(data)


@dataclass
class ChatMessage(StreamData):
    channel_id: str
    username: str
    text: str


@dataclass
class DHPublicKey(StreamData):
    value: int  # public key in the form g^a or g^a^b or g^a^b^c, etc...


@dataclass
class Request(StreamData):
    type: "Request.Types"
    ctx: dict
    id: str = ''

    def __post_init__(self):
        self.id = self.id or make_id()
        return super().__post_init__()
    
    class Server(IntEnum):
        pass
    
    class Client(IntEnum):
        GetDHPublicKey = auto()
        GetDHMixedPublicKey = auto()
        PostFinalDHMixedPublicKey = auto()

    class Common(IntEnum):
        pass


@dataclass
class Response(StreamData):
    id: str
    data: StreamData


DATA_CLASSES = {
    dc.__name__: dc for dc in (
        ChatMessage,
        DHPublicKey,
        EncryptedData,
        Request,
        Response,
    )
}
