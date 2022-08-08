from atexit import register
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


# messaging requests
class PostMessage(Request):
    message: models.ChatMessage


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
