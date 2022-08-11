from pychat.client import diffiehellman as dh
from pychat.client import events
from pychat.common import models
from pychat.common import request as req
from pychat.common.stream import DataStream


class ChatRoom:
    def __init__(self, name: str, uid: str):
        self.name = name
        self.uid = uid
        
        self.dh_secret: int = dh.secret_key()
        self.dh_public: int = dh.public_key(self.dh_secret)
        self.dh_fernet = None
    
    def mix_dh_public(self, dh_public: int) -> int:
        return dh.mix_keys(self.dh_secret, dh_public)
    
    def create_shared_secret(self, dh_final_public: int):
        dh_secret: int = self.mix_dh_public(dh_final_public)
        self.dh_fernet = dh.create_fernet(dh_secret)
    
    def model(self) -> models.ChatRoom:
        return models.ChatRoom(name=self.name, uid=self.uid)


class ChatRooms:
    def __init__(self, stream: DataStream):
        self.rooms: dict[str, ChatRoom] = {}
        self.stream = stream
    
    def _register_request_handlers(self):
        self.stream.register_request_handler(req.GetDHKey, self.on_get_dh_key)
        self.stream.register_request_handler(req.GetDHMixedKey, self.on_get_dh_mixed_key)
        self.stream.register_request_handler(req.PostFinalKey, self.on_post_dh_final_key)
        self.stream.register_request_handler(req.PostMessage, self.on_message_received)
    
    def _register_event_handlers(self):
        events.pubsub.subscribe(events.CreateRoom, self.on_create_room)
        events.pubsub.subscribe(events.JoinRoom, self.on_join_room)
        events.pubsub.subscribe(events.SendMessage, self.on_send_message)
    
    def add_room(self, room: models.ChatRoom):
        room = ChatRoom(room.name, room.uid)
        self.rooms[room.uid] = room
        events.pubsub.publish(events.RoomCreated(room=room.model()))
    
    def delete_room(self, room_uid):
        del self.rooms[room_uid]
    
    def on_get_dh_key(self, r: req.GetDHKey) -> req.GetDHKey.Response:
        room_uid = r.fernet_uid
        room = self.rooms[room_uid]
        
        return req.GetDHKey.Response(key=room.dh_public)
    
    def on_get_dh_mixed_key(self, r: req.GetDHMixedKey) -> req.GetDHMixedKey.Response:
        room_uid = r.fernet_uid
        room = self.rooms[room_uid]

        mixed_dh_public = room.mix_dh_public(r.key)
        return req.GetDHMixedKey.Response(key=mixed_dh_public)
    
    def on_post_dh_final_key(self, r: req.PostFinalKey) -> None:
        room_uid = r.fernet_uid
        room = self.rooms[room_uid]
        room.create_shared_secret(r.key)
    
    async def on_create_room(self, event: events.CreateRoom) -> None:
        """Request for the server to make a new room and await
        the server to send back a response with the room model"""

        r = req.CreateRoom(room_name=event.room_name)
        resp: req.CreateRoom.Response = await self.stream.write(r)

        room: models.ChatRoom = resp.room
        invite_code: str = resp.invite_code

        self.add_room(room)

        # TODO Should this be handled by the server??
        # send a message to the new room containing the invite code
        usr = models.User(name='Pychat', uid='')
        txt = f'The invite code is: {invite_code}'
        msg = models.ChatMessage(user=usr, text=txt, room_uid=room.uid)
        await self.stream.write(req.PostMessage(message=msg))
    
    async def on_join_room(self, event: events.JoinRoom) -> None:
        """Request for the server to find a room with a matching invite code. If
        a match is found, a respone containing the room model is returned"""

        r = req.JoinRoom(invite_code=event.invite_code)
        resp: req.JoinRoom.Response = await self.stream.write(r)

        self.add_room(resp.room)

        # TODO Should this be handled by the server??
        # send a message to the room informing other users
        usr = models.User(name='Pychat', uid='')
        txt = f'User PLACEHOLDER has join the chat!'
        msg = models.ChatMessage(user=usr, text=txt, room_uid=resp.room.uid)
        await self.stream.write(req.PostMessage(message=msg))

    async def on_send_message(self, event: events.SendMessage) -> None:
        room = self.rooms[event.message.room_uid]
        msg: models.ChatMessage = event.message

        if room.dh_fernet is not None:
            msg: models.Encrypted = msg.encrypt(room.dh_fernet, room.uid)
        
        await self.stream.write(req.PostMessage(message=msg))
    
    def on_message_received(self, r: req.PostMessage) -> None:
        msg: models.ChatMessage | models.Encrypted = r.message
         # decrypt the message if needed
        if isinstance(msg, models.Encrypted):
            room_uid = msg.fernet_id
            room = self.rooms[room_uid]
            msg: models.ChatMessage = msg.decrypt(room.dh_fernet)

        events.pubsub.publish(events.MessageReceived(message=msg))
