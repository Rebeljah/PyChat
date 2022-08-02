from typing import Iterable

from .user import User
from pychat.common.identity import make_id


class ChatRoom:
    ROOMS: set["ChatRoom"] = set()

    def __init__(self, name: str):
        ChatRoom.ROOMS.add(self)

        self.id = make_id()
        self.name = name

        self.users: dict[str, User] = {}
    
    def add_user(self, user: User):
        self.users[user.id] = user
    
    def discard_user(self, user_id: str):
        self.users.pop(user_id, None)


class ChatRooms:
    def __init__(self):
        self._rooms: dict[str, ChatRoom] = {}
    
    def __iter__(self):
        return iter(self._rooms.values())
    
    def make_room(self, name: str):
        room = ChatRoom(name)
        self._rooms[room.id] = room
    
    def delete_room(self, room_id: str):
        del self._rooms[room_id]

    def purge_user(self, user_id: str):
        room: ChatRoom
        for room in self:
            room.discard_user(user_id)
