import asyncio

from pychat.common.stream import DataStream, SERVER_IP, PORT
from pychat.client import events
from pychat.common import request as req
from pychat.common import models


USER = models.User(name='', uid='')


class PychatClient:
    def __init__(self):
        self.stream: DataStream | None = None

        events.pubsub.subscribe(events.SendMessage, self.on_send_message)
        events.pubsub.subscribe(events.CreateRoom, self.on_create_room)
        events.pubsub.subscribe(events.JoinRoom, self.on_join_room)

        asyncio.create_task(self.connect())

    async def connect(self):
        r, w = await asyncio.open_connection(host=SERVER_IP, port=PORT)
        self.stream = DataStream(r, w)

        self.stream.register_request_handler(req.PostMessage, self.on_message_received)

        # start handling messages
        try:
            await self.stream.listen()
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        pass
    
    async def on_send_message(self, event: events.SendMessage):
        await self.stream.write(req.PostMessage(message=event.message))
    
    async def on_create_room(self, event: events.CreateRoom):
        """Request for the server to make a new room and await
        the server to send back a response with the room model"""

        r = req.CreateRoom(room_name=event.room_name)
        resp: req.CreateRoom.Response = await self.stream.write(r)

        room: models.ChatRoom = resp.room
        invite_code: str = resp.invite_code

        events.pubsub.publish(events.RoomCreated(room=room))

        # TODO Should this be handled by the server??
        # send a message to the new room containing the invite code
        usr = models.User(name='Pychat', uid='')
        txt = f'The invite code is: {invite_code}'
        msg = models.ChatMessage(user=usr, text=txt, room_uid=room.uid)
        await self.stream.write(req.PostMessage(message=msg))
    
    async def on_join_room(self, event: events.JoinRoom):
        """Request for the server to find a room with a matching invite code. If
        a match is found, a respone containing the room model is returned"""

        r = req.JoinRoom(invite_code=event.invite_code)
        resp: req.JoinRoom.Response = await self.stream.write(r)

        events.pubsub.publish(events.RoomCreated(room=resp.room))

        # TODO Should this be handled by the server??
        # send a message to the room informing other users
        usr = models.User(name='Pychat', uid='')
        txt = f'User {USER.name} has join the chat!'
        msg = models.ChatMessage(user=usr, text=txt, room_uid=resp.room.uid)
        await self.stream.write(req.PostMessage(message=msg))
    
    def on_message_received(self, r: req.PostMessage) -> None:
        events.pubsub.publish(events.MessageReceived(message=r.message))
