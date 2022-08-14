from pydantic import Field
from typing import Optional

from pychat.common import models
from pychat.common.utils import make_uid


class Request(models.StreamData):
    uid: str = Field(default_factory=make_uid)
    context: Optional[dict]

    def needs_response(self):
        cls = self.__class__
        return 'Response' in vars(cls)

class Response(models.StreamData):
    error: Optional[str]
    uid: Optional[str]


class Error(Response):
    reason: str


# diffie hellman
class KeyRequest(Request):
    fernet_uid: str

class GetDHKey(KeyRequest):
    pass

    class Response(Response):
        key: int = Field(repr=False)

class GetDHMixedKey(KeyRequest):
    key: int = Field(repr=False)

    class Response(Response):
        key: int = Field(repr=False)

class PostFinalKey(KeyRequest):
    key: int = Field(repr=False)

class RegenerateDHKeyPair(KeyRequest):
    class Response(Response):
        pass


# messaging requests
class PostMessage(Request):
    message: models.ChatMessage | models.Encrypted


# room creation / joining
class CreateRoom(Request):
    room_name: str

    class Response(Response):
        room: models.ChatRoom
        invite_code: str


class JoinRoom(Request):
    invite_code: str

    class Response(Response):
        room: models.ChatRoom


models.register_models(Request)
models.register_models(Response)
