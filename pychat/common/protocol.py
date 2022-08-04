from pydantic import BaseModel, Field
import json
from cryptography.fernet import Fernet
from typing import Type, Optional

from pychat.common.identity import make_uid


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


class ChatMessage(Encryptable):
    text: str


class PublicKey(StreamData):
    value: int


### REQUEST AND RESPONSE PROTOCOL ###

class Request(StreamData):
    uid: str = Field(default_factory=make_uid)
    context: Optional[dict]

    def needs_response(self):
        cls = self.__class__
        return 'Response' in vars(cls)

class Response(StreamData):
    error: Optional[str]
    uid: str


class KeyRequest(Request):
    fernet_id: str

class GetDHKey(KeyRequest):
    pass

    class Response(Response):
        key: int

class GetDHMixedKey(KeyRequest):
    key: int

    class Response(Response):
        key: int

class PostFinalKey(KeyRequest):
    key: int


register_models(StreamData)
