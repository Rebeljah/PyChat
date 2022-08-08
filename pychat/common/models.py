from pydantic import BaseModel
import json
from cryptography.fernet import Fernet
from typing import Type


_MODELS: dict[str, Type[BaseModel]] = {}


def register_models(superclass):
    """Add all models to the _MODELS dict so that that the correct class
    can be selected when raw data is received"""
    for subclass in superclass.__subclasses__():
        _MODELS[subclass.__qualname__] = subclass
        register_models(subclass)


def name_to_type(name: str) -> Type[BaseModel]:
    """Use the __qualname__ attribute from raw dat to fetch the appropriate
    model class"""
    return _MODELS[name]


def json_to_model(json_: str | bytes):
    obj: dict = json.loads(json_)
    type_ = name_to_type(obj['__name__'])
    return type_.parse_obj(obj)


class StreamData(BaseModel):
    def json(self, *args, **kwargs):
        d = self.dict(*args, **kwargs)
        d['__name__'] = self.__class__.__qualname__
        return json.dumps(d, indent=None, separators=(', ', ': '))


class Encrypted(StreamData):
    encrypted_type: str
    fernet_id: str
    ciphertext: str

    def decrypt(self, f: Fernet) -> StreamData:
        ciphertext: bytes = self.ciphertext.encode()
        model_type = name_to_type(self.encrypted_type)

        return model_type.parse_raw(f.decrypt(ciphertext))


class Encryptable(StreamData):

    def encrypt(self, fernet: Fernet, fernet_id: str) -> Encrypted:
        json_: bytes = self.json().encode()
        ciphertext: bytes = fernet.encrypt(json_).decode()

        return Encrypted(
            encrypted_type=self.__class__.__qualname__,
            fernet_id=fernet_id,
            ciphertext=ciphertext
        )


class User(StreamData):
    name: str
    uid: str


class ChatMessage(Encryptable):
    user: User
    text: str
    room_uid: str


class ChatRoom(StreamData):
    uid: str
    name: str


register_models(StreamData)
