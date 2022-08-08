import tkinter as tk

from pychat.common import models
from pychat.client import events
from pychat.client.client import USER

USER: models.User


class RoomTab(tk.Frame):
    def __init__(self, master, room_uid, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.uid = room_uid

        events.pubsub.subscribe(events.MessageReceived, lambda e:
            self.add_message(e.message)
        )

        # chat frame widgets
        self.chat_frame = tk.Frame(self)
        self.chat_text = tk.Text(self.chat_frame)
        self.entry = tk.Entry(self.chat_frame)
        self.send_btn = tk.Button(self.chat_frame, text='Send', command=self.send_message)

        self._arrange()
    
    def _arrange(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # chat frame
        self.chat_frame.rowconfigure(0, weight=90)
        self.chat_frame.rowconfigure(1, weight=10)
        self.chat_frame.columnconfigure(0, weight=90)
        self.chat_frame.columnconfigure(1, weight=10)
        self.chat_text.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.entry.grid(row=1, column=0, sticky='ew')
        self.send_btn.grid(row=1, column=1, sticky='ew')

        self.chat_frame.grid(row=0, column=0, sticky='nsew')
    
    def add_message(self, message: models.ChatMessage):
        if message.room_uid != self.uid:
            return

        txt = f"{message.user.name}: {message.text}\n"
        self.chat_text.insert('end', txt)
    
    def send_message(self):
        txt = self.entry.get()
        self.entry.delete(0, tk.END)

        events.pubsub.publish(
            events.SendMessage(
                message=models.ChatMessage(user=USER, text=txt, room_uid=self.uid)
            )
        )


class NewRoomTab(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.name_label = tk.Label(self, text='Room name')
        self.name_entry = tk.Entry(self)

        self.submit_btn = tk.Button(self, text='Create', command=self.create_room)

        self.arrange()
    
    def arrange(self):
        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1)
        self.submit_btn.grid(row=1, column=1)
    
    def create_room(self):
        if not len(name := self.name_entry.get()):
            return

        self.name_entry.delete(0, tk.END)

        events.pubsub.publish(events.CreateRoom(room_name=name))


class JoinRoomTab(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.invite_label = tk.Label(self, text='Invite code')
        self.invite_entry = tk.Entry(self)

        self.join_btn = tk.Button(self, text='Join', command=self.join_room)

        self.arrange()
    
    def arrange(self):
        self.invite_label.grid(row=0, column=0)
        self.invite_entry.grid(row=0, column=1)
        self.join_btn.grid(row=1, column=1)
    
    def join_room(self):
        if not len(code := self.invite_entry.get()):
            return

        self.invite_entry.delete(0, tk.END)

        events.pubsub.publish(events.JoinRoom(invite_code=code))
