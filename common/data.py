
from dataclasses import dataclass, asdict, field


@dataclass
class StreamData:
    __dataclass__: str = field(init=False, repr=False)

    def __post_init__(self):
        self.__dataclass__ = self.__class__.__name__

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'StreamData':
        """Load the dict as StreamData. If any dict contained in d
        has a '__dataclass__' key, it is recursively converted into StreamData"""
        data_class = DATA_CLASSES[d['__dataclass__']]
        del d['__dataclass__']

        for key, val in d.items():
            if isinstance(val, dict) and '__dataclass__' in val:
                d[key] = StreamData.from_dict(val)

        return data_class(**d)


@dataclass
class MessageData(StreamData):
    channel_id: str
    username: str
    text: str


@dataclass
class DHPublicKey(StreamData):
    key: int  # represents a public key in the form g^a or g^a^b or g^a^b^c, etc
    is_final: bool  # key is ready to make shared secret once all parts are added
    channel_id: str  # channel which the encryption will be used in


DATA_CLASSES = {
    dc.__name__: dc for dc in (
        MessageData,
        DHPublicKey,
    )
}
