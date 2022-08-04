
from typing import Iterable

from pychat.server.user import User
from pychat.common.identity import make_uid


class ChatRoom:
    def __init__(self, name: str):
        self.uid = make_uid()
        self.name = name
        self.users: dict[str, User] = {}
    
    def add_user(self, user: User):
        self.users[user.uid] = user
    
    def discard_user(self, user_uid: str):
        self.users.pop(user_uid, None)


class ChatRooms:
    def __init__(self):
        self._rooms: dict[str, ChatRoom] = {}
    
    def __iter__(self) -> Iterable[ChatRoom]:
        return iter(self._rooms.values())
    
    def make_room(self, name: str):
        room = ChatRoom(name)
        self._rooms[room.uid] = room
    
    def delete_room(self, room_uid: str):
        del self._rooms[room_uid]

    def purge_user(self, user_uid: str):
        room: ChatRoom
        for room in self:
            room.discard_user(user_uid)
