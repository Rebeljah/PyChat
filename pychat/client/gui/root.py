import tkinter as tk
from tkinter import ttk
import asyncio

from pychat.client.gui.room import NewRoomTab, JoinRoomTab, RoomTab
from pychat.client import events
from pychat.common import models


class GUIRoot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_running_loop()
        self.closed = asyncio.Event()

        self.title('PyChat')
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.room_tabs = ttk.Notebook(self)
        inner_tabs = ttk.Notebook(self.room_tabs)
        inner_tabs.add(NewRoomTab(inner_tabs), text='New room')
        inner_tabs.add(JoinRoomTab(inner_tabs), text='Join room')
        self.room_tabs.add(inner_tabs, text=' + ')

        self._arrange()

        events.pubsub.subscribe(events.RoomCreated, lambda e:
            self._add_room(e.room)
        )

        self._mainloop()
    
    def _arrange(self):
        self.room_tabs.pack(fill=tk.BOTH, expand=1)
    
    def _mainloop(self):
        self.update()
        self.loop.call_soon(self._mainloop)

    def _close(self):
        self.closed.set()

    def _add_room(self, room: models.ChatRoom):
        self.room_tabs.insert(0, RoomTab(self.room_tabs, room.uid), text=room.name)
