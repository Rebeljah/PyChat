
from dataclasses import dataclass, asdict, field


@dataclass
class StreamData:
    __dataclass__: str = field(init=False)

    def __post_init__(self):
        self.__dataclass__ = self.__class__.__name__

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'StreamData':
        """Load the dict as StreamData. If any dict contained in d
        has a '__dataclass__' key, it is recursively converted into StreamData"""
        data_class = data_classes[d['__dataclass__']]
        del d['__dataclass__']

        for key, val in d.items():
            if isinstance(val, dict) and '__dataclass__' in val:
                d[key] = StreamData.from_dict(val)

        return data_class(**d)


@dataclass
class ClientData(StreamData):
    channel_id: str
    username: str


@dataclass
class MessageData(StreamData):
    client: ClientData
    text: str


data_classes = {
    dc.__name__: dc for dc in (
        MessageData,
        ClientData,
    )
}
