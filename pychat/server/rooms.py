
import asyncio

from pychat.common.utils import make_uid, make_invite_code
from pychat.common import models
from pychat.common import request as req
from pychat.server import users


class ChatRoom:
    def __init__(self, name: str):
        self.uid = make_uid()
        self.name = name
        self.invite_code = make_invite_code()

        self.users: set[users.User] = set()
    
    @property
    def has_users(self):
        return len(self.users) > 0
    
    def add_user(self, user):
        self.users.add(user)
    
    def remove_user(self, user):
        self.users.remove(user)
    
    async def send_message(self, message: models.ChatMessage):
        r = req.PostMessage(message=message)
        await asyncio.gather(*[u.stream.write(r) for u in self.users])

    def model(self) -> models.ChatRoom:
        return models.ChatRoom(uid=self.uid, name=self.name)


class ChatRooms:
    def __init__(self):
        self.invite_codes: dict[str, ChatRoom] = {}
        self.rooms: dict[str, ChatRoom] = {}

    def make_room(self, name: str) -> ChatRoom:
        room = ChatRoom(name)

        self.rooms[room.uid] = room
        self.invite_codes[room.invite_code] = room

        return room
        
    def delete_room(self, room_uid: str):
        room = self.rooms[room_uid]
        del self.invite_codes[room.invite_code]
        del self.rooms[room.uid]

    def add_user_to_room(self, user, room_uid):
        room = self.rooms[room_uid]
        room.add_user(user)

    def remove_user_from_room(self, user, room_uid):
        room = self.rooms[room_uid]
        room.remove_user(user)

        if not room.has_users:
            self.delete_room(room_uid)

    def purge_user(self, user):
        for room in tuple(self.rooms.values()):
            if user not in room.users: continue
            room.remove_user(user)

    async def send_message(self, message: models.ChatMessage):
        room = self.rooms[message.room_uid]
        await room.send_message(message)

    async def on_post_message(self, r: req.PostMessage) -> None:
        await self.send_message(r.message)
    
    def on_create_room(self, user: users.User, r: req.CreateRoom) -> req.CreateRoom.Response:
        # make a new room and add the requesting user to the room
        room: ChatRoom = self.make_room(r.room_name)

        self.add_user_to_room(user, room.uid)

        # return the room model and invite code
        return req.CreateRoom.Response(room=room.model(), invite_code=room.invite_code)
    
    def on_join_room(self, user: users.User, r: req.JoinRoom) -> req.JoinRoom.Response:
        room = self.invite_codes.get(r.invite_code)

        self.add_user_to_room(user, room.uid)

        return req.JoinRoom.Response(room=room.model())
