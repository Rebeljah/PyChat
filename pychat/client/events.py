from pydantic import BaseModel

from pychat.common.pubsub import PubSub
from pychat.common import models


class Event(BaseModel):
    pass


class MessageReceived(Event):
    message: models.ChatMessage


class SendMessage(Event):
    message: models.ChatMessage


class CreateRoom(Event):
    room_name: str


class JoinRoom(Event):
    invite_code: str


class RoomCreated(Event):
    room: models.ChatRoom


# pubsub used by GUI and client to communicate events
pubsub = PubSub()
