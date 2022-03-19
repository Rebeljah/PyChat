import json
from dataclasses import dataclass, asdict, fields
from typing import Type


@dataclass(frozen=True)
class StreamData:
    def to_json(self):
        data = {'type': self.__class__.__name__, **asdict(self)}
        return json.dumps(data, indent=None, separators=(',', ':'))

    @classmethod
    def from_json(cls, data: bytes):
        """convert json bytestring to appropriate StreamData object"""
        data: dict = json.loads(data)

        data_class: Type[StreamData] = stream_data_types[data['type']]
        field_names = set(field.name for field in fields(data_class))

        return data_class(
            **{k: v for k, v in data.items() if k in field_names}
        )


@dataclass(frozen=True)
class ClientData(StreamData):
    id: str


@dataclass(frozen=True)
class MessageData(StreamData):
    channel_id: str
    sender_id: str
    text: str


data_types = (MessageData, ClientData)
stream_data_types = {type_.__name__: type_ for type_ in data_types}
